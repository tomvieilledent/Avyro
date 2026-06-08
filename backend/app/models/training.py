"""
Modèle Training — session de formation (kind='training') ou salle de réunion
mutualisée (kind='room').

Un seul modèle pour les deux types : même workflow (publication → réservation
→ confirmation). Le champ `kind` discrimine les deux modes de l'interface.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions import db
from .mixins import TimestampMixin


class Training(TimestampMixin, db.Model):
    """
    Offre publiée par une Company (provider) proposant des places à d'autres.

    Cycle de vie du statut :
        open → closed   (fermeture manuelle par le provider)
        open → cancelled (annulation)
    Les formations terminées (ends_at dépassé) sont purgées par la tâche
    de maintenance planifiée.

    shared_seats   = nombre de places proposées à la mutualisation
    available_seats = shared_seats − places confirmées (calculé à la volée)
    """

    __tablename__ = "trainings"

    id = db.Column(db.Integer, primary_key=True)
    # Discriminant de mode : "training" (Avyro bleu) | "room" (Avyro vert)
    kind = db.Column(
        db.String(20), nullable=False, default="training", index=True
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    is_remote = db.Column(db.Boolean, default=False, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)

    # Places proposées à la mutualisation
    shared_seats = db.Column(db.Integer, nullable=False, default=1)
    price_per_seat = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # "open" | "closed" | "cancelled"
    status = db.Column(
        db.String(20), nullable=False, default="open", index=True
    )

    # True une fois le mail de rappel envoyé (idempotence, anti-doublon)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)

    provider_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True
    )
    provider = db.relationship("Company", back_populates="trainings")
    bookings = db.relationship(
        "Booking",
        back_populates="training",
        cascade="all, delete-orphan",
        # Chargement lazy par défaut ; utiliser joinedload() si besoin de perf
    )

    def __repr__(self) -> str:
        return (
            f"<Training id={self.id} kind={self.kind!r} "
            f"title={self.title!r} status={self.status!r}>"
        )

    # ── Propriétés calculées ─────────────────────────────────────────────────

    @hybrid_property
    def booked_seats(self) -> int:
        """
        Nombre de places confirmées.

        Version Python (instance) : itère les bookings chargés.
        Version SQL (expression)  : sous-requête corrélée — utilisée par
        les filtres/tris SQLAlchemy pour éviter des requêtes Python N+1.
        """
        return sum(
            b.seats for b in self.bookings if b.status == "confirmed"
        )

    @booked_seats.expression  # type: ignore[no-redef]
    def booked_seats(cls):  # noqa: N805
        from app.models.booking import Booking

        return (
            select(func.coalesce(func.sum(Booking.seats), 0))
            .where(
                Booking.training_id == cls.id,
                Booking.status == "confirmed",
            )
            .correlate(cls)
            .scalar_subquery()
        )

    @property
    def available_seats(self) -> int:
        return max(0, self.shared_seats - self.booked_seats)

    @property
    def confirmed_bookings(self) -> list:
        return [b for b in self.bookings if b.status == "confirmed"]

    def attendees(self) -> list[dict]:
        """Liste des inscrits confirmés (pour emails de rappel et rapports)."""
        return [
            {
                "company_name": b.company.name,
                "seats": b.seats,
                "contact_name": b.requested_by.full_name,
                "contact_email": b.requested_by.email,
            }
            for b in self.confirmed_bookings
        ]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "is_remote": self.is_remote,
            "contact_phone": self.contact_phone,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "shared_seats": self.shared_seats,
            "booked_seats": self.booked_seats,
            "available_seats": self.available_seats,
            "price_per_seat": float(self.price_per_seat),
            "status": self.status,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "created_at": self.created_at.isoformat(),
        }
