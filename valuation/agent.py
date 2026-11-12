"""Agent Valorisation : offre de rachat, location et occasion (F09 à F11)."""

from google.adk.agents import LlmAgent

from shared.config import generation_config, model_for
from shared.outils import OUTILS_VALORISATION
from shared.outils_mcp import outils_catalogue
from shared.schemas import PropositionValorisation
from valuation.prompt import INSTRUCTION

root_agent = LlmAgent(
    name="valorisation",
    model=model_for("valuation"),
    description="Calcule l'offre de rachat indicative et cherche location et occasion pour un équipement diagnostiqué.",
    instruction=INSTRUCTION,
    tools=outils_catalogue(OUTILS_VALORISATION),  # MCPToolset si MCP_CATALOG_URL est défini, sinon fonctions locales
    output_schema=PropositionValorisation,
    output_key="proposition_valorisation",
    generate_content_config=generation_config(temperature=0.0),
)
