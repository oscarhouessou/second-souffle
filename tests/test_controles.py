"""Juge (contrôles déterministes) et garde-fou de confirmation R07."""

import pytest

from orchestrator.actions import est_confirmation
from shared import regles
from shared.controles import controler_message
from shared.schemas import FicheDiagnostic


@pytest.fixture
def reco():
    fiche = FicheDiagnostic(famille="camping", categorie="tente", etat="moyen", age_annees=3,
                            defauts=[{"type": "arceau_casse", "gravite": "moyenne"}], confiance=0.9, resume="t")
    return regles.decider(fiche, {"reparable": True, "pieces": [{"part_id": "PC-001"}], "service_id": "SV-001"}, None)


def bon_message(reco):
    rachat = next(o for o in reco.options if o.option == "revendre")
    return (f"Je vous recommande de réparer vous-même pour 9,99 €. En atelier : 25 €, 7 jours. "
            f"Revente : {rachat.gain_client_eur:g} €, offre indicative.")


def test_message_fidele_accepte(reco):
    assert controler_message(bon_message(reco), reco).accepte


def test_prix_invente_refuse(reco):
    v = controler_message(bon_message(reco).replace("25 €", "19 €"), reco)
    assert not v.accepte and "R08" in v.motifs[0]


def test_arrondi_a_l_euro_tolere(reco):
    assert controler_message(bon_message(reco).replace("9,99 €", "10 €"), reco).accepte


def test_r03_rachat_sans_mention_indicative_refuse(reco):
    v = controler_message(bon_message(reco).replace(", offre indicative", ""), reco)
    assert any("R03" in m for m in v.motifs)


def test_marque_refusee(reco):
    v = controler_message(bon_message(reco) + " Comme une tente Quechua.", reco)
    assert any("marques" in m for m in v.motifs)


def test_option_recommandee_absente_refusee(reco):
    v = controler_message("Revente : offre indicative.", reco)
    assert any("recommandée" in m for m in v.motifs)


@pytest.mark.parametrize("texte,attendu", [
    ("oui", True), ("Oui je confirme", True), ("ok vas-y", True), ("d'accord", True),
    ("c'est quoi l'option 2 ?", False), ("non pas encore", False), ("je réfléchis", False),
])
def test_r07_confirmation_explicite(texte, attendu):
    assert est_confirmation(texte) is attendu
