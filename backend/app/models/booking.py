"""Modèle Booking — demande de réservation sur une Training ou une Room."""
from app.extensions import db
from .mixins import TimestampMixin


class Booking(TimestampMixin, db.Model):
    """
    Demande de réservation créée par une Company (booker) sur une Training
    ou une Room publiée par une autre Company (provider).

    Exactement un des deux champs training_id / room_id est renseigné.

    Workflow de statut :
        pending   → confirmed   (validé par le provider)
        pending   → cancelled   (refusé par le provider OU annulé par le booker)
    """

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    seats = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )

    training_id = db.Column(
        db.Integer, db.ForeignKey("trainings.id"), nullable=True, index=True
    )
    room_id = db.Column(
        db.Integer, db.ForeignKey("rooms.id"), nullable=True, index=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True
    )
    requested_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    training = db.relationship("Training", back_populates="bookings")
    room = db.relationship("Room", back_populates="bookings")
    company = db.relationship("Company", back_populates="bookings")
    requested_by = db.relationship("User")

    def __repr__(self) -> str:
        ref = f"training={self.training_id}" if self.training_id else f"room={self.room_id}"
        return f"<Booking id={self.id} {ref} company={self.company_id} status={self.status!r}>"

    @property
    def _item(self):
        """Retourne la Training ou la Room associée."""
        return self.training or self.room

    def to_dict(self) -> dict:
        item = self._item
        return {
            "id": self.id,
            "seats": self.seats,
            "status": self.status,
            "training_id": self.training_id,
            "room_id": self.room_id,
            "training_title": item.title if item else None,
            "training_starts_at": item.starts_at.isoformat() if item else None,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "requested_by_id": self.requested_by_id,
            "requested_by_name": (
                self.requested_by.full_name if self.requested_by else None
            ),
            "created_at": self.created_at.isoformat(),
        }
