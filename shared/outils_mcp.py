"""Choix de la source des outils : serveur MCP si MCP_CATALOG_URL est défini, sinon fonctions locales."""

import os

from shared.config import TIMEOUT_APPEL_S


def outils_catalogue(fonctions: list) -> list:
    url = os.getenv("MCP_CATALOG_URL")
    if not url:
        return list(fonctions)

    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

    from shared.auth_gcp import entetes_auth

    return [
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=url, timeout=TIMEOUT_APPEL_S),
            tool_filter=[f.__name__ for f in fonctions],  # chaque agent ne voit que ses outils
            header_provider=lambda _ctx: entetes_auth(url),  # jeton d'identité sur Cloud Run (NF14)
        )
    ]
