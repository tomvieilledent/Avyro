from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from .mixins import TimestampMixin


class User(TimestampMixin, db.Model):
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
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    company = db.relationship("Company", back_populates="users")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
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
