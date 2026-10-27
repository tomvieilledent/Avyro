"""Tokens d'invitation signés (itsdangerous), distincts des JWT d'accès."""
from flask import current_app
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer

_INVITE_SALT = "avyro-invite-v1"


class InvalidInviteToken(Exception):
    """Token d'invitation illisible, falsifié ou expiré."""


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_INVITE_SALT)


def create_invite_token(email: str, role: str, company_id: int) -> str:
    return _serializer().dumps(
        {"email": email, "role": role, "company_id": company_id}
    )


def read_invite_token(token: str) -> dict:
    """Retourne le payload ou lève InvalidInviteToken."""
    try:
        data = _serializer().loads(
            token, max_age=current_app.config["INVITE_MAX_AGE"]
        )
    except SignatureExpired as exc:
        raise InvalidInviteToken("expired") from exc
    except BadData as exc:
        raise InvalidInviteToken("invalid") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("email"), str)
        or data.get("role") not in ("member", "admin")
        or not isinstance(data.get("company_id"), int)
    ):
        raise InvalidInviteToken("malformed")
    return data
