"""Outils en lecture seule sur le catalogue fictif (F06 à F12, NF12).

ADK transforme chaque fonction en outil : le nom, les paramètres typés et la docstring deviennent
la description envoyée à Gemini. Les mêmes fonctions sont exposées par le serveur MCP (lot 5).
Les prix renvoyés viennent des données ou des règles, jamais du LLM.
"""

from datetime import datetime

from shared import data, regles
from shared.vocabulaire import CATEGORIES


def _verifier_categorie(categorie: str) -> dict | None:
    if categorie not in CATEGORIES:
        return {"erreur": f"catégorie inconnue : {categorie}", "categories_valides": CATEGORIES}
    return None


# ---------------------------------------------------------------------------------------------
# Réparation
# ---------------------------------------------------------------------------------------------
def chercher_pieces(categorie: str, defaut: str) -> dict:
    """Cherche les pièces détachées et tutoriels qui traitent un défaut pour une catégorie de produit.

    Args:
        categorie: code de catégorie (ex. "tente", "velo_ville").
        defaut: code du défaut (ex. "arceau_casse").

    Returns:
        Les pièces trouvées (part_id, nom, prix_eur, difficulte, tutoriel). Liste vide si aucune.
    """
    if err := _verifier_categorie(categorie):
        return err
    trouvees = [p for p in data.pieces() if categorie in p.categories and p.defaut == defaut]
    return {"pieces": [p.model_dump(exclude={"categories", "defaut"}) for p in trouvees]}


def chercher_prestation_atelier(categorie: str, defaut: str) -> dict:
    """Cherche la prestation d'atelier qui répare un défaut, avec son prix et sa durée.

    Args:
        categorie: code de catégorie.
        defaut: code du défaut.

    Returns:
        La prestation (service_id, prix_eur, duree_jours) ou {"prestation": null} si aucune.
    """
    if err := _verifier_categorie(categorie):
        return err
    p = next((s for s in data.prestations() if categorie in s.categories and s.defaut == defaut), None)
    return {"prestation": p.model_dump(exclude={"categories"}) if p else None}


def trouver_atelier(code_postal: str) -> dict:
    """Trouve l'atelier le plus proche d'un code postal français et ses trois prochains créneaux.

    Args:
        code_postal: code postal à 5 chiffres.

    Returns:
        L'atelier (workshop_id, nom, ville) et ses créneaux au format ISO 8601.
    """
    if not (len(code_postal) == 5 and code_postal.isdigit()):
        return {"erreur": "code postal invalide, 5 chiffres attendus"}
    ateliers = data.ateliers()
    meme_dept = [a for a in ateliers if a.code_postal[:2] == code_postal[:2]]
    # À défaut du même département, le plus proche numériquement (approximation de démo).
    atelier = (meme_dept or sorted(ateliers, key=lambda a: abs(int(a.code_postal[:2]) - int(code_postal[:2]))))[0]
    return {
        "workshop_id": atelier.workshop_id,
        "nom": atelier.nom,
        "ville": atelier.ville,
        "meme_departement": bool(meme_dept),
        "creneaux": atelier.prochains_creneaux(datetime.now(), 3),
    }


# ---------------------------------------------------------------------------------------------
# Valorisation
# ---------------------------------------------------------------------------------------------
def calculer_offre_rachat(categorie: str, etat: str, age_annees: float, gamme: str = "inconnue") -> dict:
    """Calcule l'offre de rachat indicative d'un produit selon le barème (règles R01, R02, R03).

    Args:
        categorie: code de catégorie.
        etat: "bon", "moyen", "use" ou "hors_usage".
        age_annees: âge du produit en années.
        gamme: "entree", "milieu", "haut" ou "inconnue".

    Returns:
        montant_eur, autorisee (faux si le produit ne peut pas être racheté) et le détail du calcul.
    """
    if err := _verifier_categorie(categorie):
        return err
    if etat not in data.bareme().coef_etat:
        return {"erreur": f"état inconnu : {etat}"}
    offre = regles.calculer_offre_rachat(categorie, etat, age_annees, gamme)
    return {"montant_eur": offre.montant_eur, "autorisee": offre.autorisee, "detail": offre.detail}


def chercher_location(categorie: str, gamme: str = "inconnue") -> dict:
    """Cherche une offre de location pour une catégorie de produit.

    Args:
        categorie: code de catégorie.
        gamme: gamme souhaitée, ou "inconnue".

    Returns:
        Les offres (product_id, nom, prix_jour_eur, prix_semaine_eur, caution_eur). Liste vide si aucune.
    """
    if err := _verifier_categorie(categorie):
        return err
    offres = []
    for o in data.location():
        p = data.produit(o.product_id)
        if p.categorie == categorie and (gamme == "inconnue" or p.gamme == gamme):
            offres.append({"product_id": o.product_id, "nom": p.nom, **o.model_dump(exclude={"product_id"})})
    return {"offres": sorted(offres, key=lambda o: o["prix_jour_eur"])[:3]}


def chercher_occasion(categorie: str, gamme: str = "inconnue") -> dict:
    """Cherche des articles d'occasion contrôlés équivalents dans le stock.

    Args:
        categorie: code de catégorie.
        gamme: gamme souhaitée, ou "inconnue".

    Returns:
        Les articles (item_id, nom, etat_controle, prix_eur), du moins cher au plus cher. Liste vide si aucun.
    """
    if err := _verifier_categorie(categorie):
        return err
    if regles.est_securite(categorie):
        return {"articles": [], "note": "R01 : aucun produit de sécurité d'occasion."}
    articles = []
    for o in data.occasion():
        p = data.produit(o.product_id)
        if p.categorie == categorie and (gamme == "inconnue" or p.gamme == gamme):
            articles.append({"item_id": o.item_id, "nom": p.nom, "etat_controle": o.etat_controle, "prix_eur": o.prix_eur})
    return {"articles": sorted(articles, key=lambda a: a["prix_eur"])[:3]}


OUTILS_REPARATION = [chercher_pieces, chercher_prestation_atelier, trouver_atelier]
OUTILS_VALORISATION = [calculer_offre_rachat, chercher_location, chercher_occasion]
