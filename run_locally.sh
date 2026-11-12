#!/usr/bin/env bash
# Lance tous les services en local, chacun sur son port, puis l'orchestrateur (adk web) qui les
# appelle par A2A. Ctrl+C arrête tout.
#
#   ./run_locally.sh            # services A2A + MCP + interface adk web sur http://localhost:8000
#   ./run_locally.sh --services # services seulement (pour les tests ou l'éval)
set -euo pipefail
cd "$(dirname "$0")"
unset VIRTUAL_ENV
MODE="${1:-}"

SERVICES=("mcp_catalog.server:app 8105" "diagnostic.server:app 8101" "repair.server:app 8102" "valuation.server:app 8103" "judge.server:app 8104")
PIDS=()
trap 'kill "${PIDS[@]}" 2>/dev/null; wait 2>/dev/null' EXIT INT TERM

mkdir -p .logs
for s in "${SERVICES[@]}"; do
  read -r module port <<< "$s"
  service="${module%%.*}"
  [ -f "$service/server.py" ] || continue
  uv run uvicorn "$module" --port "$port" --log-level warning > ".logs/$service.log" 2>&1 &
  PIDS+=($!)
  echo "▶ $service sur http://localhost:$port"
done

# Attendre que chaque service réponde
for port in 8101 8102 8103 8104; do
  for _ in $(seq 1 60); do
    curl -sf "http://localhost:$port/.well-known/agent-card.json" > /dev/null && break
    sleep 0.5
  done
done

export DIAGNOSTIC_AGENT_CARD_URL=http://localhost:8101/.well-known/agent-card.json
export REPAIR_AGENT_CARD_URL=http://localhost:8102/.well-known/agent-card.json
export VALUATION_AGENT_CARD_URL=http://localhost:8103/.well-known/agent-card.json
export JUDGE_AGENT_CARD_URL=http://localhost:8104/.well-known/agent-card.json
export MCP_CATALOG_URL=${MCP_CATALOG_URL:-http://localhost:8105/mcp}

if [ "$MODE" = "--services" ]; then
  echo "Services prêts. Ctrl+C pour arrêter."
  wait
else
  echo "▶ orchestrateur (adk web) sur http://localhost:8000 — choisir « orchestrator »"
  uv run adk web --port 8000 .
fi
