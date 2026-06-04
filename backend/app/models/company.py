from app.extensions import db
from .mixins import TimestampMixin


class Company(TimestampMixin, db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # "pro" = entreprise, "private" = particulier
    kind = db.Column(db.String(20), nullable=False, default="pro")
    siret = db.Column(db.String(20), unique=True, nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)

    users = db.relationship("User", back_populates="company")
    trainings = db.relationship(
        "Training", back_populates="provider", cascade="all, delete-orphan"
    )
    bookings = db.relationship(
        "Booking", back_populates="company", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "siret": self.siret,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat(),
        }
