"""Règles métier R01 à R08 (section 5 du cahier des charges).

Principe : le modèle comprend et explique, les règles décident. Tout ce qui engage l'entreprise
(prix, sécurité, escalade) est calculé ici, en Python déterministe et testé.
"""

import statistics
from dataclasses import dataclass

from shared import data
from shared.config import (
    CATEGORIES_SECURITE,
    MAX_ECHANGES_SANS_PROGRES,
    MENTION_RACHAT,
    RATIO_REPARATION_OCCASION,
    SEUIL_CONFIANCE,
)
from shared.schemas import FicheDiagnostic, OptionChiffree, Recommandation
from shared.vocabulaire import DEFAUTS_CRITIQUES, LIBELLES_CATEGORIES


# ------------------------------------------------------------------------------------------
# R01 : sécurité
# ------------------------------------------------------------------------------------------
def est_securite(categorie: str | None) -> bool:
    return categorie in CATEGORIES_SECURITE


def est_endommage(fiche: FicheDiagnostic) -> bool:
    return bool(fiche.defauts) or fiche.etat in ("use", "hors_usage")


def revente_interdite(fiche: FicheDiagnostic) -> bool:
    """R01 : un produit de sécurité endommagé n'est ni revendu ni proposé d'occasion."""
    return est_securite(fiche.categorie) and est_endommage(fiche)


def est_dangereux(fiche: FicheDiagnostic) -> bool:
    """Défaut critique (cadre fissuré, casque choqué…) : on ne répare pas, on remplace."""
    return any(d.type in DEFAUTS_CRITIQUES for d in fiche.defauts) or fiche.etat == "hors_usage"


# ------------------------------------------------------------------------------------------
# R02 + R03 : offre de rachat
# ------------------------------------------------------------------------------------------
def prix_reference(categorie: str, gamme: str = "inconnue") -> float:
    """Prix neuf de référence : médiane du catalogue pour la catégorie (et la gamme si connue)."""
    produits = data.produits_de(categorie)
    de_la_gamme = [p for p in produits if p.gamme == gamme]
    return float(statistics.median(p.prix_neuf_eur for p in (de_la_gamme or produits)))


def coef_age(age_annees: float | None) -> float:
    age = 3.0 if age_annees is None else age_annees  # âge inconnu : hypothèse prudente
    for palier in data.bareme().coef_age:
        if palier.age_max_annees is None or age <= palier.age_max_annees:
            return palier.coef
    return data.bareme().coef_age[-1].coef


@dataclass
class OffreRachat:
    montant_eur: float
    autorisee: bool
    detail: str


def calculer_offre_rachat(categorie: str, etat: str, age_annees: float | None, gamme: str = "inconnue") -> OffreRachat:
    """R02 : prix neuf de référence × coef. état × coef. âge, plafonné par catégorie, arrondi à l'euro."""
    if categorie in CATEGORIES_SECURITE:
        return OffreRachat(0.0, False, "R01 : produit de sécurité, pas de rachat.")
    bareme = data.bareme()
    ref = prix_reference(categorie, gamme)
    c_etat = bareme.coef_etat[etat]
    c_age = coef_age(age_annees)
    plafond = bareme.plafond_par_categorie[categorie]
    brut = ref * c_etat * c_age
    montant = float(round(min(brut, plafond)))
    if montant <= 0:
        return OffreRachat(0.0, False, "État hors d'usage : pas de rachat, recyclage proposé.")
    detail = f"{ref:.0f} € × {c_etat} (état {etat}) × {c_age} (âge) = {brut:.2f} €, plafond {plafond:.0f} €"
    return OffreRachat(montant, True, detail)


# ------------------------------------------------------------------------------------------
# R04 : réparer ou non
# ------------------------------------------------------------------------------------------
def prix_occasion_equivalent(categorie: str, gamme: str = "inconnue") -> float:
    """Prix d'un équivalent d'occasion : stock réel s'il existe, sinon 50 % du prix neuf de référence."""
    prix = [
        o.prix_eur
        for o in data.occasion()
        if (p := data.produit(o.product_id)) and p.categorie == categorie and (gamme == "inconnue" or p.gamme == gamme)
    ]
    return float(statistics.median(prix)) if prix else round(prix_reference(categorie, gamme) * 0.5, 2)


