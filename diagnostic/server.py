"""Service A2A de l'agent diagnostic. Local : uv run uvicorn diagnostic.server:app --port 8101"""

from diagnostic.agent import root_agent
from shared.serveur_a2a import creer_app

app = creer_app(root_agent, port_defaut=8101)
