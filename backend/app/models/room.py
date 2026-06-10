"""Modèle Room — salle de réunion mutualisée (Avyro Room)."""
import json

from sqlalchemy import select, func
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions import db
from .mixins import TimestampMixin


class Room(TimestampMixin, db.Model):
    """
    Salle de réunion proposée par une Company (provider) à d'autres entreprises.
    Même workflow que Training : publication → réservation → confirmation.
    Table dédiée `rooms` pour séparer clairement les deux domaines.
    """

    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    is_remote = db.Column(db.Boolean, default=False, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    shared_seats = db.Column(db.Integer, nullable=False, default=1)
    price_per_seat = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    _tags = db.Column("tags", db.Text, nullable=True)

    provider_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True
    )
    provider = db.relationship("Company", back_populates="rooms")
    bookings = db.relationship(
        "Booking",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    @property
    def tags(self) -> list:
        try:
            return json.loads(self._tags) if self._tags else []
        except (ValueError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list | None):
        self._tags = json.dumps(value) if value else None

    def __repr__(self) -> str:
        return f"<Room id={self.id} title={self.title!r} status={self.status!r}>"

    @hybrid_property
    def booked_seats(self) -> int:
        return sum(b.seats for b in self.bookings if b.status == "confirmed")

    @booked_seats.expression  # type: ignore[no-redef]
    def booked_seats(cls):  # noqa: N805
        from app.models.booking import Booking

        return (
            select(func.coalesce(func.sum(Booking.seats), 0))
            .where(Booking.room_id == cls.id, Booking.status == "confirmed")
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
            "kind": "room",
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "is_remote": self.is_remote,
            "contact_phone": self.contact_phone,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": None,
            "shared_seats": self.shared_seats,
            "booked_seats": self.booked_seats,
            "available_seats": self.available_seats,
            "price_per_seat": float(self.price_per_seat),
            "tags": self.tags,
            "status": self.status,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "created_at": self.created_at.isoformat(),
        }
