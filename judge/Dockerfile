# Service A2A « judge ». Construire depuis la racine du dépôt :
#   docker build -f judge/Dockerfile -t second-souffle-judge .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY shared/ shared/
COPY data/ data/
COPY judge/ judge/
# Cloud Run fournit PORT ; PUBLIC_URL est l'adresse publiée dans la carte A2A.
CMD ["sh", "-c", "uv run --no-sync uvicorn judge.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
