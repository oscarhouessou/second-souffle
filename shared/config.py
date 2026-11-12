"""Paramètres de démonstration (section 5 du cahier des charges).

Tous les seuils sont des hypothèses de démo : ils se règlent ici ou par variable d'environnement,
jamais dans un prompt.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
# Les variables déjà définies (shell, Cloud Run) gardent la priorité sur le fichier.
load_dotenv(ROOT_DIR / ".env", override=False)
DATA_DIR = Path(os.getenv("SECOND_SOUFFLE_DATA_DIR", ROOT_DIR / "data"))

# --- Modèles (NF08 : modèle rapide par défaut, réglable par rôle) -------------------------------
DEFAULT_MODEL = os.getenv("SECOND_SOUFFLE_MODEL", "gemini-3.6-flash")


def model_name_for(role: str) -> str:
    """Nom du modèle d'un rôle : SECOND_SOUFFLE_MODEL_<ROLE> s'il existe, sinon le modèle par défaut."""
    return os.getenv(f"SECOND_SOUFFLE_MODEL_{role.upper()}", DEFAULT_MODEL)


def model_name_secours(role: str) -> str:
    """Modèle de repli d'un rôle : l'autre modèle de la paire Flash / Flash-Lite (quota distinct)."""
    principal = model_name_for(role)
    return os.getenv("SECOND_SOUFFLE_MODEL_SECOURS",
                     "gemini-3.6-flash" if "lite" in principal else "gemini-3.5-flash-lite")


def model_for(role: str, secours: bool = False):
    """Modèle Gemini d'un rôle, avec nouvelles tentatives sur erreur transitoire (NF04).

    429 (quota) et 503 (surcharge) : 2 nouvelles tentatives au plus, délai exponentiel 1 s puis 2 s,
    avec un peu d'aléa pour que des appels parallèles ne réessaient pas tous au même instant.
    """
    from google.adk.models import Gemini
    from google.genai import types

    return Gemini(
        model=model_name_secours(role) if secours else model_name_for(role),
        retry_options=types.HttpRetryOptions(
            attempts=3, initial_delay=1.0, max_delay=8.0, exp_base=2.0, jitter=0.5, http_status_codes=[429, 503]
        ),
    )


# Mesuré le 2026-11-12 sur le diagnostic (4 cas) : niveau "minimal" = 2,2 s en moyenne, 4/4 justes ;
# réflexion par défaut = 5 s en moyenne. Réglable par SECOND_SOUFFLE_THINKING (minimal, low, high).
THINKING_LEVEL = os.getenv("SECOND_SOUFFLE_THINKING", "minimal")


def generation_config(temperature: float = 0.1):
    """Configuration de génération commune : température basse et réflexion minimale (NF01, NF06)."""
    from google.genai import types

    return types.GenerateContentConfig(
        temperature=temperature,
        thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
    )


# --- Diagnostic (F04, F05, R06) ---------------------------------------------------------------
SEUIL_CONFIANCE = float(os.getenv("SEUIL_CONFIANCE", "0.7"))
MAX_QUESTIONS = 2  # F05 : au plus deux questions de précision au total

# --- Règles métier ----------------------------------------------------------------------------
# R01 : produits de sécurité, jamais revendus ni proposés d'occasion une fois endommagés.
CATEGORIES_SECURITE = frozenset(
    {"casque_velo", "siege_velo_enfant", "baudrier", "gilet_sauvetage"}
)
# R04 : réparer si coût < 50 % du prix d'un équivalent d'occasion.
RATIO_REPARATION_OCCASION = float(os.getenv("RATIO_REPARATION_OCCASION", "0.5"))
# R05 : location proposée si moins de 3 utilisations par an.
SEUIL_USAGE_PONCTUEL = 3
# R06 : escalade après 3 échanges sans progrès.
MAX_ECHANGES_SANS_PROGRES = 3

# --- Coûts et fiabilité (NF03, NF04, NF05, NF07) ----------------------------------------------
TIMEOUT_APPEL_S = float(os.getenv("TIMEOUT_APPEL_S", "20"))
MAX_TOURS_JUGE = 2
BUDGET_TOKENS_SESSION = int(os.getenv("BUDGET_TOKENS_SESSION", "60000"))

# Prix Vertex AI indicatifs en € par million de tokens (entrée, sortie) ; à ajuster.
PRIX_TOKENS_EUR = {
    "default": (0.28, 2.30),
}

MENTION_RACHAT = (
    "Cette offre de rachat est indicative : elle sera confirmée après contrôle du produit en magasin."
)
MENTION_IA = "Vous échangez avec un assistant IA de démonstration (données fictives)."
