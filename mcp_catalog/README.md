# mcp_catalog

Serveur MCP en lecture seule (F17) : pièces, prestations, ateliers, barème de rachat, location, occasion.
Il expose les fonctions de `shared/outils.py` en transport *streamable HTTP*, sans état.

```bash
uv run uvicorn mcp_catalog.server:app --port 8105    # http://localhost:8105/mcp
```

Les agents Réparation et Valorisation s'y branchent avec `McpToolset` quand `MCP_CATALOG_URL` est
défini (chacun ne voit que ses outils, via `tool_filter`). Sans cette variable, ils appellent les
mêmes fonctions en local, ce qui garde les tests simples.

Pour transposer l'architecture à une autre équipe, on remplace ce serveur (par exemple par un
serveur MCP devant un outil RH ou les stocks) : les agents et l'orchestrateur ne changent pas.
