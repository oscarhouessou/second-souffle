"""Agent Réparation : pièces, tutoriels, prestation d'atelier et créneau (F06 à F08)."""

from google.adk.agents import LlmAgent

from repair.prompt import INSTRUCTION
from shared.config import generation_config, model_for
from shared.outils import OUTILS_REPARATION
from shared.outils_mcp import outils_catalogue
from shared.schemas import PropositionReparation

root_agent = LlmAgent(
    name="reparation",
    model=model_for("repair"),
    description="Trouve les pièces, tutoriels, prestations d'atelier et créneaux pour réparer un équipement diagnostiqué.",
    instruction=INSTRUCTION,
    tools=outils_catalogue(OUTILS_REPARATION),  # MCPToolset si MCP_CATALOG_URL est défini, sinon fonctions locales
    output_schema=PropositionReparation,  # structure imposée à la réponse finale, après les appels d'outils
    output_key="proposition_reparation",
    generate_content_config=generation_config(temperature=0.0),
)
