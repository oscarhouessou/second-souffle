.PHONY: install web test

install:  ## Crée .venv (Python 3.12) et installe les dépendances
	uv sync

web:      ## Interface de test ADK sur http://localhost:8000
	uv run adk web .

test:     ## Tests unitaires (règles métier et outils)
	uv run pytest

# À venir : run-local (lot 4), eval (lot 6), deploy (lot 7)
