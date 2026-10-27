"""Modèle User — compte utilisateur rattaché à une Company."""
from sqlalchemy import func
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
    # Unicité insensible à la casse, garantie par la base (en plus de unique=True)
    __table_args__ = (
        db.Index("uq_users_email_lower", func.lower(db.column("email")), unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    # "admin" | "member"
    role = db.Column(db.String(20), nullable=False, default="member")

    # Incrémenté au changement de mot de passe : invalide les refresh tokens
    token_version = db.Column(
        db.Integer, nullable=False, default=0, server_default="0"
    )

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
        if self.id is not None:
            # Compte existant : révoque les refresh tokens déjà émis
            self.token_version = (self.token_version or 0) + 1
        else:
            self.token_version = 0

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
