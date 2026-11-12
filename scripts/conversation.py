"""Joue une conversation complète avec l'orchestrateur, message par message.

    uv run python scripts/conversation.py "ma tente a un arceau cassé, 3 ans" "je répare moi-même" "oui"
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from orchestrator.agent import root_agent  # noqa: E402


async def jouer(messages: list[str], afficher: bool = True) -> dict:
    runner = InMemoryRunner(agent=root_agent, app_name="second_souffle")
    session = await runner.session_service.create_session(app_name="second_souffle", user_id="demo")
    tours = []
    for msg in messages:
        debut = time.perf_counter()
        reponses, outils = [], []
        async for ev in runner.run_async(
            user_id="demo", session_id=session.id, new_message=types.Content(role="user", parts=[types.Part(text=msg)])
        ):
            outils += [fc.name for fc in ev.get_function_calls()]
            if ev.author in (root_agent.name, "conseiller") and ev.content and ev.content.parts:
                texte = "".join(p.text or "" for p in ev.content.parts if not p.thought)
                if texte.strip():
                    reponses.append(texte)
        latence = time.perf_counter() - debut
        tours.append({"client": msg, "reponse": "\n".join(reponses), "latence_s": latence, "outils": outils})
        if afficher:
            print(f"\n👤 {msg}\n🤖 ({latence:.1f} s{', outils : ' + ', '.join(outils) if outils else ''})\n" + "\n".join(reponses))
    fin = await runner.session_service.get_session(app_name="second_souffle", user_id="demo", session_id=session.id)
    if afficher:
        u = fin.state.get("usage") or {}
        print(f"\n— phase : {fin.state.get('phase')} · tokens : {u.get('tokens_entree', 0)} + {u.get('tokens_sortie', 0)}"
              f" · coût ≈ {u.get('cout_eur', 0):.4f} € · actions : {fin.state.get('actions')}")
    return {"tours": tours, "etat": dict(fin.state)}


if __name__ == "__main__":
    asyncio.run(jouer(sys.argv[1:] or ["ma tente a un arceau cassé et une petite déchirure, je l'ai depuis 3 ans"]))
