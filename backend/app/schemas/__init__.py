from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class RegisterSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1))
    last_name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    phone = fields.Str(required=True, validate=validate.Length(min=6))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    # Optionnel : nom de la structure. Vide -> "Prénom Nom".
    company_name = fields.Str(load_default=None, allow_none=True)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class UpdateProfileSchema(Schema):
    first_name = fields.Str(validate=validate.Length(min=1))
    last_name = fields.Str(validate=validate.Length(min=1))
    phone = fields.Str(validate=validate.Length(min=6))
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=8))


class TrainingSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(load_default=None, allow_none=True)
    location = fields.Str(load_default=None, allow_none=True)
    is_remote = fields.Bool(load_default=False)
    contact_phone = fields.Str(required=True, validate=validate.Length(min=6))
    starts_at = fields.DateTime(required=True)
    ends_at = fields.DateTime(required=True)
    # Nombre de places proposées à la mutualisation.
    shared_seats = fields.Int(required=True, validate=validate.Range(min=1))
    price_per_seat = fields.Decimal(
        load_default=0, validate=validate.Range(min=0), as_string=False
    )
    status = fields.Str(
        load_default="open",
        validate=validate.OneOf(["open", "closed", "cancelled"]),
    )

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if "starts_at" in data and "ends_at" in data:
            if data["ends_at"] < data["starts_at"]:
                raise ValidationError("ends_at must be after starts_at", "ends_at")


class BookingSchema(Schema):
    training_id = fields.Int(required=True)
    seats = fields.Int(required=True, validate=validate.Range(min=1))
