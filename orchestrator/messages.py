"""Messages déterministes : quand une règle décide, le texte n'a pas besoin d'un LLM.

Plus rapides, gratuits et toujours conformes ; le LLM est réservé à la présentation des options.
"""

from shared.config import MENTION_IA
from shared.schemas import Recommandation

REFUS_HORS_PERIMETRE = (
    "Je ne peux vous aider que pour donner une seconde vie à un équipement de vélo, de camping ou de "
    "randonnée : le réparer, le revendre, le louer ou en racheter un d'occasion. "
    "Quel équipement souhaitez-vous faire diagnostiquer ?"
)

QUESTION_PAR_DEFAUT = "Pouvez-vous me dire de quel équipement il s'agit et quel est le problème ?"


def questions(qs: list[str]) -> str:
    if len(qs) == 1:
        return f"Pour bien vous conseiller, j'ai besoin d'une précision : {qs[0]}"
    return "Pour bien vous conseiller, j'ai besoin de deux précisions :\n" + "\n".join(f"- {q}" for q in qs)


def escalade(reference: str, motifs: list[str]) -> str:
    return (
        f"Je transmets votre demande à un conseiller ({', '.join(motifs)}). "
        f"Votre numéro de dossier est {reference} : un membre de l'équipe reprendra la conversation "
        "avec le résumé de votre situation, vous n'aurez pas à tout réexpliquer."
    )


def budget_atteint() -> str:
    return (
        "Cette conversation a atteint sa limite de longueur. Pour continuer, ouvrez une nouvelle "
        "conversation ou demandez à parler à un conseiller."
    )


def presentation_de_secours(reco: Recommandation, resume: str) -> str:
    """Utilisée si le rédacteur échoue ou si le juge refuse deux fois : toujours conforme."""
    lignes = [f"Voici ce que je retiens : {resume}", "", "Vos options :"]
    for i, o in enumerate(reco.options):
        morceaux = [o.detail]
        if o.delai_jours:
            morceaux.append(f"délai {o.delai_jours} jour{'s' if o.delai_jours > 1 else ''}")
        if o.co2_evite_kg:
            morceaux.append(f"{o.co2_evite_kg:g} kg de CO₂ évités")
        etiquette = " (recommandée)" if i == 0 else ""
        lignes.append(f"- {o.titre}{etiquette} : {', '.join(morceaux)}")
    lignes += ["", reco.raison, *reco.mentions_obligatoires, "", "Quelle option choisissez-vous ?"]
    return "\n".join(lignes)


def avec_mention_ia(texte: str) -> str:
    return f"_{MENTION_IA}_\n\n{texte}"
