"""Appels authentifiés entre services Cloud Run (NF14).

Les agents et le serveur MCP sont déployés sans accès public : seul un appelant muni d'un jeton
d'identité Google, émis pour l'URL du service et signé pour un compte de service autorisé
(rôle run.invoker), peut les joindre. Sur Cloud Run, le jeton vient du serveur de métadonnées.
En local (AUTH_ID_TOKEN absent), aucun en-tête n'est ajouté.
"""

import os
import time
from urllib.parse import urlparse

_cache: dict[str, tuple[str, float]] = {}


def _audience(url: str) -> str:
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}"


def jeton_identite(url: str) -> str:
    audience = _audience(url)
    jeton, expire = _cache.get(audience, ("", 0.0))
    if time.time() < expire - 300:  # renouvelé 5 minutes avant l'expiration (1 heure)
        return jeton
    import google.auth.transport.requests
    import google.oauth2.id_token

    jeton = google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audience)
    _cache[audience] = (jeton, time.time() + 3600)
    return jeton


def entetes_auth(url: str) -> dict[str, str]:
    if os.getenv("AUTH_ID_TOKEN") != "1":
        return {}
    return {"Authorization": f"Bearer {jeton_identite(url)}"}
