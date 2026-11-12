"""Orchestrateur de Second Souffle : point d'entrée unique du client.

À chaque message, il route selon la phase de la conversation (état de session) :

  diagnostic ─► agent Diagnostic ─┬─ hors périmètre ............ refus poli (F18)
                                  ├─ motif d'escalade (R06) .... ticket (F15)
                                  ├─ information manquante ..... ≤ 2 questions (F05)
                                  └─ fiche complète ............ pipeline de conseil ─► phase « choix »

  pipeline de conseil = SequentialAgent [
      ParallelAgent [Réparation, Valorisation],      propositions avec outils (F06 à F11)
      Décision,                                      règles R01 à R05 en Python (F13)
      LoopAgent(max 2) [Rédacteur, Juge],            message relu par le juge (R08, NF05)
  ]

  choix / termine ─► Conseiller (LlmAgent + actions simulées, garde-fou R07)

Les spécialistes sont appelés par un message JSON : en local dans le même processus, au lot 4 par A2A
si leurs URL de carte sont définies (DIAGNOSTIC_AGENT_CARD_URL, etc.).
"""

import json
import logging
import os
import random
import string
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.events import Event, EventActions
from google.genai import types

from diagnostic.agent import root_agent as agent_diagnostic
from judge.agent import root_agent as agent_juge
from orchestrator import messages
from orchestrator.actions import OUTILS_CONSEILLER, garde_confirmation
from orchestrator.etapes import AppelSpecialiste, Decision, EtapeSpecialiste, entree_fiche
from orchestrator.prompts import instruction_conseiller, instruction_redacteur
from repair.agent import root_agent as agent_reparation
from shared import regles, usage
from shared.config import MAX_QUESTIONS, SEUIL_CONFIANCE, generation_config, model_for
from shared.schemas import FicheDiagnostic, PropositionReparation, PropositionValorisation, Recommandation, VerdictJuge
from valuation.agent import root_agent as agent_valorisation

log = logging.getLogger("second_souffle")


def _appel(agent: BaseAgent, variable_url: str) -> AppelSpecialiste:
    url = os.getenv(variable_url)
    return AppelSpecialiste(url_carte_a2a=url) if url else AppelSpecialiste(agent_local=agent)


# --------------------------------------------------------------------------------------------
# Entrées des spécialistes
# --------------------------------------------------------------------------------------------
def entree_diagnostic(etat: dict, ctx) -> list[types.Part]:
    """La conversation du client (texte et photos) et la fiche précédente, s'il y en a une."""
    lignes: list[str] = []
    images: list[types.Part] = []
    for ev in ctx.session.events:
        if not ev.content or not ev.content.parts:
            continue
        if ev.author == "user":
            lignes.append("Client : " + " ".join(p.text for p in ev.content.parts if p.text))
            images += [p for p in ev.content.parts if p.inline_data or p.file_data]
        elif ev.author == ctx.agent.name:
            lignes.append("Assistant : " + " ".join(p.text for p in ev.content.parts if p.text))
    texte = "Conversation avec le client :\n" + "\n".join(lignes)
    if etat.get("fiche"):
        texte += "\n\nFiche précédente (à mettre à jour) :\n" + json.dumps(etat["fiche"], ensure_ascii=False)
    return [types.Part(text=texte), *images]


def entree_juge(etat: dict, _ctx) -> list[types.Part]:
    contenu = {
        "message": etat.get("message_client") or "",
        "recommandation": etat.get("recommandation"),
        "sources": [etat.get("proposition_reparation"), etat.get("fiche")],
    }
    return [types.Part(text=json.dumps(contenu, ensure_ascii=False))]


# --------------------------------------------------------------------------------------------
# Construction du graphe d'agents
# --------------------------------------------------------------------------------------------
etape_diagnostic = EtapeSpecialiste(
    name="etape_diagnostic", appel=_appel(agent_diagnostic, "DIAGNOSTIC_AGENT_CARD_URL"),
    construire_entree=entree_diagnostic, cle_sortie="fiche", schema_sortie=FicheDiagnostic,
)

propositions = ParallelAgent(
    name="propositions",
    sub_agents=[
        EtapeSpecialiste(
            name="etape_reparation", appel=_appel(agent_reparation, "REPAIR_AGENT_CARD_URL"),
            construire_entree=entree_fiche, cle_sortie="proposition_reparation", schema_sortie=PropositionReparation,
        ),
        EtapeSpecialiste(
            name="etape_valorisation", appel=_appel(agent_valorisation, "VALUATION_AGENT_CARD_URL"),
            construire_entree=entree_fiche, cle_sortie="proposition_valorisation", schema_sortie=PropositionValorisation,
        ),
    ],
)

redacteur = LlmAgent(
    name="redacteur",
    model=model_for("redacteur"),
    instruction=instruction_redacteur,
    include_contents="none",  # tout le contexte utile est dans l'instruction : moins de tokens
    output_key="message_client",
    generate_content_config=generation_config(temperature=0.3),
    after_model_callback=usage.compter_usage_callback,
)

