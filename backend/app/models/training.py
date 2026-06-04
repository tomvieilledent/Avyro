from app.extensions import db
from .mixins import TimestampMixin


class Training(TimestampMixin, db.Model):
    __tablename__ = "trainings"

    id = db.Column(db.Integer, primary_key=True)
    # "training" (Avyro bleu) | "room" (Avyro vert : salles de réunion)
    kind = db.Column(db.String(20), nullable=False, default="training", index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    is_remote = db.Column(db.Boolean, default=False, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)

    # passe à True une fois l'email de rappel envoyé (1 jour ouvré avant le début)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)

    total_seats = db.Column(db.Integer, nullable=False, default=0)
    # places mises à disposition pour mutualisation
    shared_seats = db.Column(db.Integer, nullable=False, default=0)
    price_per_seat = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # "open" | "closed" | "cancelled"
    status = db.Column(db.String(20), nullable=False, default="open")

    provider_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    provider = db.relationship("Company", back_populates="trainings")
    bookings = db.relationship(
        "Booking", back_populates="training", cascade="all, delete-orphan"
    )

    @property
    def confirmed_bookings(self):
        return [b for b in self.bookings if b.status == "confirmed"]

    @property
    def booked_seats(self):
        return sum(b.seats for b in self.confirmed_bookings)

    def attendees(self):
        """Liste live des inscrits confirmés."""
        return [
            {
                "company_name": b.company.name,
                "seats": b.seats,
                "contact_name": b.requested_by.full_name,
                "contact_email": b.requested_by.email,
            }
            for b in self.confirmed_bookings
        ]

    @property
    def available_seats(self):
        return self.shared_seats - self.booked_seats

    def to_dict(self):
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
            "total_seats": self.total_seats,
            "shared_seats": self.shared_seats,
            "available_seats": self.available_seats,
            "price_per_seat": float(self.price_per_seat),
            "status": self.status,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "created_at": self.created_at.isoformat(),
        }
