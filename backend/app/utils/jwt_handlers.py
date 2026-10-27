"""Révocation des JWT : blocklist (jti) et version de token par utilisateur."""
from datetime import datetime, timezone

from flask import jsonify
from flask_jwt_extended import get_jwt

from app.extensions import db, jwt
from app.models import TokenBlocklist, User


def revoke_token(payload: dict) -> None:
    """Ajoute le jti du payload à la blocklist (idempotent). Ne commit pas."""
    jti = payload["jti"]
    if TokenBlocklist.query.filter_by(jti=jti).first() is not None:
        return
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
    sub = payload.get("sub")
    db.session.add(TokenBlocklist(
        jti=jti,
        token_type=payload.get("type", "access"),
        user_id=int(sub) if str(sub).isdigit() else None,
        expires_at=exp,
    ))


def purge_expired_blocklist(now: "datetime | None" = None) -> int:
    """Supprime les entrées dont le token a expiré ; retourne le nombre purgé."""
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    n = TokenBlocklist.query.filter(TokenBlocklist.expires_at <= now).delete(
        synchronize_session=False
    )
    db.session.commit()
    return n


def register_jwt_handlers() -> None:
    @jwt.token_in_blocklist_loader
    def _is_revoked(_header, payload) -> bool:
        if TokenBlocklist.query.filter_by(jti=payload["jti"]).first() is not None:
            return True
        sub = str(payload.get("sub", ""))
        user = db.session.get(User, int(sub)) if sub.isdigit() else None
        # Utilisateur absent : laissé aux contrôles métier (401 explicite).
        # Un token sans claim `tv` (émis avant ce contrôle) est refusé : choix
        # le plus sûr, l'impact se limite à une reconnexion.
        if user is not None and payload.get("tv") != user.token_version:
            return True
        return False

    @jwt.revoked_token_loader
    def _revoked(_header, _payload):
        return jsonify(error="unauthorized", message="Session révoquée, reconnectez-vous."), 401