boucle_redaction = LoopAgent(
    name="boucle_redaction",
    max_iterations=2,  # NF05
    sub_agents=[
        redacteur,
        EtapeSpecialiste(
            name="etape_juge", appel=_appel(agent_juge, "JUDGE_AGENT_CARD_URL"),
            construire_entree=entree_juge, cle_sortie="verdict", schema_sortie=VerdictJuge,
            sortir_de_boucle_si=lambda v: v.accepte,
        ),
    ],
)

pipeline_conseil = SequentialAgent(
    name="pipeline_conseil",
    sub_agents=[propositions, Decision(name="decision"), boucle_redaction],
)

conseiller = LlmAgent(
    name="conseiller",
    model=model_for("conseiller"),
    instruction=instruction_conseiller,
    tools=OUTILS_CONSEILLER,
    before_tool_callback=garde_confirmation,  # R07
    after_model_callback=usage.compter_usage_callback,
    generate_content_config=generation_config(temperature=0.2),
)


# --------------------------------------------------------------------------------------------
# Orchestrateur
# --------------------------------------------------------------------------------------------
def _ticket() -> str:
    return "TCK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Orchestrateur(BaseAgent):
    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        etat = ctx.session.state
        phase = etat.get("phase") or "diagnostic"

        if usage.budget_depasse(etat.get("usage")):  # NF07
            yield self._message(ctx, messages.budget_atteint())
            return

        if phase in ("choix", "termine"):
            async for ev in conseiller.run_async(ctx):
                yield ev
            return

        if phase == "escalade":
            ref = (etat.get("tickets") or [{}])[-1].get("reference", "")
            yield self._message(ctx, f"Votre demande est entre les mains d'un conseiller (dossier {ref}). "
                                     "Il reprendra la conversation dès que possible.")
            return

        # --- Phase diagnostic ------------------------------------------------------------------
        async for ev in etape_diagnostic.run_async(ctx):
            yield ev
        if not etat.get("fiche"):
            yield self._message(ctx, "Je n'ai pas réussi à analyser votre demande. Pouvez-vous la reformuler ?")
            return
        fiche = FicheDiagnostic.model_validate(etat["fiche"])
        posees = etat.get("questions_posees", 0)
        sans_progres = etat.get("echanges_sans_progres", 0)

        if fiche.hors_perimetre:
            yield self._message(ctx, messages.REFUS_HORS_PERIMETRE, {"echanges_sans_progres": sans_progres + 1})
            return

        motifs = regles.motifs_escalade(fiche, posees, sans_progres)
        complete = fiche.categorie and fiche.etat and fiche.confiance >= SEUIL_CONFIANCE
        if not complete and posees >= MAX_QUESTIONS and not motifs:
            motifs = ["diagnostic incertain après deux questions"]
        if motifs:
            ref = _ticket()
            ticket = {"type": "escalade", "reference": ref, "motif": ", ".join(motifs), "resume": fiche.resume}
            yield self._message(ctx, messages.escalade(ref, motifs),
                                {"phase": "escalade", "tickets": [*etat.get("tickets", []), ticket]})
            return

        if not complete:
            qs = (fiche.questions_restantes or [messages.QUESTION_PAR_DEFAUT])[: MAX_QUESTIONS - posees]
            yield self._message(ctx, messages.questions(qs),
                                {"questions_posees": posees + len(qs), "echanges_sans_progres": sans_progres + 1})
            return

        # --- Fiche complète : propositions, décision, rédaction relue par le juge --------------
        async for ev in pipeline_conseil.run_async(ctx):
            if ev.author == redacteur.name and ev.content:
                # Le brouillon n'est pas montré au client tant que le juge ne l'a pas accepté.
                ev = ev.model_copy(update={"content": None})
            yield ev

        reco = Recommandation.model_validate(etat["recommandation"])
        verdict = etat.get("verdict") or {}
        texte = etat.get("message_client") if verdict.get("accepte") else None
        if not texte:
            log.info("message de secours (verdict : %s)", verdict)
            texte = messages.presentation_de_secours(reco, fiche.resume)
        yield self._message(ctx, texte, {"phase": "choix", "echanges_sans_progres": 0})

    def _message(self, ctx, texte: str, state_delta: dict | None = None) -> Event:
        delta = dict(state_delta or {})
        if not ctx.session.state.get("mention_ia_faite"):  # transparence (AI Act)
            texte = messages.avec_mention_ia(texte)
            delta["mention_ia_faite"] = True
        return Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(role="model", parts=[types.Part(text=texte)]),
            actions=EventActions(state_delta=delta),
        )


root_agent = Orchestrateur(
    name="second_souffle",
    description="Assistant de seconde vie de l'équipement de sport : diagnostic, options chiffrées, action.",
    sub_agents=[etape_diagnostic, pipeline_conseil, conseiller],
)
