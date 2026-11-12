"""Schémas Pydantic partagés par tous les services.

Définis une seule fois ici, ils servent à la fois :
- de format de sortie imposé aux LLM (`output_schema` d'ADK) ;
- de contrat des messages échangés entre services (A2A) ;
- de validation dans les règles métier et les tests.
"""

from typing import Literal

from pydantic import BaseModel, Field

from shared.vocabulaire import CATEGORIES, TYPES_DEFAUT

Famille = Literal["velo", "camping", "randonnee"]
Categorie = Literal[tuple(CATEGORIES)]  # type: ignore[valid-type]
TypeDefaut = Literal[tuple(TYPES_DEFAUT)]  # type: ignore[valid-type]
Etat = Literal["bon", "moyen", "use", "hors_usage"]
Gravite = Literal["faible", "moyenne", "forte"]
FrequenceUsage = Literal["reguliere", "occasionnelle", "ponctuelle", "inconnue"]
Gamme = Literal["entree", "milieu", "haut", "inconnue"]
Option = Literal["reparer", "revendre", "louer", "occasion", "recycler"]


# --------------------------------------------------------------------------------------------
# Diagnostic (F02 à F05)
# --------------------------------------------------------------------------------------------
class Defaut(BaseModel):
    type: TypeDefaut = Field(description="Code du défaut, pris dans le vocabulaire de la catégorie.")
    gravite: Gravite = Field(description="faible : cosmétique ; moyenne : gêne l'usage ; forte : empêche l'usage.")
    taille_cm: float | None = Field(default=None, ge=0, description="Taille du défaut si elle est connue.")


class FicheDiagnostic(BaseModel):
    """Sortie de l'agent Diagnostic."""

    hors_perimetre: bool = Field(
        default=False,
        description="Vrai si la demande ne concerne pas la seconde vie d'un équipement de vélo, camping ou randonnée.",
    )
    famille: Famille | None = Field(default=None, description="Famille du produit.")
    categorie: Categorie | None = Field(default=None, description="Catégorie du produit.")
    gamme: Gamme = Field(default="inconnue", description="Gamme de prix si le client l'indique ou si elle est évidente.")
    age_annees: float | None = Field(default=None, ge=0, le=50, description="Âge du produit en années.")
    etat: Etat | None = Field(default=None, description="État général : bon, moyen, use, hors_usage.")
    defauts: list[Defaut] = Field(default_factory=list, description="Défauts visibles ou décrits, le principal en premier.")
    frequence_usage: FrequenceUsage = Field(
        default="inconnue",
        description="ponctuelle : moins de 3 utilisations par an ; occasionnelle : quelques fois par an ; reguliere : souvent.",
    )
    souhait_client: str | None = Field(
        default=None, description="Ce que le client dit vouloir (ex. passer à un vélo électrique), en quelques mots."
    )
    veut_s_en_separer: bool = Field(
        default=False,
        description="Vrai si le client ne compte plus utiliser ce produit (trop petit, changement de pratique, achat d'un autre).",
    )
    code_postal: str | None = Field(
        default=None,
        pattern=r"^\d{5}$",
        description="Code postal, uniquement si le client l'a donné (sert à trouver un atelier).",
    )
    demande_humain: bool = Field(default=False, description="Vrai si le client demande à parler à un humain.")
    sous_garantie_ou_litige: bool = Field(
        default=False, description="Vrai si le client mentionne une garantie, un achat récent défectueux ou un litige."
    )
    confiance: float = Field(ge=0, le=1, description="Confiance globale dans cette fiche, de 0 à 1.")
    questions_restantes: list[str] = Field(
        default_factory=list,
        max_length=2,
        description="Au plus deux questions courtes, seulement si une information indispensable manque.",
    )
    resume: str = Field(description="Une phrase qui résume le produit et son problème, en français simple.")

    @property
    def defaut_principal(self) -> str | None:
        return self.defauts[0].type if self.defauts else None


# --------------------------------------------------------------------------------------------
# Propositions des agents Réparation et Valorisation (F06 à F12)
# --------------------------------------------------------------------------------------------
class PieceProposee(BaseModel):
    part_id: str
    nom: str
    prix_eur: float
    difficulte: Literal["facile", "moyen", "atelier"]
    tutoriel: str | None = None


class PropositionReparation(BaseModel):
    """Sortie de l'agent Réparation. Tous les chiffres viennent des outils."""

    reparable: bool = Field(description="Faux si aucune pièce ni prestation ne traite le défaut principal.")
    pieces: list[PieceProposee] = Field(default_factory=list, description="Pièces pour une réparation soi-même.")
    service_id: str | None = Field(default=None, description="Prestation d'atelier retenue, si elle existe.")
    cout_atelier_eur: float | None = Field(default=None, description="Prix de la prestation, copié de l'outil.")
    delai_atelier_jours: int | None = Field(default=None, description="Durée de la prestation, copiée de l'outil.")
    workshop_id: str | None = None
    creneau: str | None = Field(default=None, description="Premier créneau proposé, copié de l'outil (ISO 8601).")
    explication: str = Field(description="Deux phrases au plus, sans jargon.")


class PropositionValorisation(BaseModel):
    """Sortie de l'agent Valorisation. Tous les chiffres viennent des outils."""

    offre_rachat_eur: float | None = Field(default=None, description="Offre indicative calculée par l'outil.")
    rachat_autorise: bool = Field(default=True, description="Faux si la règle R01 interdit la revente.")
    location_product_id: str | None = None
    location_prix_jour_eur: float | None = None
    location_prix_semaine_eur: float | None = None
    occasion_item_id: str | None = None
    occasion_prix_eur: float | None = None
    occasion_etat: str | None = None
    explication: str = Field(description="Deux phrases au plus, sans jargon.")


# --------------------------------------------------------------------------------------------
# Décision (règles) et contrôle du juge
# --------------------------------------------------------------------------------------------
class OptionChiffree(BaseModel):
    option: Option
    titre: str
    cout_client_eur: float | None = None  # ce que le client paie
    gain_client_eur: float | None = None  # ce que le client récupère
    delai_jours: int | None = None
    co2_evite_kg: float | None = None
    detail: str


class Recommandation(BaseModel):
    options: list[OptionChiffree]
    option_recommandee: Option
    raison: str
    regles_appliquees: list[str]
    mentions_obligatoires: list[str] = Field(default_factory=list)


class VerdictJuge(BaseModel):
    accepte: bool
    motifs: list[str] = Field(default_factory=list)
