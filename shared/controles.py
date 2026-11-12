"""Contrôles déterministes du juge (R01, R03, R08, ton).

Ils vérifient le message réellement envoyé au client, pas les données intermédiaires :
c'est la dernière barrière avant l'utilisateur.
"""

import json
import re

from shared.schemas import Recommandation, VerdictJuge

# Marques connues du secteur : le service de démo n'en cite aucune (section 2 du cahier des charges).
MARQUES_INTERDITES = [
    "decathlon", "quechua", "forclaz", "btwin", "b'twin", "rockrider", "riverside", "van rysel", "triban",
    "elops", "kalenji", "kiprun", "simond", "tribord", "domyos", "jamet", "shimano", "sram",
]

_UNITE = r"(?P<unite>€|euros?|jours?|kg)"
_MONTANT = re.compile(r"(?P<nombre>\d+(?:[.,]\d{1,2})?)\s*" + _UNITE, re.IGNORECASE)
_NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")

MOTS_OPTION = {
    "reparer": r"répar",
    "revendre": r"revend|revente|rachat|racheter",
    "louer": r"lou(er|ez|ation)",
    "occasion": r"occasion",
    "recycler": r"recycl",
}

MAX_MOTS = 220


def _nombre(texte: str) -> float:
    return float(texte.replace(",", "."))


def nombres_autorises(*sources) -> set[float]:
    """Tous les nombres présents dans les sources (recommandation, propositions…), en JSON."""
    texte = " ".join(json.dumps(s, ensure_ascii=False, default=str) for s in sources if s is not None)
    valeurs = {_nombre(n) for n in _NOMBRE.findall(texte)}
    # On accepte aussi l'arrondi à l'euro d'un montant (9,99 € → « 10 € » reste fidèle).
    return valeurs | {float(round(v)) for v in valeurs}


def montants_cites(message: str) -> list[tuple[float, str]]:
    return [(_nombre(m["nombre"]), m["unite"].lower()) for m in _MONTANT.finditer(message)]


def controler_message(message: str, reco: Recommandation, autres_sources: list | None = None) -> VerdictJuge:
    motifs: list[str] = []
    bas = message.lower()

    # R08 : aucun prix, délai ou poids qui ne vienne des données ou des règles
    autorises = nombres_autorises(reco.model_dump(), *(autres_sources or []))
    inventes = [f"{v:g} {u}" for v, u in montants_cites(message) if round(v, 2) not in autorises]
    if inventes:
        motifs.append(f"R08 : chiffres absents des sorties d'outils : {', '.join(inventes)}")

    # R03 : toute offre de rachat est présentée comme indicative
    if any(o.option == "revendre" for o in reco.options) and re.search(MOTS_OPTION["revendre"], bas):
        if "indicati" not in bas:
            motifs.append("R03 : l'offre de rachat doit être présentée comme indicative")

    # R01 : un produit de sécurité endommagé n'est ni revendu ni proposé d'occasion
    if "R01" in reco.regles_appliquees and _montant_de_rachat_present(message):
        motifs.append("R01 : aucune offre de rachat pour un produit de sécurité endommagé")

    # Option recommandée présente, aucune marque, longueur raisonnable
    if not re.search(MOTS_OPTION[reco.option_recommandee], bas):
        motifs.append(f"l'option recommandée ({reco.option_recommandee}) n'apparaît pas")
    marques = [m for m in MARQUES_INTERDITES if re.search(rf"\b{re.escape(m)}\b", bas)]
    if marques:
        motifs.append(f"marques citées : {', '.join(marques)}")
    if len(message.split()) > MAX_MOTS:
        motifs.append(f"message trop long ({len(message.split())} mots, {MAX_MOTS} au plus)")

    return VerdictJuge(accepte=not motifs, motifs=motifs)


def _montant_de_rachat_present(message: str) -> bool:
    for phrase in re.split(r"[.\n]", message.lower()):
        if re.search(MOTS_OPTION["revendre"], phrase) and "€" in phrase:
            return True
    return False
