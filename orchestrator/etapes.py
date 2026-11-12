"""Étapes de l'orchestrateur : appel d'un agent spécialiste et décision par les règles.

Contrat d'un spécialiste (identique en local et en A2A) : un message en entrée (JSON et, pour le
diagnostic, photos), un texte JSON en sortie, validé ici par le schéma Pydantic attendu.
L'état de session ne traverse pas une frontière A2A : c'est l'orchestrateur qui lit l'état pour
construire le message, puis range la réponse validée dans l'état.
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.events import Event, EventActions
from google.genai import types
from pydantic import BaseModel, ConfigDict

from shared import regles, usage
from shared.config import TIMEOUT_APPEL_S
from shared.execution import ResultatAgent, executer_agent
from shared.schemas import FicheDiagnostic

log = logging.getLogger("second_souffle")

ConstruireEntree = Callable[[dict, Any], list[types.Part]]


class AppelSpecialiste(BaseModel):
    """Comment joindre un spécialiste : agent local (même processus) ou URL de carte A2A."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    agent_local: BaseAgent | None = None
    url_carte_a2a: str | None = None

    async def appeler(self, parts: list[types.Part]) -> ResultatAgent:
        if self.url_carte_a2a:
            from orchestrator.a2a_client import appeler_a2a  # lot 4

            return await appeler_a2a(self.url_carte_a2a, parts)
        return await executer_agent(self.agent_local, parts)


class EtapeSpecialiste(BaseAgent):
    """Appelle un spécialiste, valide sa réponse et la range dans l'état sous `cle_sortie`."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    appel: AppelSpecialiste
    construire_entree: ConstruireEntree
    cle_sortie: str
    schema_sortie: type[BaseModel]
    sortir_de_boucle_si: Callable[[BaseModel], bool] | None = None

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        parts = self.construire_entree(dict(ctx.session.state), ctx)
        try:
            # NF03 : délai maximal par appel, puis on continue sans ce spécialiste
            resultat = await asyncio.wait_for(self.appel.appeler(parts), timeout=TIMEOUT_APPEL_S)
            valeur = self.schema_sortie.model_validate_json(_json_seul(resultat.texte))
        except Exception as e:  # timeout, réponse invalide, service injoignable
            log.warning("étape %s en échec : %s", self.name, e)
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                actions=EventActions(state_delta={self.cle_sortie: None, f"erreur_{self.name}": str(e)[:300]}),
            )
            return

        etat_usage = usage.ajouter(ctx.session.state.get("usage"), self.name, resultat.tokens_entree, resultat.tokens_sortie)
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            # Pas de contenu texte : rien ne s'affiche dans le chat, tout est visible dans l'onglet Events.
            custom_metadata={
                "latence_s": round(resultat.latence_s, 2),
                "appels_outils": resultat.appels_outils,
                "tokens": [resultat.tokens_entree, resultat.tokens_sortie],
            },
            actions=EventActions(
                state_delta={self.cle_sortie: valeur.model_dump(mode="json"), "usage": etat_usage},
                escalate=bool(self.sortir_de_boucle_si and self.sortir_de_boucle_si(valeur)),
            ),
        )


def _json_seul(texte: str) -> str:
    """Retire d'éventuelles balises ```json autour de la réponse."""
    texte = texte.strip()
    if texte.startswith("```"):
        texte = texte.split("\n", 1)[1].rsplit("```", 1)[0]
    return texte


def entree_fiche(etat: dict, _ctx) -> list[types.Part]:
    """Entrée des agents Réparation et Valorisation : la fiche de diagnostic, en JSON."""
    return [types.Part(text=json.dumps({"fiche": etat["fiche"]}, ensure_ascii=False))]


class Decision(BaseAgent):
    """Applique les règles R01 à R05 aux propositions : options chiffrées et option recommandée."""

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        etat = ctx.session.state
        fiche = FicheDiagnostic.model_validate(etat["fiche"])
        reco = regles.decider(fiche, etat.get("proposition_reparation"), etat.get("proposition_valorisation"))
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            actions=EventActions(state_delta={"recommandation": reco.model_dump(mode="json"), "verdict": None}),
        )
