"""Règles métier R01 à R06 : déterministes, donc testables sans LLM."""

import pytest

from shared import regles
from shared.config import MENTION_RACHAT
from shared.schemas import FicheDiagnostic


def fiche(categorie="tente", famille="camping", etat="moyen", defauts=None, **kw) -> FicheDiagnostic:
    defauts = [{"type": "arceau_casse", "gravite": "moyenne"}] if defauts is None else defauts
    return FicheDiagnostic(famille=famille, categorie=categorie, etat=etat, defauts=defauts,
                           age_annees=kw.pop("age_annees", 3), confiance=0.9, resume="test", **kw)


# --- R01 ------------------------------------------------------------------------------------
def test_r01_casque_endommage_ni_rachat_ni_occasion():
    f = fiche("casque_velo", "velo", etat="hors_usage", defauts=[{"type": "choc_coque", "gravite": "forte"}])
    reco = regles.decider(f, {"reparable": False}, {"occasion_item_id": "OC-001"})
    assert reco.option_recommandee == "recycler"
    assert {o.option for o in reco.options} == {"recycler"}
    assert "R01" in reco.regles_appliquees


def test_r01_offre_de_rachat_refusee_pour_securite():
    assert not regles.calculer_offre_rachat("siege_velo_enfant", "bon", 1).autorisee


# --- R02 / R03 --------------------------------------------------------------------------------
def test_r02_formule_et_plafond():
    # Tente gamme milieu : médiane 149 € ; état moyen 0,30 ; 3 ans → 0,70 → 31,29 → 31 €
    offre = regles.calculer_offre_rachat("tente", "moyen", 3, "milieu")
    assert offre.montant_eur == 31
    # Vélo de route haut de gamme quasi neuf : 1899 × 0,45 × 1 = 854 € → plafonné à 600 €
    assert regles.calculer_offre_rachat("velo_route", "bon", 0.5, "haut").montant_eur == 600


def test_r02_hors_usage_pas_de_rachat():
    assert not regles.calculer_offre_rachat("tente", "hors_usage", 2).autorisee


def test_r03_mention_indicative_avec_toute_offre():
    reco = regles.decider(fiche(defauts=[], etat="bon", veut_s_en_separer=True), None, None)
    assert reco.option_recommandee == "revendre"
    assert MENTION_RACHAT in reco.mentions_obligatoires


# --- R04 --------------------------------------------------------------------------------------
def test_r04_reparation_rentable_recommandee():
    rep = {"reparable": True, "pieces": [{"part_id": "PC-001"}], "service_id": "SV-001"}
    reco = regles.decider(fiche(), rep, None)
    assert reco.option_recommandee == "reparer"
    assert "R04" in reco.regles_appliquees


def test_r04_seuil():
    seuil = 0.5 * regles.prix_occasion_equivalent("tente")
    assert regles.reparation_rentable(seuil - 0.01, "tente")
    assert not regles.reparation_rentable(seuil, "tente")


def test_prix_des_options_relus_dans_les_donnees_pas_chez_le_llm():
    rep = {"reparable": True, "pieces": [{"part_id": "PC-001", "prix_eur": 0.01}], "service_id": "SV-001", "cout_atelier_eur": 1}
    reco = regles.decider(fiche(), rep, None)
    prix = {o.titre: o.cout_client_eur for o in reco.options}
    assert prix["Réparer vous-même"] == 9.99
    assert prix["Faire réparer en atelier"] == 25.0


def test_identifiant_invente_ignore():
    reco = regles.decider(fiche(), {"reparable": True, "pieces": [{"part_id": "PC-999"}]}, {"occasion_item_id": "OC-999"})
    assert "reparer" not in {o.option for o in reco.options}
    assert "occasion" not in {o.option for o in reco.options}


# --- R05 --------------------------------------------------------------------------------------
@pytest.mark.parametrize("frequence,attendu", [("ponctuelle", True), ("reguliere", False), ("inconnue", False)])
def test_r05_location_si_usage_ponctuel(frequence, attendu):
    reco = regles.decider(fiche(frequence_usage=frequence, defauts=[], etat="bon"), None,
                          {"location_product_id": "P-TENTE-02"})
    assert ("louer" in {o.option for o in reco.options}) is attendu


# --- R06 --------------------------------------------------------------------------------------
def test_r06_motifs_escalade():
    assert regles.motifs_escalade(fiche(demande_humain=True), 0, 0) == ["demande explicite du client"]
    assert regles.motifs_escalade(fiche(sous_garantie_ou_litige=True), 0, 0)
    incertaine = fiche().model_copy(update={"confiance": 0.3})
    assert regles.motifs_escalade(incertaine, 2, 0) == ["diagnostic incertain après deux questions"]
    assert regles.motifs_escalade(incertaine, 1, 0) == []
    assert regles.motifs_escalade(None, 0, 3) == ["trois échanges sans progrès"]


# --- Divers -----------------------------------------------------------------------------------
def test_defaut_critique_jamais_repare():
    f = fiche("velo_ville", "velo", etat="hors_usage", defauts=[{"type": "cadre_fissure", "gravite": "forte"}])
    reco = regles.decider(f, {"reparable": True, "service_id": "SV-014"}, None)
    assert reco.option_recommandee == "recycler"


def test_au_plus_trois_options_recommandee_en_premier():
    rep = {"reparable": True, "pieces": [{"part_id": "PC-001"}], "service_id": "SV-001"}
    val = {"location_product_id": "P-TENTE-02", "occasion_item_id": "OC-001"}
    reco = regles.decider(fiche(frequence_usage="ponctuelle"), rep, val)
    assert len(reco.options) <= 3
    assert reco.options[0].option == reco.option_recommandee
