"""Modèle Booking — demande de réservation de places sur une Training."""
from app.extensions import db
from .mixins import TimestampMixin


class Booking(TimestampMixin, db.Model):
    """
    Demande de réservation créée par une Company (booker) sur une Training
    publiée par une autre Company (provider).

    Workflow de statut :
        pending   → confirmed   (validé par le provider)
        pending   → cancelled   (refusé par le provider OU annulé par le booker)
        confirmed → cancelled   (NON : une réservation confirmée ne peut plus
                                 être annulée par le booker via l'API)
    """

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    seats = db.Column(db.Integer, nullable=False, default=1)
    # "pending" | "confirmed" | "cancelled"
    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )

    training_id = db.Column(
        db.Integer, db.ForeignKey("trainings.id"), nullable=False, index=True
    )
    # Company qui réserve
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True
    )
    # Utilisateur qui a créé la demande
    requested_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    training = db.relationship("Training", back_populates="bookings")
    company = db.relationship("Company", back_populates="bookings")
    requested_by = db.relationship("User")

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} training={self.training_id} "
            f"company={self.company_id} status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "seats": self.seats,
            "status": self.status,
            "training_id": self.training_id,
            "training_title": self.training.title if self.training else None,
            "training_starts_at": (
                self.training.starts_at.isoformat() if self.training else None
            ),
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "requested_by_id": self.requested_by_id,
            "requested_by_name": (
                self.requested_by.full_name if self.requested_by else None
            ),
            "created_at": self.created_at.isoformat(),
        }
