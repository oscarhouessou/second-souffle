"""Cohérence des données fictives entre elles et avec le vocabulaire."""

from datetime import datetime

from shared import data
from shared.config import CATEGORIES_SECURITE
from shared.vocabulaire import CATEGORIES, DEFAUTS_PAR_CATEGORIE


def test_chaque_categorie_a_des_produits():
    for cat in CATEGORIES:
        assert data.produits_de(cat), cat


def test_identifiants_uniques():
    for liste, cle in [
        (data.catalogue(), "product_id"),
        (data.pieces(), "part_id"),
        (data.prestations(), "service_id"),
        (data.ateliers(), "workshop_id"),
        (data.occasion(), "item_id"),
    ]:
        ids = [getattr(x, cle) for x in liste]
        assert len(ids) == len(set(ids)), cle


def test_pieces_et_prestations_utilisent_le_vocabulaire():
    for x in [*data.pieces(), *data.prestations()]:
        for cat in x.categories:
            assert x.defaut in DEFAUTS_PAR_CATEGORIE[cat], (x, cat)


def test_aucune_piece_pour_un_produit_de_securite():
    """R01 : un produit de sécurité endommagé se remplace, il ne se répare pas."""
    for x in [*data.pieces(), *data.prestations()]:
        assert not set(x.categories) & CATEGORIES_SECURITE


def test_occasion_et_location_pointent_vers_le_catalogue_sans_securite():
    for o in [*data.occasion(), *data.location()]:
        p = data.produit(o.product_id)
        assert p is not None
        assert not p.est_securite


def test_bareme_couvre_toutes_les_categories():
    assert set(data.bareme().plafond_par_categorie) == set(CATEGORIES)


def test_creneaux_calcules_dans_le_futur():
    maintenant = datetime(2026, 11, 12, 10, 0)
    for atelier in data.ateliers():
        creneaux = atelier.prochains_creneaux(maintenant, 3)
        assert len(creneaux) == 3
        assert all(datetime.fromisoformat(c) > maintenant for c in creneaux)
