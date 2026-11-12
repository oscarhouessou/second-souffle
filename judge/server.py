"""Service A2A de l'agent judge. Local : uv run uvicorn judge.server:app --port 8104"""

from judge.agent import root_agent
from shared.serveur_a2a import creer_app

app = creer_app(root_agent, port_defaut=8104)
