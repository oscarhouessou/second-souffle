"""Agent Diagnostic : analyse la photo et la description, produit la fiche de diagnostic.

`adk web` cherche la variable `root_agent` dans ce module.
"""

import os

from google.adk.agents import LlmAgent

MODEL = os.getenv("SECOND_SOUFFLE_MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    name="diagnostic",
    model=MODEL,
    description="Analyse la photo et la description d'un équipement de sport et produit une fiche de diagnostic.",
    instruction=(
        "Tu es l'agent de diagnostic de Second Souffle, un assistant qui aide à donner une seconde vie "
        "à l'équipement de sport. Pose des questions pour comprendre le produit (type, âge, état, problème) "
        "et résume ce que tu as compris."
    ),
)
