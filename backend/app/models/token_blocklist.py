"""Modèle TokenBlocklist — jetons JWT révoqués (logout, suppression de compte)."""
from datetime import datetime, timezone

from app.extensions import db


class TokenBlocklist(db.Model):
    """
    Un jti révoqué. `expires_at` permet de purger les lignes devenues inutiles
    (un token expiré est de toute façon refusé). Pas de FK vers users : la
    ligne doit survivre à la suppression du compte.
    """

    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(64), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
