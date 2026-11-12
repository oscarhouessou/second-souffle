"""Appel d'un agent spécialiste distant par A2A (lot 4).

On réutilise `RemoteA2aAgent` d'ADK : il lit la carte de l'agent, envoie le message et convertit
la réponse en événements ADK. Comme en local, on l'exécute sur un seul message (le JSON construit par
l'orchestrateur) : le contrat est identique, seul le transport change.
"""

from functools import lru_cache

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types

from shared.config import TIMEOUT_APPEL_S
from shared.execution import ResultatAgent, executer_agent


@lru_cache
def _agent_distant(url_carte: str) -> RemoteA2aAgent:
    nom = url_carte.split("//", 1)[-1].split("/", 1)[0].replace(".", "_").replace(":", "_").replace("-", "_")
    return RemoteA2aAgent(name=f"distant_{nom}", agent_card=url_carte, timeout=TIMEOUT_APPEL_S)


async def appeler_a2a(url_carte: str, parts: list[types.Part]) -> ResultatAgent:
    return await executer_agent(_agent_distant(url_carte), parts)
