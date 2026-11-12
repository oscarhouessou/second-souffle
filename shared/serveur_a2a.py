"""Expose un agent ADK comme service A2A (lot 4).

    uv run uvicorn diagnostic.server:app --port 8101

L'agent publie sa carte sur /.well-known/agent-card.json. Sur Cloud Run, PUBLIC_URL donne l'adresse
publiée dans la carte (https://…run.app) ; en local, http://localhost:<PORT>.
"""

import os
from urllib.parse import urlparse

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent


def creer_app(agent: BaseAgent, port_defaut: int):
    port = int(os.getenv("PORT", port_defaut))
    publique = urlparse(os.getenv("PUBLIC_URL", f"http://localhost:{port}"))
    return to_a2a(
        agent,
        host=publique.hostname or "localhost",
        port=publique.port or (443 if publique.scheme == "https" else port),
        protocol=publique.scheme or "http",
    )
