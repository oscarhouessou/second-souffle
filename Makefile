.PHONY: install web run-local services test conversation data

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

conversation: ## Conversation de démo en ligne de commande
	uv run python scripts/conversation.py "ma tente a un arceau cassé et une petite déchirure, je l'ai depuis 3 ans" "je la répare moi-même" "oui"

data:         ## Régénère les données fictives
	uv run python scripts/generate_data.py

# À venir : eval (lot 6), deploy (lot 7)
