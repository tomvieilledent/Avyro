"""Schemas marshmallow pour les Company."""
from marshmallow import Schema, fields, validate

from .fields import NormalizedEmail, StrippedStr


class UpdateCompanySchema(Schema):
    """Corps de la requête PATCH /companies/me (tous les champs optionnels)."""

    name = StrippedStr(validate=validate.Length(min=1, max=255))
    kind = fields.Str(validate=validate.OneOf(["pro", "private"]))
    siret = fields.Str(
        validate=validate.Length(max=20), allow_none=True, load_default=None
    )
    contact_email = NormalizedEmail(
        allow_none=True, load_default=None, validate=validate.Length(max=255)
    )
    tags = fields.List(
        StrippedStr(validate=validate.Length(min=1, max=50)),
        allow_none=True,
        validate=validate.Length(max=20),
    )


class CompanySchema(Schema):
    """Représentation publique d'une Company."""

    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    kind = fields.Str(dump_only=True)
    siret = fields.Str(dump_only=True, allow_none=True)
    contact_email = fields.Str(dump_only=True, allow_none=True)
    tags = fields.List(fields.Str(), dump_only=True)
    created_at = fields.Str(dump_only=True)
