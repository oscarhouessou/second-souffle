"""Service A2A de l'agent repair. Local : uv run uvicorn repair.server:app --port 8102"""

from repair.agent import root_agent
from shared.serveur_a2a import creer_app

app = creer_app(root_agent, port_defaut=8102)
