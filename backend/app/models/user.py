"""Modèle User — compte utilisateur rattaché à une Company."""
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from .mixins import TimestampMixin


class User(TimestampMixin, db.Model):
    """
    Utilisateur de la plateforme, toujours rattaché à une Company.
    role='admin'  → peut gérer la Company (nom, SIRET, etc.)
    role='member' → peut uniquement réserver des formations/salles
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    # "admin" | "member"
    role = db.Column(db.String(20), nullable=False, default="member")

    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True
    )
    company = db.relationship("Company", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
        }
