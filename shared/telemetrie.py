"""Traçage distribué vers Cloud Trace (section 8, Observabilité).

ADK crée déjà un span par agent, appel LLM et appel d'outil. Il reste à :
1. exporter ces spans vers Google Cloud (Cloud Trace, Logging, Monitoring) ;
2. propager le contexte de trace dans les appels HTTP sortants (A2A, MCP) : instrumentation httpx ;
3. reprendre ce contexte à l'arrivée d'une requête : instrumentation Starlette côté services.
Ainsi une conversation forme une seule trace, de l'orchestrateur jusqu'au serveur MCP.
Activé seulement si OTEL_TO_CLOUD=1 (Cloud Run) : en local, rien n'est exporté.
"""

import logging
import os

log = logging.getLogger("second_souffle")
_fait = False


def activer_tracage(app=None) -> None:
    global _fait
    if os.getenv("OTEL_TO_CLOUD") != "1":
        return
    try:
        if not _fait:
            import google.auth
            from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
            from google.adk.telemetry.setup import maybe_set_otel_providers
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            credentials, projet = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            maybe_set_otel_providers(
                otel_hooks_to_setup=[get_gcp_exporters(
                    enable_cloud_tracing=True, enable_cloud_metrics=True, enable_cloud_logging=True,
                    google_auth=(credentials, projet),
                )],
                otel_resource=get_gcp_resource(projet),
            )
            HTTPXClientInstrumentor().instrument()
            _fait = True
        if app is not None:
            from opentelemetry.instrumentation.starlette import StarletteInstrumentor

            StarletteInstrumentor.instrument_app(app)
    except Exception as e:  # le traçage ne doit jamais empêcher le service de démarrer
        log.warning("traçage Cloud Trace non activé : %s", e)
