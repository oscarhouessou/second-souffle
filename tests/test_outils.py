from shared import outils


def test_chercher_pieces_tente_arceau():
    r = outils.chercher_pieces("tente", "arceau_casse")
    assert {p["part_id"] for p in r["pieces"]} >= {"PC-001"}


def test_categorie_inconnue_renvoie_une_erreur_explicite():
    assert "erreur" in outils.chercher_pieces("ski", "carre_abimee")


def test_trouver_atelier_meme_departement_et_repli():
    assert outils.trouver_atelier("59800")["ville"] in ("Lille", "Villeneuve-d'Ascq")
    loin = outils.trouver_atelier("29200")
    assert loin["meme_departement"] is False and loin["creneaux"]
    assert "erreur" in outils.trouver_atelier("abc")


def test_offre_rachat_securite_refusee():
    assert outils.calculer_offre_rachat("casque_velo", "bon", 1)["autorisee"] is False


def test_occasion_jamais_pour_securite():
    assert outils.chercher_occasion("casque_velo")["articles"] == []
