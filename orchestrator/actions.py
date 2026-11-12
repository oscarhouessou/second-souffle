"""Actions simulées du conseiller (F08, F14, F15) et garde-fou R07.

Les actions n'appellent aucun système réel : elles calculent tout depuis les données fictives,
enregistrent l'action dans l'état de session et renvoient une référence.
"""

import random
import re
import string
from datetime import datetime, timedelta

from google.adk.tools import ToolContext

from shared import data, outils, regles
from shared.config import MENTION_RACHAT
from shared.schemas import FicheDiagnostic


def _reference(prefixe: str) -> str:
    return f"{prefixe}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"


def _enregistrer(tool_context: ToolContext, action: dict) -> dict:
    tool_context.state["actions"] = [*tool_context.state.get("actions", []), action]
    tool_context.state["phase"] = "termine"
    return action


def _fiche(tool_context: ToolContext) -> FicheDiagnostic | None:
    f = tool_context.state.get("fiche")
    return FicheDiagnostic.model_validate(f) if f else None


def reserver_atelier(code_postal: str, tool_context: ToolContext, creneau: str = "") -> dict:
    """Réserve une réparation dans l'atelier le plus proche. À n'appeler qu'après confirmation explicite.

    Args:
        code_postal: code postal du client (5 chiffres).
        creneau: créneau choisi au format ISO 8601 ; vide pour le premier disponible.
    """
    fiche = _fiche(tool_context)
    if not fiche or not fiche.defaut_principal:
        return {"erreur": "aucun défaut diagnostiqué à réparer"}
    presta = outils.chercher_prestation_atelier(fiche.categorie, fiche.defaut_principal).get("prestation")
    if not presta:
        return {"erreur": "aucune prestation d'atelier pour ce défaut"}
    atelier = outils.trouver_atelier(code_postal)
    if "erreur" in atelier:
        return atelier
    choisi = creneau if creneau in atelier["creneaux"] else atelier["creneaux"][0]
    fin = datetime.fromisoformat(choisi) + timedelta(days=presta["duree_jours"])
    return _enregistrer(tool_context, {
        "type": "reservation_atelier", "reference": _reference("ATL"), "atelier": atelier["nom"],
        "creneau_depot": choisi, "prix_eur": presta["prix_eur"], "duree_jours": presta["duree_jours"],
        "retrait_estime": fin.date().isoformat(),
    })


def reserver_pieces(tool_context: ToolContext) -> dict:
    """Réserve en retrait les pièces de la réparation soi-même, avec leurs tutoriels. Après confirmation explicite."""
    # Même sélection que la décision : le prix réservé est celui qui a été annoncé.
    pieces = regles.pieces_retenues(tool_context.state.get("proposition_reparation"))
    if not pieces:
        return {"erreur": "aucune pièce à réserver"}
    return _enregistrer(tool_context, {
        "type": "reservation_pieces", "reference": _reference("PCE"),
        "pieces": [{"nom": p.nom, "prix_eur": p.prix_eur, "tutoriel": p.tutoriel} for p in pieces],
        "total_eur": round(sum(p.prix_eur for p in pieces), 2),
    })


def demander_rachat(tool_context: ToolContext) -> dict:
    """Enregistre la demande de rachat au montant indicatif calculé par le barème. Après confirmation explicite."""
    fiche = _fiche(tool_context)
    if not fiche or not fiche.categorie or not fiche.etat:
        return {"erreur": "diagnostic incomplet"}
    if regles.revente_interdite(fiche) or regles.est_securite(fiche.categorie):
        return {"erreur": "R01 : ce produit de sécurité ne peut pas être racheté"}
    offre = regles.calculer_offre_rachat(fiche.categorie, fiche.etat, fiche.age_annees, fiche.gamme)
    if not offre.autorisee:
        return {"erreur": offre.detail}
    return _enregistrer(tool_context, {
        "type": "demande_rachat", "reference": _reference("RCH"), "montant_indicatif_eur": offre.montant_eur,
        "mention": MENTION_RACHAT,
    })


