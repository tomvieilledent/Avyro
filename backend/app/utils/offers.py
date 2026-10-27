"""Helpers partagés Training/Room : verrouillage et places confirmées."""
from datetime import datetime, timezone

from sqlalchemy import func

from app.extensions import db
from app.models import Booking, Training


def lock_offer(model, offer_id: int):
    """Charge l'offre avec SELECT ... FOR UPDATE (sérialise les calculs de places)."""
    return (
        db.session.query(model)
        .filter(model.id == offer_id)
        .populate_existing()
        .with_for_update()
        .first()
    )


def confirmed_seats(item) -> int:
    """Places confirmées, lues en base (pas depuis le cache de la relation)."""
    col = Booking.training_id if isinstance(item, Training) else Booking.room_id
    return int(
        db.session.query(func.coalesce(func.sum(Booking.seats), 0))
        .filter(col == item.id, Booking.status == "confirmed")
        .scalar()
    )


def available_seats(item) -> int:
    return max(0, item.shared_seats - confirmed_seats(item))


def to_naive_utc(value: datetime) -> datetime:
    """Normalise un datetime en UTC naïf (convention de stockage)."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def normalize_dates(args: dict) -> None:
    """Normalise in-place starts_at/ends_at présents dans args."""
    for key in ("starts_at", "ends_at"):
        if key in args and args[key] is not None:
            args[key] = to_naive_utc(args[key])
