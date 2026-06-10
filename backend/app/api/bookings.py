"""
Routes Booking : réservations de places sur Training ou Room.
Préfixe : /api/bookings
"""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from app.extensions import db
from app.models import Booking, Training, Room
from app.schemas import (
    BookingCreateSchema,
    BookingUpdateSchema,
    BookingSchema,
    KindQuerySchema,
    MessageSchema,
)
from app.utils.auth import current_user

blp = Blueprint(
    "bookings",
    __name__,
    url_prefix="/api/bookings",
    description="Gestion des réservations de places.",
)


@blp.route("/incoming")
class IncomingBookingsView(MethodView):
    decorators = [jwt_required()]

    @blp.arguments(KindQuerySchema, location="query")
    @blp.response(200, BookingSchema(many=True))
    def get(self, args: dict):
        """Demandes reçues sur les formations ou salles du provider."""
        user = current_user()
        if args["kind"] == "room":
            bookings = (
                Booking.query.join(Room, Booking.room_id == Room.id)
                .filter(Room.provider_id == user.company_id)
                .order_by(Booking.created_at.desc())
                .all()
            )
        else:
            bookings = (
                Booking.query.join(Training, Booking.training_id == Training.id)
                .filter(Training.provider_id == user.company_id)
                .order_by(Booking.created_at.desc())
                .all()
            )
        return [b.to_dict() for b in bookings]


@blp.route("")
class BookingListView(MethodView):
    decorators = [jwt_required()]

    @blp.arguments(KindQuerySchema, location="query")
    @blp.response(200, BookingSchema(many=True))
    def get(self, args: dict):
        """Réservations de la Company (formations ou salles)."""
        user = current_user()
        if args["kind"] == "room":
            bookings = (
                Booking.query
                .filter(
                    Booking.company_id == user.company_id,
                    Booking.room_id.isnot(None),
                )
                .order_by(Booking.created_at.desc())
                .all()
            )
        else:
            bookings = (
                Booking.query
                .filter(
                    Booking.company_id == user.company_id,
                    Booking.training_id.isnot(None),
                )
                .order_by(Booking.created_at.desc())
                .all()
            )
        return [b.to_dict() for b in bookings]

    @blp.arguments(BookingCreateSchema, location="json")
    @blp.response(201, BookingSchema)
    def post(self, args: dict):
        """Crée une demande de réservation (pending)."""
        user = current_user()
        training_id = args.get("training_id")
        room_id = args.get("room_id")

        if training_id:
            item = db.get_or_404(Training, training_id)
        else:
            item = db.get_or_404(Room, room_id)

        if item.provider_id == user.company_id:
            abort(400, message="Vous ne pouvez pas réserver votre propre offre.")

        if item.status != "open":
            abort(400, message="Cette offre n'accepte plus de réservations.")

        if args["seats"] > item.available_seats:
            abort(400, message=f"Seulement {item.available_seats} place(s) disponible(s).")

        booking = Booking(
            training_id=training_id,
            room_id=room_id,
            company_id=user.company_id,
            requested_by_id=user.id,
            seats=args["seats"],
            status="pending",
        )
        db.session.add(booking)
        db.session.commit()
        return booking.to_dict()


@blp.route("/<int:booking_id>")
class BookingDetailView(MethodView):
    decorators = [jwt_required()]

    @blp.arguments(BookingUpdateSchema, location="json")
    @blp.response(200, BookingSchema)
    def patch(self, args: dict, booking_id: int):
        """Le provider confirme ou refuse une demande."""
        booking = db.get_or_404(Booking, booking_id)
        user = current_user()
        item = booking._item

        if item.provider_id != user.company_id:
            abort(403, message="Vous n'êtes pas le provider de cette offre.")

        if args["status"] == "confirmed":
            if booking.seats > item.available_seats:
                abort(400, message=f"Plus assez de places : {item.available_seats} disponible(s).")

        booking.status = args["status"]
        db.session.commit()
        return booking.to_dict()

    @blp.response(200, MessageSchema)
    def delete(self, booking_id: int):
        """Le booker annule sa demande (pending uniquement)."""
        booking = db.get_or_404(Booking, booking_id)
        user = current_user()

        if booking.company_id != user.company_id:
            abort(403, message="Cette réservation n'appartient pas à votre Company.")

        if booking.status != "pending":
            abort(400, message="Impossible d'annuler une réservation déjà confirmée.")

        db.session.delete(booking)
        db.session.commit()
        return {"message": "Désinscription effectuée."}
