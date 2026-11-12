#!/usr/bin/env bash
# Déploie Second Souffle sur Cloud Run (lot 7). À lancer depuis la racine du dépôt :
#
#   PROJECT=mon-projet ./scripts/deploy.sh
#
# Ordre : serveur MCP, puis les 4 agents (privés), puis l'orchestrateur (seul service public).
# Coûts : Cloud Run avec mise à l'échelle à zéro (aucune instance au repos), Cloud Build et
# Artifact Registry à l'usage, appels Vertex AI à l'usage. Prévoir une alerte de budget (NF09).
set -euo pipefail

PROJECT="${PROJECT:?définir PROJECT=<id du projet GCP>}"
REGION="${REGION:-europe-west1}"
REPO=second-souffle
MODELE="${SECOND_SOUFFLE_MODEL:-gemini-3.5-flash-lite}"
MODELE_DIAG="${SECOND_SOUFFLE_MODEL_DIAGNOSTIC:-gemini-3.6-flash}"
SA_AGENTS="agents-second-souffle@${PROJECT}.iam.gserviceaccount.com"
SA_ORCH="orchestrateur-second-souffle@${PROJECT}.iam.gserviceaccount.com"
gc() { gcloud --project "$PROJECT" "$@"; }

echo "1/6 APIs"
gc services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  aiplatform.googleapis.com cloudtrace.googleapis.com logging.googleapis.com monitoring.googleapis.com

echo "2/6 Artifact Registry et comptes de service (moindre privilège, NF14)"
gc artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1 || \
  gc artifacts repositories create "$REPO" --repository-format docker --location "$REGION"
for sa in agents-second-souffle orchestrateur-second-souffle; do
  gc iam service-accounts describe "${sa}@${PROJECT}.iam.gserviceaccount.com" >/dev/null 2>&1 || \
    gc iam service-accounts create "$sa" --display-name "Second Souffle ($sa)"
done
for sa in "$SA_AGENTS" "$SA_ORCH"; do
  for role in roles/aiplatform.user roles/cloudtrace.agent roles/logging.logWriter roles/monitoring.metricWriter; do
    gc projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$sa" --role "$role" --condition None >/dev/null
  done
done

echo "3/6 Images (un build Cloud Build par service)"
# Un par un : sur un projet neuf, le premier build crée le bucket de Cloud Build ; en parallèle, les
# autres échouent. Et avec set -e, un build en échec arrête le script (pas de déploiement sans image).
# SKIP_BUILD=1 réutilise les images déjà publiées.
if [ "${SKIP_BUILD:-}" != "1" ]; then
  for s in mcp_catalog diagnostic repair valuation judge orchestrator; do
    echo "  ▶ build $s"
    gc builds submit --config ".cloudbuild/$s.yaml" --substitutions "_REGION=$REGION" --quiet . > "/tmp/build-$s.log" 2>&1 \
      || { echo "build $s en échec :"; tail -20 "/tmp/build-$s.log"; exit 1; }
  done
fi

image() { echo "${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/$1:latest"; }
url() { gc run services describe "$1" --region "$REGION" --format 'value(status.url)'; }
COMMUN="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=eu,SECOND_SOUFFLE_MODEL=${MODELE},SECOND_SOUFFLE_MODEL_DIAGNOSTIC=${MODELE_DIAG},AUTH_ID_TOKEN=1,OTEL_TO_CLOUD=1"
PRIVE=(--no-allow-unauthenticated --region "$REGION" --min-instances 0 --max-instances 3 --cpu 1 --memory 1Gi)

echo "4/6 Serveur MCP (privé)"
gc run deploy mcp-catalog --image "$(image mcp-catalog)" --service-account "$SA_AGENTS" "${PRIVE[@]}"
MCP_URL="$(url mcp-catalog)/mcp"

echo "5/6 Agents (privés)"
for s in diagnostic repair valuation judge; do
  nom="agent-$s"
  gc run deploy "$nom" --image "$(image "$s")" --service-account "$SA_AGENTS" "${PRIVE[@]}" \
    --set-env-vars "${COMMUN},MCP_CATALOG_URL=${MCP_URL}"
  # La carte A2A doit annoncer l'URL publique du service : second déploiement léger avec PUBLIC_URL.
  gc run services update "$nom" --region "$REGION" --update-env-vars "PUBLIC_URL=$(url "$nom")"
done
# Les agents appellent le serveur MCP, l'orchestrateur appelle les agents.
gc run services add-iam-policy-binding mcp-catalog --region "$REGION" \
  --member "serviceAccount:$SA_AGENTS" --role roles/run.invoker
for s in diagnostic repair valuation judge; do
  gc run services add-iam-policy-binding "agent-$s" --region "$REGION" \
    --member "serviceAccount:$SA_ORCH" --role roles/run.invoker
done

echo "6/6 Orchestrateur (public)"
CARTES="DIAGNOSTIC_AGENT_CARD_URL=$(url agent-diagnostic)/.well-known/agent-card.json"
CARTES+=",REPAIR_AGENT_CARD_URL=$(url agent-repair)/.well-known/agent-card.json"
CARTES+=",VALUATION_AGENT_CARD_URL=$(url agent-valuation)/.well-known/agent-card.json"
CARTES+=",JUDGE_AGENT_CARD_URL=$(url agent-judge)/.well-known/agent-card.json"
gc run deploy orchestrateur --image "$(image orchestrator)" --service-account "$SA_ORCH" \
  --allow-unauthenticated --region "$REGION" --min-instances 0 --max-instances 3 --cpu 1 --memory 1Gi \
  --set-env-vars "${COMMUN},${CARTES},ADK_COMMAND=${ADK_COMMAND:-web}"

echo "✅ Démo : $(url orchestrateur)  (choisir « orchestrator »)"