def reserver_location(date_debut: str, nombre_jours: int, tool_context: ToolContext) -> dict:
    """Réserve la location proposée. Après confirmation explicite.

    Args:
        date_debut: date de début AAAA-MM-JJ.
        nombre_jours: durée de la location en jours (1 à 21).
    """
    val = tool_context.state.get("proposition_valorisation") or {}
    offre = next((o for o in data.location() if o.product_id == val.get("location_product_id")), None)
    if not offre:
        return {"erreur": "aucune offre de location proposée"}
    if not 1 <= nombre_jours <= 21:
        return {"erreur": "durée de location entre 1 et 21 jours"}
    semaines, jours = divmod(nombre_jours, 7)
    prix = semaines * offre.prix_semaine_eur + min(jours * offre.prix_jour_eur, offre.prix_semaine_eur)
    return _enregistrer(tool_context, {
        "type": "reservation_location", "reference": _reference("LOC"),
        "produit": data.produit(offre.product_id).nom, "date_debut": date_debut, "nombre_jours": nombre_jours,
        "prix_eur": prix, "caution_eur": offre.caution_eur,
    })


def reserver_occasion(tool_context: ToolContext) -> dict:
    """Réserve l'article d'occasion proposé pendant 48 heures. Après confirmation explicite."""
    val = tool_context.state.get("proposition_valorisation") or {}
    article = next((o for o in data.occasion() if o.item_id == val.get("occasion_item_id")), None)
    if not article:
        return {"erreur": "aucun article d'occasion proposé"}
    return _enregistrer(tool_context, {
        "type": "reservation_occasion", "reference": _reference("OCC"),
        "produit": data.produit(article.product_id).nom, "etat": article.etat_controle,
        "prix_eur": article.prix_eur, "valable_jusqu_au": (datetime.now() + timedelta(hours=48)).isoformat(timespec="minutes"),
    })


def escalader_vers_humain(motif: str, tool_context: ToolContext) -> dict:
    """Transmet la conversation à un conseiller humain avec un résumé (F15, R06).

    Args:
        motif: raison de l'escalade, en quelques mots.
    """
    fiche = tool_context.state.get("fiche") or {}
    ticket = {
        "type": "escalade", "reference": _reference("TCK"), "motif": motif,
        "resume": fiche.get("resume"), "recommandation": (tool_context.state.get("recommandation") or {}).get("option_recommandee"),
    }
    tool_context.state["tickets"] = [*tool_context.state.get("tickets", []), ticket]
    tool_context.state["phase"] = "escalade"
    return ticket


def nouveau_produit(tool_context: ToolContext) -> dict:
    """Recommence un diagnostic pour un autre produit (la conversation continue)."""
    for cle in ("fiche", "recommandation", "proposition_reparation", "proposition_valorisation", "verdict", "message_client"):
        tool_context.state[cle] = None
    tool_context.state["phase"] = "diagnostic"
    tool_context.state["questions_posees"] = 0
    return {"ok": True}


OUTILS_CONSEILLER = [
    reserver_atelier, reserver_pieces, demander_rachat, reserver_location, reserver_occasion,
    escalader_vers_humain, nouveau_produit,
]
ACTIONS_A_CONFIRMER = {"reserver_atelier", "reserver_pieces", "demander_rachat", "reserver_location", "reserver_occasion"}

_CONFIRMATION = re.compile(
    r"\b(oui|ouais|ok|okay|d'accord|daccord|je confirme|confirm[eé]|valid[eé]|vas-?y|allez-?y|go|"
    r"c'est bon|c'est parti|parfait|je veux bien|réserve[sz]?|reserve[sz]?|on y va)\b",
    re.IGNORECASE,
)


def est_confirmation(texte: str) -> bool:
    return bool(_CONFIRMATION.search(texte or "")) and not re.search(r"\b(non|pas encore|attends?)\b", texte or "", re.I)


def valider_arguments(tool, args, tool_context: ToolContext):
    """before_tool_callback (NF11) : arguments vérifiés avant tout appel d'outil."""
    if "code_postal" in args and not re.fullmatch(r"\d{5}", str(args["code_postal"])):
        return {"erreur": "code postal invalide : demande au client ses 5 chiffres"}
    if "date_debut" in args:
        try:
            if datetime.fromisoformat(str(args["date_debut"])).date() < datetime.now().date():
                return {"erreur": "la date de début est passée"}
        except ValueError:
            return {"erreur": "date invalide, format attendu AAAA-MM-JJ"}
    return None


def garde_confirmation(tool, args, tool_context: ToolContext):
    """before_tool_callback (R07) : aucune action sans confirmation explicite dans le dernier message du client."""
    if tool.name not in ACTIONS_A_CONFIRMER:
        return None
    contenu = tool_context.user_content
    texte = " ".join(p.text or "" for p in (contenu.parts if contenu else []))
    if est_confirmation(texte):
        return None
    return {"erreur": "R07 : action non effectuée. Décris l'action au client et demande-lui de confirmer explicitement."}
