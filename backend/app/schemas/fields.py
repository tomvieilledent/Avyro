"""Champs marshmallow réutilisables."""
from marshmallow import fields


class NormalizedEmail(fields.Email):
    """Email : strip + minuscules avant validation."""

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            value = value.strip().lower()
        return super()._deserialize(value, attr, data, **kwargs)


class StrippedStr(fields.Str):
    """Chaîne dont les espaces de début/fin sont retirés avant validation."""

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.strip()
