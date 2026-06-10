"""Exporte tous les schemas pour un import centralisé."""
from .auth import (
    RegisterSchema,
    LoginSchema,
    UpdateProfileSchema,
    UserSchema,
    TokenResponseSchema,
    AccessTokenSchema,
    InviteSchema,
    AcceptInviteSchema,
)
from .company import UpdateCompanySchema, CompanySchema
from .training import (
    TrainingCreateSchema,
    TrainingUpdateSchema,
    TrainingQuerySchema,
    TrainingSchema,
    TrainingReportSchema,
)
from .room import (
    RoomCreateSchema,
    RoomUpdateSchema,
    RoomQuerySchema,
    RoomSchema,
    RoomReportSchema,
)
from .booking import (
    BookingCreateSchema,
    BookingUpdateSchema,
    BookingSchema,
    BookingCountsSchema,
    KindQuerySchema,
    MessageSchema,
)

__all__ = [
    "RegisterSchema", "LoginSchema", "UpdateProfileSchema", "UserSchema",
    "TokenResponseSchema", "AccessTokenSchema", "InviteSchema", "AcceptInviteSchema",
    "UpdateCompanySchema", "CompanySchema",
    "TrainingCreateSchema", "TrainingUpdateSchema", "TrainingQuerySchema",
    "TrainingSchema", "TrainingReportSchema",
    "RoomCreateSchema", "RoomUpdateSchema", "RoomQuerySchema",
    "RoomSchema", "RoomReportSchema",
    "BookingCreateSchema", "BookingUpdateSchema", "BookingSchema",
    "BookingCountsSchema", "KindQuerySchema", "MessageSchema",
]
