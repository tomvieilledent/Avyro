"""Helpers JWT : récupération de l'utilisateur courant, décorateur admin."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_smorest import abort

from app.models import User


def current_user_optional() -> "User | None":
    """Comme current_user() mais retourne None si pas de JWT."""
    user_id = get_jwt_identity()
    return db_get_user(int(user_id)) if user_id is not None else None


def current_user() -> User:
    """
    Renvoie l'utilisateur authentifié depuis le JWT en cours.
    Abandonne avec 401 si le compte n'existe plus (token révoqué ou supprimé).
    """
    user_id = get_jwt_identity()
    user = db_get_user(int(user_id)) if user_id is not None else None
    if user is None:
        abort(401, message="Session expirée, reconnectez-vous.")
    return user


def db_get_user(user_id: int) -> "User | None":
    """Récupère un User par id (SQLAlchemy 2.x)."""
    from app.extensions import db
    return db.session.get(User, user_id)


def admin_required(fn):
    """
    Décorateur : vérifie que l'utilisateur authentifié est admin de sa Company.
    Combine jwt_required + vérification du rôle.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = current_user()
        if user.role != "admin":
            abort(403, message="Accès réservé aux administrateurs.")
        return fn(*args, **kwargs)

    return wrapper
