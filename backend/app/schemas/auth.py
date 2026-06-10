"""Schemas marshmallow pour l'authentification et la gestion de profil."""
from marshmallow import Schema, fields, validate


# ── Schémas d'entrée ─────────────────────────────────────────────────────────

class RegisterSchema(Schema):
    """Corps de la requête POST /auth/register."""

    first_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=120),
        metadata={"example": "Alice"},
    )
    last_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=120),
        metadata={"example": "Martin"},
    )
    email = fields.Email(required=True, metadata={"example": "alice@example.com"})
    phone = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=30),
        metadata={"example": "0600000000"},
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True,
        metadata={"example": "motdepasse123"},
    )
    # Si absent, le nom de la Company prend la valeur "Prénom Nom"
    company_name = fields.Str(
        load_default=None,
        allow_none=True,
        metadata={"example": "Acme Corp"},
    )
    tags = fields.List(fields.Str(), load_default=None, allow_none=True)


class LoginSchema(Schema):
    """Corps de la requête POST /auth/login."""

    email = fields.Email(required=True, metadata={"example": "alice@example.com"})
    password = fields.Str(
        required=True,
        load_only=True,
        metadata={"example": "motdepasse123"},
    )


class UpdateProfileSchema(Schema):
    """Corps de la requête PATCH /auth/me (tous les champs optionnels)."""

    first_name = fields.Str(validate=validate.Length(min=1, max=120))
    last_name = fields.Str(validate=validate.Length(min=1, max=120))
    phone = fields.Str(validate=validate.Length(min=6, max=30))
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=8), load_only=True)


# ── Schémas de sortie ────────────────────────────────────────────────────────

class UserSchema(Schema):
    """Représentation publique d'un utilisateur."""

    id = fields.Int(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    full_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    company_id = fields.Int(dump_only=True)
    created_at = fields.Str(dump_only=True)


class TokenResponseSchema(Schema):
    """Réponse d'un login ou register réussi."""

    access_token = fields.Str()
    refresh_token = fields.Str(allow_none=True)
    user = fields.Nested(UserSchema)


class AccessTokenSchema(Schema):
    """Réponse d'un refresh réussi."""

    access_token = fields.Str()


class InviteSchema(Schema):
    """Corps de la requête POST /companies/me/invite."""

    email = fields.Email(required=True)
    role = fields.Str(load_default="member", validate=validate.OneOf(["member", "admin"]))


class AcceptInviteSchema(Schema):
    """Corps de la requête POST /auth/accept-invite."""

    token = fields.Str(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    phone = fields.Str(required=True, validate=validate.Length(min=6, max=30))
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
