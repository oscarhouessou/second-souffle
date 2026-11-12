"""Génère les données fictives de data/ (section 7 du cahier des charges).

Les noms de produits sont génériques (aucune marque). Les prix sont des ordres de grandeur
plausibles pour le marché français du sport, choisis à la main ; les empreintes carbone sont des
hypothèses de démonstration. Relancer le script redonne exactement les mêmes fichiers.

    uv run python scripts/generate_data.py
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import CATEGORIES_SECURITE, DATA_DIR  # noqa: E402
from shared.vocabulaire import FAMILLES, famille_de  # noqa: E402

rng = random.Random(42)

# catégorie -> liste de (nom, gamme, prix neuf €, empreinte kg CO2e)
PRODUITS: dict[str, list[tuple[str, str, float, float]]] = {
    "velo_ville": [
        ("Vélo de ville cadre bas 6 vitesses", "entree", 199, 120),
        ("Vélo de ville 7 vitesses moyeu intégré", "milieu", 449, 140),
        ("Vélo de ville cadre aluminium 8 vitesses", "milieu", 549, 150),
        ("Vélo de ville longue distance 11 vitesses", "haut", 799, 170),
        ("Vélo pliant 6 vitesses", "milieu", 399, 110),
    ],
    "vtt": [
        ("VTT semi-rigide 27,5 pouces 8 vitesses", "entree", 299, 140),
        ("VTT semi-rigide 29 pouces 12 vitesses", "milieu", 699, 165),
        ("VTT tout-suspendu 29 pouces", "haut", 1399, 210),
        ("VTT junior 26 pouces", "entree", 249, 110),
    ],
    "velo_route": [
        ("Vélo de route aluminium 8 vitesses", "entree", 449, 150),
        ("Vélo de route endurance 11 vitesses", "milieu", 999, 185),
        ("Vélo de route carbone 12 vitesses", "haut", 1899, 230),
        ("Vélo gravel aluminium 10 vitesses", "milieu", 899, 175),
    ],
    "velo_enfant": [
        ("Draisienne enfant 2-4 ans", "entree", 59, 25),
        ("Vélo enfant 16 pouces 4-6 ans", "entree", 119, 45),
        ("Vélo enfant 20 pouces 6-9 ans", "milieu", 199, 60),
        ("Vélo enfant 24 pouces 9-12 ans", "milieu", 279, 75),
    ],
    "siege_velo_enfant": [
        ("Siège vélo enfant arrière sur porte-bagages", "entree", 45, 8),
        ("Siège vélo enfant arrière inclinable", "milieu", 99, 11),
        ("Siège vélo enfant avant", "milieu", 79, 9),
    ],
    "casque_velo": [
        ("Casque vélo urbain", "entree", 19, 2),
        ("Casque VTT avec visière", "milieu", 49, 3),
        ("Casque vélo route ventilé", "haut", 99, 4),
        ("Casque vélo enfant", "entree", 15, 2),
    ],
    "tente": [
        ("Tente dôme 2 places", "entree", 49, 15),
        ("Tente dôme 3 places", "milieu", 99, 22),
        ("Tente familiale 4 places 2 chambres", "milieu", 199, 32),
        ("Tente de trekking 2 places ultralégère", "haut", 349, 20),
        ("Tente gonflable 4 places", "haut", 399, 38),
    ],
    "sac_couchage": [
        ("Sac de couchage 15 °C", "entree", 25, 8),
        ("Sac de couchage 5 °C", "milieu", 69, 12),
        ("Sac de couchage duvet 0 °C", "haut", 179, 18),
        ("Sac de couchage enfant 10 °C", "entree", 35, 7),
        ("Sac de couchage enfant évolutif 5 °C", "milieu", 59, 9),
    ],
    "matelas_camping": [
        ("Matelas mousse de camping", "entree", 19, 4),
        ("Matelas autogonflant 1 personne", "milieu", 49, 6),
        ("Matelas gonflable 2 personnes", "milieu", 59, 7),
        ("Matelas de trekking isolant", "haut", 99, 8),
    ],
    "chaussures_randonnee": [
        ("Chaussures de randonnée basses", "entree", 39, 12),
        ("Chaussures de randonnée mi-hautes imperméables", "milieu", 89, 14),
        ("Chaussures de trekking cuir imperméables", "haut", 169, 17),
        ("Chaussures de randonnée enfant imperméables", "entree", 35, 10),
        ("Chaussures de randonnée rapide légères", "milieu", 99, 13),
    ],
    "sac_a_dos": [
        ("Sac à dos de randonnée 20 L", "entree", 19, 6),
        ("Sac à dos de randonnée 30 L", "milieu", 49, 8),
        ("Sac à dos de trekking 50 L", "milieu", 99, 11),
        ("Sac à dos de trekking 70 L", "haut", 169, 13),
        ("Sac à dos enfant 10 L", "entree", 15, 4),
    ],
    "batons_marche": [
        ("Bâtons de marche télescopiques (paire)", "entree", 15, 3),
        ("Bâtons de randonnée réglables (paire)", "milieu", 35, 4),
        ("Bâtons de trekking carbone pliants (paire)", "haut", 79, 5),
    ],
    "veste_impermeable": [
        ("Veste imperméable de randonnée", "entree", 29, 10),
        ("Veste imperméable respirante 3 couches", "milieu", 79, 15),
        ("Veste de trekking imperméable haute montagne", "haut", 199, 22),
        ("Veste imperméable enfant", "entree", 25, 8),
    ],
}

# (catégories, défaut, nom, prix €, difficulté)
PIECES: list[tuple[list[str], str, str, float, str]] = [
    (["tente"], "arceau_casse", "Kit de réparation d'arceau fibre (manchon + élastique)", 9.99, "facile"),
    (["tente"], "arceau_casse", "Arceau fibre de remplacement Ø 8,5 mm", 14.99, "moyen"),
    (["tente"], "arceau_casse", "Arceau aluminium de remplacement Ø 9,5 mm", 24.99, "moyen"),
    (["tente"], "dechirure_toile", "Patchs autocollants pour toile de tente (lot de 4)", 4.99, "facile"),
    (["tente"], "dechirure_toile", "Kit de réparation toile avec colle souple", 8.99, "facile"),
    (["tente", "sac_couchage", "sac_a_dos", "veste_impermeable"], "fermeture_eclair_cassee",
     "Curseurs de fermeture éclair (lot de 2)", 5.99, "moyen"),
    (["tente"], "tendeur_casse", "Tendeurs de tente avec cordelette (lot de 4)", 4.99, "facile"),
    (["tente"], "sardines_manquantes", "Sardines aluminium (lot de 10)", 6.99, "facile"),
    (["tente", "chaussures_randonnee", "veste_impermeable"], "impermeabilite_degradee",
     "Spray imperméabilisant 300 ml", 9.99, "facile"),
    (["sac_couchage", "sac_a_dos", "veste_impermeable"], "dechirure_tissu",
     "Patchs nylon autocollants (lot de 6)", 5.99, "facile"),
    (["matelas_camping"], "crevaison", "Kit de rustines pour matelas", 4.99, "facile"),
    (["matelas_camping"], "valve_defectueuse", "Valve de remplacement pour matelas autogonflant", 6.99, "moyen"),
    (["chaussures_randonnee"], "semelle_decollee", "Colle néoprène pour chaussures 30 g", 7.99, "facile"),
    (["chaussures_randonnee"], "lacets_casses", "Lacets ronds de randonnée 150 cm", 3.99, "facile"),
    (["sac_a_dos"], "boucle_cassee", "Boucles clipsables 25 mm (lot de 2)", 3.99, "facile"),
    (["sac_a_dos"], "bretelle_dechiree", "Kit couture renforcée pour sangles", 7.99, "moyen"),
    (["batons_marche"], "embout_use", "Embouts carbure de remplacement (paire)", 5.99, "facile"),
    (["batons_marche"], "blocage_casse", "Kit de blocage rapide pour bâton", 7.99, "moyen"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "freins_uses", "Patins de frein V-brake (paire)", 6.99, "moyen"),
    (["velo_ville", "vtt", "velo_route"], "freins_uses", "Plaquettes de frein à disque (paire)", 12.99, "moyen"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "chaine_usee", "Chaîne 8 vitesses", 14.99, "moyen"),
    (["vtt", "velo_route"], "chaine_usee", "Chaîne 11/12 vitesses", 29.99, "moyen"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "pneu_creve", "Chambre à air avec valve Presta ou Schrader", 5.99, "facile"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "pneu_creve", "Kit de réparation crevaison", 4.99, "facile"),
    (["velo_ville", "velo_enfant"], "pneu_use", "Pneu ville renforcé anti-crevaison", 19.99, "moyen"),
    (["vtt"], "pneu_use", "Pneu VTT 29 pouces", 24.99, "moyen"),
    (["velo_route"], "pneu_use", "Pneu route 700x28", 22.99, "moyen"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "derailleur_deregle", "Câble et gaine de dérailleur", 4.99, "moyen"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "rayon_casse", "Rayons inox avec écrous (lot de 4)", 6.99, "atelier"),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "eclairage_defectueux", "Kit d'éclairage LED avant et arrière", 14.99, "facile"),
]

# (catégories, défaut, prix €, durée jours)
PRESTATIONS: list[tuple[list[str], str, float, int]] = [
    (["tente"], "arceau_casse", 25, 7),
    (["tente"], "dechirure_toile", 20, 7),
    (["tente", "sac_couchage", "sac_a_dos", "veste_impermeable"], "fermeture_eclair_cassee", 25, 10),
    (["tente"], "tendeur_casse", 10, 3),
    (["sac_couchage", "sac_a_dos", "veste_impermeable"], "dechirure_tissu", 15, 7),
    (["matelas_camping"], "valve_defectueuse", 15, 5),
    (["matelas_camping"], "crevaison", 10, 3),
    (["chaussures_randonnee"], "semelle_decollee", 25, 10),
    (["chaussures_randonnee"], "semelle_usee", 45, 14),
    (["chaussures_randonnee"], "couture_decousue", 15, 7),
    (["sac_a_dos"], "bretelle_dechiree", 20, 10),
    (["sac_a_dos"], "boucle_cassee", 8, 3),
    (["batons_marche"], "blocage_casse", 12, 5),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "freins_uses", 15, 1),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "chaine_usee", 25, 1),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "pneu_creve", 12, 1),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "pneu_use", 30, 1),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "derailleur_deregle", 15, 1),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "rayon_casse", 20, 2),
    (["velo_ville", "vtt", "velo_route", "velo_enfant"], "eclairage_defectueux", 15, 1),
    (["vtt"], "suspension_fuit", 69, 14),
]

ATELIERS = [
    ("Lille", "59000"), ("Villeneuve-d'Ascq", "59650"), ("Paris 11e", "75011"), ("Paris 15e", "75015"),
    ("Lyon", "69007"), ("Marseille", "13008"), ("Toulouse", "31000"), ("Bordeaux", "33000"),
    ("Nantes", "44000"), ("Rennes", "35000"), ("Strasbourg", "67000"), ("Montpellier", "34000"),
    ("Nice", "06200"), ("Grenoble", "38000"), ("Annecy", "74000"),
]

BAREME = {
    "_note": "Barème fictif. R02 : offre = prix neuf de référence × coef. état × coef. âge, plafonnée.",
    "coef_etat": {"bon": 0.45, "moyen": 0.30, "use": 0.15, "hors_usage": 0.0},
    "coef_age": [
        {"age_max_annees": 1, "coef": 1.0},
        {"age_max_annees": 2, "coef": 0.85},
        {"age_max_annees": 4, "coef": 0.70},
        {"age_max_annees": 6, "coef": 0.50},
        {"age_max_annees": None, "coef": 0.30},
    ],
    "plafond_par_categorie": {
        "velo_ville": 250, "vtt": 450, "velo_route": 600, "velo_enfant": 80,
        "siege_velo_enfant": 0, "casque_velo": 0,
        "tente": 120, "sac_couchage": 60, "matelas_camping": 30,
        "chaussures_randonnee": 50, "sac_a_dos": 50, "batons_marche": 25, "veste_impermeable": 60,
    },
    "co2_evite_ratio": {
        "_note": "Part de l'empreinte d'un produit neuf évitée par option (hypothèses de démonstration).",
        "reparer": 0.75, "occasion": 0.80, "louer": 0.60, "revendre": 0.50, "recycler": 0.05,
    },
}

CATEGORIES_LOCATION = {"tente", "sac_couchage", "matelas_camping", "sac_a_dos", "velo_ville", "vtt", "velo_route"}


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    catalogue = []
    for famille, cats in FAMILLES.items():
        for cat in cats:
            for i, (nom, gamme, prix, co2) in enumerate(PRODUITS[cat], start=1):
                catalogue.append({
                    "product_id": f"P-{cat.upper()[:6]}-{i:02d}",
                    "nom": nom,
                    "famille": famille,
                    "categorie": cat,
                    "gamme": gamme,
                    "prix_neuf_eur": float(prix),
                    "est_securite": cat in CATEGORIES_SECURITE,
                    "co2_kg": float(co2),
                })

    pieces = [
        {
            "part_id": f"PC-{i:03d}",
            "nom": nom,
            "categories": cats,
            "defaut": defaut,
            "prix_eur": prix,
            "difficulte": diff,
            "tutoriel": f"https://second-souffle.example/tutos/{defaut.replace('_', '-')}-{i:03d}",
        }
        for i, (cats, defaut, nom, prix, diff) in enumerate(PIECES, start=1)
    ]

    prestations = [
        {"service_id": f"SV-{i:03d}", "categories": cats, "defaut": defaut, "prix_eur": float(prix), "duree_jours": duree}
        for i, (cats, defaut, prix, duree) in enumerate(PRESTATIONS, start=1)
    ]

    ateliers = []
    for i, (ville, cp) in enumerate(ATELIERS, start=1):
        jours = sorted(rng.sample([1, 2, 3, 4, 5, 6], k=rng.choice([3, 4, 5])))
        heures = sorted(rng.sample(["09:30", "11:00", "14:00", "15:30", "17:00"], k=3))
        ateliers.append({
            "workshop_id": f"AT-{i:02d}",
            "nom": f"Atelier Second Souffle {ville}",
            "ville": ville,
            "code_postal": cp,
            "jours_ouverture": jours,  # 1 = lundi … 7 = dimanche
            "horaires_creneaux": heures,
        })

    location = []
    for p in catalogue:
        if p["categorie"] in CATEGORIES_LOCATION and p["gamme"] != "entree":
            jour = round(max(3.0, p["prix_neuf_eur"] * 0.06), 0)
            location.append({
                "product_id": p["product_id"],
                "prix_jour_eur": jour,
                "prix_semaine_eur": round(jour * 4, 0),
                "caution_eur": round(p["prix_neuf_eur"] * 0.5, 0),
            })

    occasion = []
    ratios = {"comme_neuf": 0.70, "tres_bon": 0.55, "bon": 0.45}
    eligibles = [p for p in catalogue if not p["est_securite"]]
    for i in range(1, 41):
        p = rng.choice(eligibles)
        etat = rng.choice(list(ratios))
        occasion.append({
            "item_id": f"OC-{i:03d}",
            "product_id": p["product_id"],
            "etat_controle": etat,
            "prix_eur": round(p["prix_neuf_eur"] * ratios[etat] - 0.01, 2),
        })

    fichiers = {
        "catalogue.json": catalogue,
        "pieces.json": pieces,
        "prestations.json": prestations,
        "ateliers.json": ateliers,
        "bareme.json": BAREME,
        "location.json": location,
        "occasion.json": occasion,
    }
    for nom, contenu in fichiers.items():
        (DATA_DIR / nom).write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        taille = len(contenu) if isinstance(contenu, list) else 1
        print(f"{nom:20s} {taille:3d} entrées")


if __name__ == "__main__":
    main()
