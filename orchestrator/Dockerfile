# Orchestrateur (seul service public). Construire depuis la racine du dépôt :
#   docker build -f orchestrator/Dockerfile -t second-souffle-orchestrator .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Le code de tous les agents est copié : sans URL A2A, l'orchestrateur peut les exécuter en local.
COPY shared/ shared/
COPY data/ data/
COPY diagnostic/ diagnostic/
COPY repair/ repair/
COPY valuation/ valuation/
COPY judge/ judge/
COPY orchestrator/ orchestrator/
# Les URL des cartes A2A sont passées par variables d'environnement au déploiement.
# ADK_COMMAND=web sert l'interface de démo ; api_server (défaut) sert seulement l'API.
ENV ADK_COMMAND=api_server
# OTEL_TO_CLOUD=1 : spans ADK exportés vers Cloud Trace et Cloud Logging.
CMD ["sh", "-c", "uv run --no-sync adk $ADK_COMMAND ${OTEL_TO_CLOUD:+--otel_to_cloud} --host 0.0.0.0 --port ${PORT:-8080} ."]
