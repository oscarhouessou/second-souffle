# eval

Jeu d'évaluation de la section 9 du cahier des charges, joué de bout en bout dans l'orchestrateur.

- `scenarios.py` : 40 scénarios nominaux (diagnostic de référence), 10 cas limites, 15 attaques.
- `run_eval.py` : joue chaque scénario, note les critères et compare aux seuils.
- `resultats/dernier-rapport.md` : dernier rapport versionné (les détails JSON restent en local).

```bash
make eval            # 65 cas, environ 10 minutes, quelques centimes d'appels Vertex AI
make eval-rapide     # 2 cas par jeu
```

Le script sort avec le code 1 si un seuil n'est pas atteint : il peut bloquer une CI.

Non couvert pour l'instant : le LLM juge calibré sur 30 cas annotés pour la qualité des explications,
et les photos de test (le diagnostic est évalué sur des descriptions textuelles).
