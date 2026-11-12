"""Comptage des tokens et du coût par session (NF06, NF07)."""

from shared.config import BUDGET_TOKENS_SESSION, PRIX_TOKENS_EUR


def ajouter(usage: dict | None, agent: str, entree: int, sortie: int) -> dict:
    """Renvoie une copie de `usage` augmentée des tokens d'un appel."""
    usage = {k: (dict(v) if isinstance(v, dict) else v) for k, v in (usage or {}).items()}
    par_agent = usage.setdefault("par_agent", {})
    a = par_agent.setdefault(agent, {"entree": 0, "sortie": 0, "appels": 0})
    a["entree"] += entree
    a["sortie"] += sortie
    a["appels"] += 1
    usage["tokens_entree"] = usage.get("tokens_entree", 0) + entree
    usage["tokens_sortie"] = usage.get("tokens_sortie", 0) + sortie
    prix_in, prix_out = PRIX_TOKENS_EUR["default"]
    usage["cout_eur"] = round(
        (usage["tokens_entree"] * prix_in + usage["tokens_sortie"] * prix_out) / 1_000_000, 5
    )
    return usage


def budget_depasse(usage: dict | None) -> bool:
    usage = usage or {}
    return usage.get("tokens_entree", 0) + usage.get("tokens_sortie", 0) > BUDGET_TOKENS_SESSION


def compter_usage_callback(callback_context, llm_response):
    """after_model_callback ADK : ajoute les tokens d'un appel LLM à l'état `usage` de la session."""
    meta = llm_response.usage_metadata
    if meta and not llm_response.partial:
        callback_context.state["usage"] = ajouter(
            callback_context.state.get("usage"),
            callback_context.agent_name,
            meta.prompt_token_count or 0,
            (meta.candidates_token_count or 0) + (meta.thoughts_token_count or 0),
        )
    return None
