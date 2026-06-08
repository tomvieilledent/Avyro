"""Mixin partagé : colonnes created_at / updated_at sur tous les modèles."""
from datetime import datetime, timezone

from app.extensions import db

# Lambda pour éviter l'évaluation à l'import (datetime.utcnow est deprecated)
_now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731


class TimestampMixin:
    """Ajoute created_at et updated_at (UTC naïf) à un modèle SQLAlchemy."""

    created_at = db.Column(
        db.DateTime,
        default=_now,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=_now,
        onupdate=_now,
        nullable=False,
    )
