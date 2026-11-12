"""Vocabulaire fermé : familles, catégories et défauts reconnus.

Un vocabulaire fermé rend le diagnostic vérifiable (on compare des codes, pas des phrases)
et permet aux règles et aux outils de retrouver pièces et prestations sans LLM.
"""

FAMILLES: dict[str, list[str]] = {
    "velo": ["velo_ville", "vtt", "velo_route", "velo_enfant", "siege_velo_enfant", "casque_velo"],
    "camping": ["tente", "sac_couchage", "matelas_camping"],
    "randonnee": ["chaussures_randonnee", "sac_a_dos", "batons_marche", "veste_impermeable"],
}

LIBELLES_CATEGORIES: dict[str, str] = {
    "velo_ville": "vélo de ville",
    "vtt": "VTT",
    "velo_route": "vélo de route",
    "velo_enfant": "vélo enfant",
    "siege_velo_enfant": "siège vélo enfant",
    "casque_velo": "casque de vélo",
    "tente": "tente",
    "sac_couchage": "sac de couchage",
    "matelas_camping": "matelas de camping",
    "chaussures_randonnee": "chaussures de randonnée",
    "sac_a_dos": "sac à dos",
    "batons_marche": "bâtons de marche",
    "veste_impermeable": "veste imperméable",
}

_VELO = [
    "freins_uses",
    "chaine_usee",
    "pneu_creve",
    "pneu_use",
    "derailleur_deregle",
    "rayon_casse",
    "eclairage_defectueux",
    "cadre_fissure",
]

DEFAUTS_PAR_CATEGORIE: dict[str, list[str]] = {
    "velo_ville": _VELO,
    "vtt": _VELO + ["suspension_fuit"],
    "velo_route": _VELO,
    "velo_enfant": _VELO,
    "siege_velo_enfant": ["sangle_cassee", "fixation_cassee", "coque_fissuree"],
    "casque_velo": ["choc_coque", "sangle_cassee"],
    "tente": [
        "arceau_casse",
        "dechirure_toile",
        "fermeture_eclair_cassee",
        "tendeur_casse",
        "impermeabilite_degradee",
        "sardines_manquantes",
    ],
    "sac_couchage": ["fermeture_eclair_cassee", "dechirure_tissu", "perte_gonflant"],
    "matelas_camping": ["crevaison", "valve_defectueuse"],
    "chaussures_randonnee": [
        "semelle_decollee",
        "semelle_usee",
        "lacets_casses",
        "impermeabilite_degradee",
        "couture_decousue",
    ],
    "sac_a_dos": ["fermeture_eclair_cassee", "boucle_cassee", "bretelle_dechiree", "dechirure_tissu"],
    "batons_marche": ["blocage_casse", "embout_use"],
    "veste_impermeable": ["fermeture_eclair_cassee", "dechirure_tissu", "impermeabilite_degradee"],
}

# Défauts qui rendent un produit dangereux à l'usage, quelle que soit la catégorie.
DEFAUTS_CRITIQUES = frozenset({"cadre_fissure", "choc_coque", "coque_fissuree", "fixation_cassee"})

CATEGORIES: list[str] = [c for cats in FAMILLES.values() for c in cats]
TYPES_DEFAUT: list[str] = sorted({d for ds in DEFAUTS_PAR_CATEGORIE.values() for d in ds} | {"autre"})


def famille_de(categorie: str) -> str:
    for famille, cats in FAMILLES.items():
        if categorie in cats:
            return famille
    raise KeyError(categorie)


def vocabulaire_markdown() -> str:
    """Le vocabulaire sous forme de liste, à insérer dans un prompt."""
    lignes = []
    for famille, cats in FAMILLES.items():
        lignes.append(f"- famille `{famille}` :")
        for c in cats:
            defauts = ", ".join(DEFAUTS_PAR_CATEGORIE[c])
            lignes.append(f"  - `{c}` ({LIBELLES_CATEGORIES[c]}) — défauts : {defauts}")
    return "\n".join(lignes)
