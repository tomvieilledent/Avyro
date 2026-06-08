"""Schemas marshmallow pour les Booking."""
from marshmallow import Schema, fields, validate


# ── Schémas d'entrée ─────────────────────────────────────────────────────────

class BookingCreateSchema(Schema):
    """Corps de la requête POST /bookings."""

    training_id = fields.Int(required=True)
    seats = fields.Int(required=True, validate=validate.Range(min=1))


class BookingUpdateSchema(Schema):
    """Corps de la requête PATCH /bookings/<id>."""

    status = fields.Str(
        required=True,
        validate=validate.OneOf(["confirmed", "cancelled"]),
    )


# ── Schémas de sortie ────────────────────────────────────────────────────────

class BookingSchema(Schema):
    """Représentation publique d'une Booking."""

    id = fields.Int(dump_only=True)
    seats = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    training_id = fields.Int(dump_only=True)
    training_title = fields.Str(dump_only=True, allow_none=True)
    training_starts_at = fields.Str(dump_only=True, allow_none=True)
    company_id = fields.Int(dump_only=True)
    company_name = fields.Str(dump_only=True, allow_none=True)
    requested_by_id = fields.Int(dump_only=True)
    requested_by_name = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.Str(dump_only=True)


# ── Schéma utilitaire ────────────────────────────────────────────────────────

class MessageSchema(Schema):
    """Réponse générique avec un message."""

    message = fields.Str()
