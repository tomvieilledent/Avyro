from app.extensions import db
from .mixins import TimestampMixin


class Booking(TimestampMixin, db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    seats = db.Column(db.Integer, nullable=False, default=1)
    # "pending" | "confirmed" | "cancelled"
    status = db.Column(db.String(20), nullable=False, default="pending")

    training_id = db.Column(
        db.Integer, db.ForeignKey("trainings.id"), nullable=False
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    requested_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    training = db.relationship("Training", back_populates="bookings")
    company = db.relationship("Company", back_populates="bookings")
    requested_by = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "seats": self.seats,
            "status": self.status,
            "training_id": self.training_id,
            "training_title": self.training.title if self.training else None,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "requested_by_id": self.requested_by_id,
            "created_at": self.created_at.isoformat(),
        }
