from functools import wraps

from flask import jsonify, abort
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.models import User


def current_user():
    """Utilisateur du token. 401 si le compte n'existe plus (token périmé)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id)) if user_id is not None else None
    if user is None:
        abort(401, description="Session expirée, reconnectez-vous")
    return user


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = current_user()
        if not user or user.role != "admin":
            return jsonify(error="forbidden", message="Admin only"), 403
        return fn(*args, **kwargs)

    return wrapper
