"""Modèle Company — structure cliente ou prestataire sur Avyro."""
from app.extensions import db
from .mixins import TimestampMixin


class Company(TimestampMixin, db.Model):
    """
    Représente une entreprise (kind='pro') ou un particulier (kind='private').
    Chaque Company est créée à l'inscription avec un premier User admin.
    Elle peut proposer des formations/salles ET en réserver chez d'autres.
    """

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # "pro" = entreprise, "private" = particulier
    kind = db.Column(db.String(20), nullable=False, default="pro")
    # Numéro SIRET (France) — optionnel pour les particuliers
    siret = db.Column(db.String(20), unique=True, nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)

    # Un seul admin par Company (le fondateur) ; plusieurs membres possibles
    users = db.relationship("User", back_populates="company")
    trainings = db.relationship(
        "Training", back_populates="provider", cascade="all, delete-orphan"
    )
    rooms = db.relationship(
        "Room", back_populates="provider", cascade="all, delete-orphan"
    )
    # Réservations effectuées par cette Company
    bookings = db.relationship(
        "Booking", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r} kind={self.kind!r}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "siret": self.siret,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat(),
        }
