# data

Données **fictives**, générées par `scripts/generate_data.py`. Pour les régénérer :
`uv run python scripts/generate_data.py`.

| Fichier | Contenu | Volume |
| --- | --- | --- |
| `catalogue.json` | Produits génériques sans marque : catégorie, gamme, prix neuf, sécurité, empreinte CO₂e | 55 |
| `pieces.json` | Pièces détachées : défaut traité, prix, difficulté, lien de tutoriel fictif | 30 |
| `prestations.json` | Prestations d'atelier : défaut, prix, durée | 21 |
| `ateliers.json` | Ateliers fictifs : ville, code postal, planning hebdomadaire | 15 |
| `bareme.json` | Barème de rachat (R02) et ratios de CO₂ évité | 1 |
| `location.json` | Offres de location | 22 |
| `occasion.json` | Stock d'occasion contrôlé (aucun produit de sécurité, R01) | 40 |

Les prix sont des ordres de grandeur plausibles, choisis à la main. Les empreintes carbone et les
ratios de CO₂ évité sont des hypothèses de démonstration, pas des mesures.
Aucune donnée réelle de magasin, de produit ou de client n'est utilisée.
