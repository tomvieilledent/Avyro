"""Schemas marshmallow pour les Training (formations et salles)."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


# ── Schémas d'entrée ─────────────────────────────────────────────────────────

class TrainingCreateSchema(Schema):
    """Corps de la requête POST /trainings."""

    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        metadata={"example": "Sécurité incendie"},
    )
    description = fields.Str(load_default=None, allow_none=True)
    location = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    is_remote = fields.Bool(load_default=False)
    contact_phone = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=30),
        metadata={"example": "0600000000"},
    )
    starts_at = fields.DateTime(required=True, metadata={"example": "2026-09-01T09:00:00"})
    ends_at = fields.DateTime(required=True, metadata={"example": "2026-09-01T17:00:00"})
    # Nombre de places proposées à la mutualisation (≥ 1)
    latitude = fields.Float(load_default=None, allow_none=True)
    longitude = fields.Float(load_default=None, allow_none=True)
    shared_seats = fields.Int(required=True, validate=validate.Range(min=1))
    price_per_seat = fields.Float(
        load_default=0.0,
        validate=validate.Range(min=0),
        metadata={"example": 150.0},
    )
    status = fields.Str(
        load_default="open",
        validate=validate.OneOf(["open", "closed", "cancelled"]),
    )
    tags = fields.List(fields.Str(), load_default=None, allow_none=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if "starts_at" in data and "ends_at" in data:
            if data["ends_at"] <= data["starts_at"]:
                raise ValidationError(
                    "ends_at doit être postérieur à starts_at.", "ends_at"
                )


class TrainingUpdateSchema(Schema):
    """Corps de la requête PATCH /trainings/<id> (tous les champs optionnels)."""

    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True, validate=validate.Length(max=255))
    is_remote = fields.Bool()
    contact_phone = fields.Str(validate=validate.Length(min=6, max=30))
    starts_at = fields.DateTime()
    ends_at = fields.DateTime()
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    shared_seats = fields.Int(validate=validate.Range(min=1))
    price_per_seat = fields.Float(validate=validate.Range(min=0))
    status = fields.Str(validate=validate.OneOf(["open", "closed", "cancelled"]))
    tags = fields.List(fields.Str(), allow_none=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if "starts_at" in data and "ends_at" in data:
            if data["ends_at"] <= data["starts_at"]:
                raise ValidationError(
                    "ends_at doit être postérieur à starts_at.", "ends_at"
                )


class TrainingQuerySchema(Schema):
    """Paramètres de requête GET /trainings."""

    mine = fields.Bool(load_default=False)
    q = fields.Str(load_default=None, allow_none=True)
    tag = fields.Str(load_default=None, allow_none=True)
    date_from = fields.Date(load_default=None, allow_none=True)
    date_to = fields.Date(load_default=None, allow_none=True)
    price_max = fields.Float(load_default=None, allow_none=True)
    seats_min = fields.Int(load_default=None, allow_none=True)
    remote_only = fields.Bool(load_default=False)
    lat = fields.Float(load_default=None, allow_none=True)
    lng = fields.Float(load_default=None, allow_none=True)
    radius = fields.Float(load_default=25.0)


# ── Schémas de sortie ────────────────────────────────────────────────────────

class TrainingSchema(Schema):
    """Représentation publique d'une Training."""

    id = fields.Int(dump_only=True)
    kind = fields.Str(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)
    location = fields.Str(dump_only=True, allow_none=True)
    is_remote = fields.Bool(dump_only=True)
    contact_phone = fields.Str(dump_only=True)
    starts_at = fields.Str(dump_only=True)
    ends_at = fields.Str(dump_only=True)
    latitude = fields.Float(dump_only=True, allow_none=True)
    longitude = fields.Float(dump_only=True, allow_none=True)
    distance_km = fields.Float(dump_only=True, allow_none=True)
    shared_seats = fields.Int(dump_only=True)
    booked_seats = fields.Int(dump_only=True)
    available_seats = fields.Int(dump_only=True)
    price_per_seat = fields.Float(dump_only=True)
    tags = fields.List(fields.Str(), dump_only=True)
    status = fields.Str(dump_only=True)
    provider_id = fields.Int(dump_only=True)
    provider_name = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.Str(dump_only=True)


class AttendeeSchema(Schema):
    """Inscrit confirmé dans un rapport."""

    company_name = fields.Str()
    seats = fields.Int()
    contact_name = fields.Str()
    contact_email = fields.Email()


class TrainingReportSchema(Schema):
    """Compte rendu live d'une Training (liste des inscrits)."""

    training_id = fields.Int()
    training_title = fields.Str()
    starts_at = fields.Str()
    total_seats = fields.Int(metadata={"description": "Nombre total de places confirmées"})
    attendees = fields.List(fields.Nested(AttendeeSchema))