def reparation_rentable(cout_reparation: float, categorie: str, gamme: str = "inconnue") -> bool:
    """R04 : réparer si le coût est inférieur à 50 % du prix d'un équivalent d'occasion."""
    return cout_reparation < RATIO_REPARATION_OCCASION * prix_occasion_equivalent(categorie, gamme)


# ------------------------------------------------------------------------------------------
# R05 : location
# ------------------------------------------------------------------------------------------
def location_pertinente(fiche: FicheDiagnostic) -> bool:
    """R05 : proposer la location si l'usage est ponctuel (moins de 3 utilisations par an)."""
    return fiche.frequence_usage == "ponctuelle"


# ------------------------------------------------------------------------------------------
# R06 : escalade
# ------------------------------------------------------------------------------------------
def motifs_escalade(fiche: FicheDiagnostic | None, questions_posees: int, echanges_sans_progres: int) -> list[str]:
    motifs = []
    if fiche and fiche.demande_humain:
        motifs.append("demande explicite du client")
    if fiche and fiche.sous_garantie_ou_litige:
        motifs.append("produit sous garantie ou litige")
    if fiche and fiche.confiance < SEUIL_CONFIANCE and questions_posees >= 2:
        motifs.append("diagnostic incertain après deux questions")
    if echanges_sans_progres >= MAX_ECHANGES_SANS_PROGRES:
        motifs.append("trois échanges sans progrès")
    return motifs


# ------------------------------------------------------------------------------------------
# CO2 évité
# ------------------------------------------------------------------------------------------
def co2_evite(option: str, categorie: str, gamme: str = "inconnue") -> float:
    produits = data.produits_de(categorie)
    de_la_gamme = [p for p in produits if p.gamme == gamme] or produits
    empreinte = statistics.median(p.co2_kg for p in de_la_gamme)
    ratio = data.bareme().co2_evite_ratio.get(option, 0.0)
    return round(float(empreinte) * float(ratio), 1)


# ------------------------------------------------------------------------------------------
# Décision : options chiffrées et recommandation (F13, R01 à R05, R03)
# ------------------------------------------------------------------------------------------
def _par_id(liste, cle, valeur):
    return next((x for x in liste if getattr(x, cle) == valeur), None)


