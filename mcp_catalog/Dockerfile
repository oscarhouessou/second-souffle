# Serveur MCP du catalogue (lecture seule). Construire depuis la racine du dépôt :
#   docker build -f mcp_catalog/Dockerfile -t second-souffle-mcp .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY shared/ shared/
COPY data/ data/
COPY mcp_catalog/ mcp_catalog/
CMD ["sh", "-c", "uv run --no-sync uvicorn mcp_catalog.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
