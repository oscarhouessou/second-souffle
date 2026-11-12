.PHONY: install web run-local services test eval eval-rapide mlflow-ui conversation data

install:      ## Crée .venv (Python 3.12) et installe les dépendances
	uv sync

web:          ## Interface ADK, agents exécutés en local dans un seul processus
	uv run adk web .

run-local:    ## Services A2A + MCP sur des ports séparés, puis l'interface ADK (orchestrateur distribué)
	./run_locally.sh

services:     ## Services A2A + MCP seulement (pour l'éval en mode distribué)
	./run_locally.sh --services

test:         ## Tests unitaires (règles, outils, juge, données), sans LLM
	uv run pytest

eval:         ## Jeu d'évaluation complet (65 cas, section 9) ; rapport dans eval/resultats/
	uv run python eval/run_eval.py

eval-rapide:  ## Deux cas par jeu, pour vérifier que tout tourne
	uv run python eval/run_eval.py --limite 2

mlflow-ui:    ## Interface MLflow : comparer les runs d'évaluation et leurs traces (http://localhost:5000)
	uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

conversation: ## Conversation de démo en ligne de commande
	uv run python scripts/conversation.py "ma tente a un arceau cassé et une petite déchirure, je l'ai depuis 3 ans" "je la répare moi-même" "oui"

data:         ## Régénère les données fictives
	uv run python scripts/generate_data.py

# À venir : deploy (lot 7)
