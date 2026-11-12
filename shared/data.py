"""Accès en lecture seule aux données fictives de data/.

Chaque fichier est lu une seule fois (cache) et validé par un modèle Pydantic :
une donnée mal formée casse au chargement, pas au milieu d'une conversation.
"""

import json
from datetime import datetime, time, timedelta
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel

from shared.config import DATA_DIR


class Produit(BaseModel):
    product_id: str
    nom: str
    famille: str
    categorie: str
    gamme: Literal["entree", "milieu", "haut"]
    prix_neuf_eur: float
    est_securite: bool
    co2_kg: float


class Piece(BaseModel):
    part_id: str
    nom: str
    categories: list[str]
    defaut: str
    prix_eur: float
    difficulte: Literal["facile", "moyen", "atelier"]
    tutoriel: str


class Prestation(BaseModel):
    service_id: str
    categories: list[str]
    defaut: str
    prix_eur: float
    duree_jours: int


class Atelier(BaseModel):
    workshop_id: str
    nom: str
    ville: str
    code_postal: str
    jours_ouverture: list[int]
    horaires_creneaux: list[str]

    def prochains_creneaux(self, apres: datetime, nombre: int = 3) -> list[str]:
        """Créneaux calculés à partir d'un planning hebdomadaire : les données ne périment pas."""
        creneaux: list[str] = []
        jour = (apres + timedelta(days=1)).date()
        while len(creneaux) < nombre:
            if jour.isoweekday() in self.jours_ouverture:
                for h in self.horaires_creneaux:
                    heure, minute = map(int, h.split(":"))
                    creneaux.append(datetime.combine(jour, time(heure, minute)).isoformat(timespec="minutes"))
            jour += timedelta(days=1)
        return creneaux[:nombre]


class CoefAge(BaseModel):
    age_max_annees: float | None
    coef: float


class Bareme(BaseModel):
    coef_etat: dict[str, float]
    coef_age: list[CoefAge]
    plafond_par_categorie: dict[str, float]
    co2_evite_ratio: dict[str, float | str]


class OffreLocation(BaseModel):
    product_id: str
    prix_jour_eur: float
    prix_semaine_eur: float
    caution_eur: float


class ArticleOccasion(BaseModel):
    item_id: str
    product_id: str
    etat_controle: Literal["comme_neuf", "tres_bon", "bon"]
    prix_eur: float


def _lire(nom: str):
    return json.loads((DATA_DIR / nom).read_text(encoding="utf-8"))


@lru_cache
def catalogue() -> list[Produit]:
    return [Produit(**p) for p in _lire("catalogue.json")]


@lru_cache
def pieces() -> list[Piece]:
    return [Piece(**p) for p in _lire("pieces.json")]


@lru_cache
def prestations() -> list[Prestation]:
    return [Prestation(**p) for p in _lire("prestations.json")]


@lru_cache
def ateliers() -> list[Atelier]:
    return [Atelier(**a) for a in _lire("ateliers.json")]


@lru_cache
def bareme() -> Bareme:
    return Bareme(**_lire("bareme.json"))


@lru_cache
def location() -> list[OffreLocation]:
    return [OffreLocation(**o) for o in _lire("location.json")]


@lru_cache
def occasion() -> list[ArticleOccasion]:
    return [ArticleOccasion(**o) for o in _lire("occasion.json")]


def produit(product_id: str) -> Produit | None:
    return next((p for p in catalogue() if p.product_id == product_id), None)


def produits_de(categorie: str) -> list[Produit]:
    return [p for p in catalogue() if p.categorie == categorie]
