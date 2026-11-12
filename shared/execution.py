"""Exécuter un agent ADK sur un message isolé, hors de `adk web`.

C'est le même contrat qu'un appel A2A : un message en entrée (texte, JSON, images), un texte en
sortie. Utilisé pour les appels locaux entre agents, les scripts de test et l'évaluation.
"""

import time
import uuid
from dataclasses import dataclass, field

from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.genai import types


@dataclass
class ResultatAgent:
    texte: str
    tokens_entree: int = 0
    tokens_sortie: int = 0
    latence_s: float = 0.0
    appels_outils: list[dict] = field(default_factory=list)
    etat: dict = field(default_factory=dict)


async def executer_agent(agent: BaseAgent, parts: list[types.Part], etat_initial: dict | None = None) -> ResultatAgent:
    """Exécute `agent` sur un seul message utilisateur et agrège sa réponse finale."""
    runner = InMemoryRunner(agent=agent, app_name=f"appel_{agent.name}")
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="orchestrateur", state=etat_initial or {}, session_id=str(uuid.uuid4())
    )
    debut = time.perf_counter()
    resultat = ResultatAgent(texte="")
    textes: list[str] = []
    async for event in runner.run_async(
        user_id="orchestrateur", session_id=session.id, new_message=types.Content(role="user", parts=parts)
    ):
        if event.usage_metadata:
            resultat.tokens_entree += event.usage_metadata.prompt_token_count or 0
            resultat.tokens_sortie += (event.usage_metadata.candidates_token_count or 0) + (
                event.usage_metadata.thoughts_token_count or 0
            )
        for fc in event.get_function_calls():
            resultat.appels_outils.append({"nom": fc.name, "args": dict(fc.args or {})})
        if event.is_final_response() and event.content and event.content.parts:
            textes = [p.text for p in event.content.parts if p.text and not p.thought]
    resultat.latence_s = time.perf_counter() - debut
    resultat.texte = "".join(textes).strip()
    fin = await runner.session_service.get_session(app_name=runner.app_name, user_id="orchestrateur", session_id=session.id)
    resultat.etat = dict(fin.state) if fin else {}
    return resultat
