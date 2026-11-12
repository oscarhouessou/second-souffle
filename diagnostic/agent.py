"""Agent Diagnostic : photo + description → fiche de diagnostic structurée (F02 à F05).

`adk web` cherche la variable `root_agent` dans ce module.
"""

from google.adk.agents import LlmAgent

from diagnostic.prompt import INSTRUCTION
from shared.config import generation_config, model_for
from shared.schemas import FicheDiagnostic

root_agent = LlmAgent(
    name="diagnostic",
    model=model_for("diagnostic"),
    description="Analyse la photo et la description d'un équipement de sport et produit une fiche de diagnostic.",
    instruction=INSTRUCTION,
    output_schema=FicheDiagnostic,  # Gemini doit répondre par un JSON conforme, validé par Pydantic
    output_key="fiche",  # le JSON validé est rangé dans l'état de session sous la clé "fiche"
    generate_content_config=generation_config(temperature=0.1),
)