def decider(fiche: FicheDiagnostic, reparation: dict | None, valorisation: dict | None) -> Recommandation:
    """Construit les options à partir des identifiants choisis par les agents, en relisant les prix
    dans les données (jamais ceux écrits par un LLM), puis applique les règles pour en recommander une."""
    assert fiche.categorie and fiche.etat, "fiche incomplète"
    cat, gamme = fiche.categorie, fiche.gamme
    libelle = LIBELLES_CATEGORIES[cat]
    reparation = reparation or {}
    valorisation = valorisation or {}
    options: list[OptionChiffree] = []
    regles: list[str] = []
    mentions: list[str] = []

    # --- Réparer -----------------------------------------------------------------------------
    cout_rep = None
    if not est_dangereux(fiche) and not est_securite(cat) and reparation.get("reparable"):
        pieces = [p for pid in [x.get("part_id") for x in reparation.get("pieces", [])] if (p := _par_id(data.pieces(), "part_id", pid))]
        presta = _par_id(data.prestations(), "service_id", reparation.get("service_id"))
        soi_meme = [p for p in pieces if p.difficulte != "atelier"]
        if soi_meme:
            cout = round(sum(p.prix_eur for p in soi_meme), 2)
            cout_rep = cout
            options.append(OptionChiffree(
                option="reparer", titre="Réparer vous-même", cout_client_eur=cout, delai_jours=0,
                co2_evite_kg=co2_evite("reparer", cat, gamme),
                detail=" + ".join(f"{p.nom} ({p.prix_eur:.2f} €)" for p in soi_meme),
            ))
        if presta:
            cout_rep = presta.prix_eur if cout_rep is None else min(cout_rep, presta.prix_eur)
            options.append(OptionChiffree(
                option="reparer", titre="Faire réparer en atelier", cout_client_eur=presta.prix_eur,
                delai_jours=presta.duree_jours, co2_evite_kg=co2_evite("reparer", cat, gamme),
                detail=f"Prestation d'atelier ({presta.prix_eur:.0f} €, {presta.duree_jours} jour"
                f"{'s' if presta.duree_jours > 1 else ''})",
            ))

    # --- Revendre (R01, R02, R03) ---------------------------------------------------------------
    if revente_interdite(fiche) or est_securite(cat):
        regles.append("R01")
    else:
        offre = calculer_offre_rachat(cat, fiche.etat, fiche.age_annees, gamme)
        if offre.autorisee:
            regles += ["R02", "R03"]
            mentions.append(MENTION_RACHAT)
            options.append(OptionChiffree(
                option="revendre", titre="Revendre (rachat)", gain_client_eur=offre.montant_eur, delai_jours=0,
                co2_evite_kg=co2_evite("revendre", cat, gamme), detail=f"Offre indicative : {offre.montant_eur:.0f} €",
            ))

    # --- Louer (R05) ------------------------------------------------------------------------------
    loc = _par_id(data.location(), "product_id", valorisation.get("location_product_id"))
    if location_pertinente(fiche) and loc:
        regles.append("R05")
        options.append(OptionChiffree(
            option="louer", titre="Louer quand vous en avez besoin", cout_client_eur=loc.prix_semaine_eur, delai_jours=0,
            co2_evite_kg=co2_evite("louer", cat, gamme),
            detail=f"{data.produit(loc.product_id).nom} : {loc.prix_jour_eur:.0f} € par jour, {loc.prix_semaine_eur:.0f} € la semaine",
        ))

    # --- Occasion (jamais pour un produit de sécurité) --------------------------------------------
    occ = _par_id(data.occasion(), "item_id", valorisation.get("occasion_item_id"))
    if occ and not est_securite(cat):
        p = data.produit(occ.product_id)
        options.append(OptionChiffree(
            option="occasion", titre="Racheter d'occasion", cout_client_eur=occ.prix_eur, delai_jours=0,
            co2_evite_kg=co2_evite("occasion", cat, gamme),
            detail=f"{p.nom}, état {occ.etat_controle.replace('_', ' ')} : {occ.prix_eur:.2f} €",
        ))

    # --- Choix de l'option recommandée -----------------------------------------------------------
    types_dispo = {o.option for o in options}
    if est_securite(cat) and est_endommage(fiche):
        recommandee, raison = "recycler", f"Un {libelle} endommagé ne protège plus : il faut le remplacer et le recycler."
        options.append(OptionChiffree(option="recycler", titre="Recycler et remplacer", detail="Dépôt en point de collecte."))
    elif est_dangereux(fiche):
        recommandee, raison = "recycler", "Le défaut rend le produit dangereux : réparation et revente sont exclues."
        options.append(OptionChiffree(option="recycler", titre="Recycler", detail="Dépôt en point de collecte."))
    elif fiche.veut_s_en_separer and "revendre" in types_dispo:
        recommandee = "revendre"
        raison = "Vous ne comptez plus l'utiliser : la revente lui donne une seconde vie et vous rapporte de l'argent."
    elif "reparer" in types_dispo and cout_rep is not None and reparation_rentable(cout_rep, cat, gamme):
        regles.append("R04")
        seuil = RATIO_REPARATION_OCCASION * prix_occasion_equivalent(cat, gamme)
        recommandee = "reparer"
        raison = f"La réparation coûte {cout_rep:.2f} €, moins de la moitié d'un équivalent d'occasion (seuil {seuil:.0f} €)."
    elif "louer" in types_dispo and "revendre" in types_dispo:
        recommandee, raison = "revendre", "Vous l'utilisez peu : le revendre puis louer au besoin vous coûte moins cher."
    elif "revendre" in types_dispo:
        recommandee = "revendre"
        raison = "La réparation n'est pas rentable ou pas possible : la revente vous rapporte le plus." if fiche.defauts else (
            "Le produit est en bon état et vous ne l'utilisez plus : le revendre lui donne une seconde vie.")
    elif "occasion" in types_dispo:
        recommandee, raison = "occasion", "Un équivalent d'occasion contrôlé est la solution la moins chère."
    else:
        recommandee, raison = "recycler", "Aucune option de réparation ou de revente n'est possible pour ce produit."
        options.append(OptionChiffree(option="recycler", titre="Recycler", detail="Dépôt en point de collecte."))

    # Option recommandée en premier, deux ou trois options au plus (F13)
    options.sort(key=lambda o: o.option != recommandee)
    return Recommandation(
        options=options[:3], option_recommandee=recommandee, raison=raison,
        regles_appliquees=sorted(set(regles)), mentions_obligatoires=mentions,
    )
