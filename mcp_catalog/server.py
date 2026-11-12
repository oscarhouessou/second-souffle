"""Serveur MCP du catalogue fictif (F17), en lecture seule.

    uv run uvicorn mcp_catalog.server:app --port 8105      # point d'accès : http://localhost:8105/mcp

Il expose les fonctions de shared/outils.py comme outils MCP. Tout client MCP peut s'y brancher
(agents ADK via MCPToolset, mais aussi un autre framework) : c'est ce qui rend l'architecture
transposable, il suffit de remplacer ce serveur pour brancher d'autres données (section 12).
"""

from mcp.server.mcpserver import MCPServer

from shared import outils
from shared.telemetrie import activer_tracage

serveur = MCPServer(
    name="second-souffle-catalogue",
    instructions="Catalogue fictif de Second Souffle : pièces, ateliers, barème de rachat, location, occasion. Lecture seule.",
)

for fonction in [*outils.OUTILS_REPARATION, *outils.OUTILS_VALORISATION]:
    serveur.tool()(fonction)

# Sans état : chaque requête est indépendante, ce qui permet plusieurs instances derrière Cloud Run.
app = serveur.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")
activer_tracage(app)
