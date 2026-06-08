"""Exporte tous les schemas pour un import centralisé."""
from .auth import (
    RegisterSchema,
    LoginSchema,
    UpdateProfileSchema,
    UserSchema,
    TokenResponseSchema,
    AccessTokenSchema,
)
from .company import UpdateCompanySchema, CompanySchema
from .training import (
    TrainingCreateSchema,
    TrainingUpdateSchema,
    TrainingQuerySchema,
    TrainingSchema,
    TrainingReportSchema,
)
from .booking import (
    BookingCreateSchema,
    BookingUpdateSchema,
    BookingSchema,
    MessageSchema,
)

__all__ = [
    "RegisterSchema",
    "LoginSchema",
    "UpdateProfileSchema",
    "UserSchema",
    "TokenResponseSchema",
    "AccessTokenSchema",
    "UpdateCompanySchema",
    "CompanySchema",
    "TrainingCreateSchema",
    "TrainingUpdateSchema",
    "TrainingQuerySchema",
    "TrainingSchema",
    "TrainingReportSchema",
    "BookingCreateSchema",
    "BookingUpdateSchema",
    "BookingSchema",
    "MessageSchema",
]
