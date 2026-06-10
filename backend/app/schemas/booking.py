"""Schemas marshmallow pour les Booking."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class BookingCreateSchema(Schema):
    """Corps de la requête POST /bookings. Exactement un de training_id/room_id requis."""

    training_id = fields.Int(load_default=None, allow_none=True)
    room_id = fields.Int(load_default=None, allow_none=True)
    seats = fields.Int(required=True, validate=validate.Range(min=1))

    @validates_schema
    def validate_one_id(self, data, **kwargs):
        has_t = data.get("training_id") is not None
        has_r = data.get("room_id") is not None
        if has_t == has_r:
            raise ValidationError(
                "Fournissez training_id ou room_id (pas les deux, pas aucun)."
            )


class BookingUpdateSchema(Schema):
    """Corps de la requête PATCH /bookings/<id>."""

    status = fields.Str(
        required=True,
        validate=validate.OneOf(["confirmed", "cancelled"]),
    )


class KindQuerySchema(Schema):
    """Paramètre kind pour filtrer les bookings par type."""

    kind = fields.Str(
        load_default="training",
        validate=validate.OneOf(["training", "room"]),
    )


class BookingSchema(Schema):
    """Représentation publique d'une Booking."""

    id = fields.Int(dump_only=True)
    seats = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    training_id = fields.Int(dump_only=True, allow_none=True)
    room_id = fields.Int(dump_only=True, allow_none=True)
    training_title = fields.Str(dump_only=True, allow_none=True)
    training_starts_at = fields.Str(dump_only=True, allow_none=True)
    company_id = fields.Int(dump_only=True)
    company_name = fields.Str(dump_only=True, allow_none=True)
    requested_by_id = fields.Int(dump_only=True)
    requested_by_name = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.Str(dump_only=True)


class MessageSchema(Schema):
    """Réponse générique avec un message."""

    message = fields.Str()
