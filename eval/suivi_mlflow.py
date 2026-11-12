"""Suivi des évaluations dans MLflow : un run par `make eval`.

Chaque run enregistre :
- paramètres : modèle de chaque rôle, version de chaque prompt, niveau de réflexion, seuils ;
- métriques : les critères de la section 9, latences p50/p95, coût, taux de repli de modèle ;
- traces : un span par scénario (messages, réponses), avec un span enfant par étape (latence,
  outils appelés, repli de modèle) construit à partir des métadonnées de l'orchestrateur ;
- artefacts : le rapport Markdown et le détail JSON.

On compare ensuite les runs dans l'interface (`make mlflow-ui`) : « prompt v2 contre v3 »,
« diagnostic sur Flash contre Flash-Lite »… C'est ce qui permet de choisir un modèle sur mesure (NF08).

Sans MLflow installé, ou avec --sans-mlflow, l'évaluation tourne exactement comme avant.
"""

import contextlib
import os
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
EXPERIENCE = "second-souffle-eval"

try:
    import mlflow
    from mlflow.entities import SpanType
except ImportError:  # MLflow est une dépendance de développement
    mlflow = None


def actif() -> bool:
    return mlflow is not None and os.getenv("SANS_MLFLOW") != "1"


def demarrer(nom_run: str) -> None:
    if not actif():
        return
    if not os.getenv("MLFLOW_TRACKING_URI"):
        mlflow.set_tracking_uri(f"sqlite:///{RACINE / 'mlflow.db'}")  # serveur local par défaut
    mlflow.set_experiment(EXPERIENCE)
    # Pas de mlflow.gemini.autolog() : testé le 2026-11-12 (MLflow 3.18, ADK 2.14), le patch de
    # google-genai renvoie None à ADK et casse les appels. Le détail des appels LLM est dans Cloud Trace.
    mlflow.start_run(run_name=nom_run)
    mlflow.set_tags({"commit": _commit(), "branche": _branche()})


def journaliser_config(params: dict) -> None:
    if actif():
        mlflow.log_params({k: str(v)[:500] for k, v in params.items()})


@contextlib.contextmanager
def span_scenario(jeu: str, nom: str, messages: list[str]):
    """Span racine d'un scénario : les appels Gemini du scénario s'y rattachent."""
    if not actif():
        yield None
        return
    with mlflow.start_span(name=f"{jeu} · {nom[:60]}", span_type=SpanType.AGENT) as span:
        span.set_inputs({"messages": messages})
        span.set_attributes({"jeu": jeu, "scenario": nom})
        yield span


def journaliser_etapes(tours: list[dict]) -> None:
    """Un span enfant par étape spécialiste, sous le span du scénario en cours."""
    if not actif():
        return
    for i, tour in enumerate(tours, start=1):
        for etape, meta in tour["etapes"].items():
            with mlflow.start_span(name=f"tour {i} · {etape}", span_type=SpanType.TOOL) as span:
                span.set_inputs({"message_client": tour["client"]})
                span.set_outputs({"outils": meta.get("appels_outils"), "tokens": meta.get("tokens")})
                span.set_attributes({"latence_s": meta.get("latence_s"), "repli_modele": meta.get("repli_modele", False)})


def terminer(metriques: dict, verdict: bool, fichiers: list[Path]) -> str | None:
    if not actif():
        return None
    mlflow.log_metrics({k: float(v) for k, v in metriques.items() if v is not None})
    mlflow.set_tag("verdict", "seuils atteints" if verdict else "seuils non atteints")
    for f in fichiers:
        mlflow.log_artifact(str(f))
    run = mlflow.active_run()
    mlflow.flush_trace_async_logging()
    mlflow.end_run()
    return run.info.run_id if run else None


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=RACINE, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def _commit() -> str:
    return _git("rev-parse", "--short", "HEAD")


def _branche() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD")
