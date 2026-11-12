"""Service A2A de l'agent valuation. Local : uv run uvicorn valuation.server:app --port 8103"""

from valuation.agent import root_agent
from shared.serveur_a2a import creer_app

app = creer_app(root_agent, port_defaut=8103)
