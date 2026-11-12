# Second Souffle

Assistant multi-agent (Google ADK + Gemini) qui aide un sportif à donner une seconde vie à son équipement :
réparer, revendre, louer ou racheter d'occasion.

> Projet de démonstration personnel. Catalogue, barème de rachat et ateliers sont **fictifs**.
> Aucune donnée, marque ni logo réels.

## Démarrage

Prérequis : [uv](https://docs.astral.sh/uv/), `gcloud`, un projet GCP avec l'API Vertex AI activée.

```bash
make install                              # crée .venv (Python 3.12) et installe les dépendances
cp .env.example .env                      # puis renseigner GOOGLE_CLOUD_PROJECT
gcloud auth application-default login
make web                                  # interface de test sur http://localhost:8000
```

## Structure

```
second-souffle/
├── orchestrator/   # point d'entrée : SequentialAgent + LoopAgent (lot 3)
├── diagnostic/     # agent Diagnostic : photo + texte → fiche (lot 1)
├── repair/         # agent Réparation (lot 2)
├── valuation/      # agent Valorisation (lot 2)
├── judge/          # agent Juge des règles métier (lot 3)
├── mcp_catalog/    # serveur MCP du catalogue (lot 5)
├── shared/         # schémas Pydantic, règles métier, config
├── data/           # données fictives
├── eval/           # scénarios d'évaluation et attaques (lot 6)
├── tests/          # tests unitaires
├── .cloudbuild/    # build et déploiement par service (lot 7)
├── Makefile
└── pyproject.toml / uv.lock
```

Chaque dossier d'agent contient directement un `agent.py` qui expose `root_agent` :
`adk web .` lancé depuis la racine les liste tous, et ils importent le code commun via `shared`.

## Feuille de route

| Lot | Contenu | Concepts ADK |
| --- | --- | --- |
| 1 | Fondations : données fictives, schémas, agent Diagnostic | `LlmAgent`, sortie structurée, multimodal |
| 2 | Règles R01–R08, agents Réparation et Valorisation | `FunctionTool`, état de session |
| 3 | Orchestrateur et Juge, en local | `SequentialAgent`, `LoopAgent` |
| 4 | Un service par agent, A2A | `RemoteA2aAgent` |
| 5 | Serveur MCP, guardrails | `MCPToolset`, callbacks, Model Armor |
| 6 | Évaluation | éval ADK |
| 7 | Déploiement Cloud Run, traçage, coûts | observabilité |
