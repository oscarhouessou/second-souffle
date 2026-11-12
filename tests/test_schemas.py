import pytest
from pydantic import ValidationError

from shared.schemas import FicheDiagnostic


def fiche(**kwargs):
    base = {
        "famille": "camping",
        "categorie": "tente",
        "age_annees": 3,
        "etat": "moyen",
        "defauts": [{"type": "arceau_casse", "gravite": "moyenne"}],
        "confiance": 0.82,
        "resume": "Tente de 3 ans avec un arceau cassé.",
    }
    return FicheDiagnostic(**(base | kwargs))


def test_exemple_du_cahier_des_charges_est_valide():
    f = fiche(defauts=[{"type": "arceau_casse", "gravite": "moyenne"},
                       {"type": "dechirure_toile", "gravite": "faible", "taille_cm": 5}])
    assert f.defaut_principal == "arceau_casse"


@pytest.mark.parametrize(
    "champ,valeur",
    [
        ("etat", "cassé"),  # hors vocabulaire
        ("categorie", "ski"),  # hors périmètre
        ("confiance", 1.5),  # hors [0, 1]
        ("questions_restantes", ["a ?", "b ?", "c ?"]),  # F05 : au plus deux
        ("defauts", [{"type": "moteur_casse", "gravite": "forte"}]),
    ],
)
def test_valeurs_invalides_refusees(champ, valeur):
    with pytest.raises(ValidationError):
        fiche(**{champ: valeur})


def test_schema_json_exporte_pour_gemini():
    schema = FicheDiagnostic.model_json_schema()
    assert "confiance" in schema["required"]
