"""
Routes Booking : demandes de réservation de places.
Préfixe : /api/bookings

Workflow :
  POST /bookings        → crée une demande (status=pending)
  PATCH /bookings/<id>  → provider confirme ou refuse (confirmed | cancelled)
  DELETE /bookings/<id> → booker annule sa demande (pending seulement)
  GET /bookings         → liste les réservations de la Company du user
  GET /bookings/incoming → liste les demandes reçues sur ses propres formations
"""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from app.extensions import db
from app.models import Booking, Training
from app.schemas import (
    BookingCreateSchema,
    BookingUpdateSchema,
    BookingSchema,
    MessageSchema,
    TrainingQuerySchema,
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
    """
    Demandes reçues sur les formations/salles du provider.
    Route déclarée avant `/<int:booking_id>` pour éviter la collision.
    """

    decorators = [jwt_required()]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, BookingSchema(many=True), description="Demandes reçues.")
    def get(self, args: dict):
        """
        Liste toutes les demandes de réservation reçues sur les formations/salles
        de la Company de l'utilisateur connecté.
        """
        user = current_user()
        bookings = (
            Booking.query.join(Training)
            .filter(
                Training.provider_id == user.company_id,
                Training.kind == args["kind"],
            )
            .order_by(Booking.created_at.desc())
            .all()
        )
        return [b.to_dict() for b in bookings]


@blp.route("")
class BookingListView(MethodView):
    """Liste et création de réservations."""

    decorators = [jwt_required()]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, BookingSchema(many=True), description="Réservations de la Company.")
    def get(self, args: dict):
        """
        Liste les réservations effectuées par la Company de l'utilisateur.
        Triées par date de création décroissante.
        """
        user = current_user()
        bookings = (
            Booking.query.join(Training)
            .filter(
                Booking.company_id == user.company_id,
                Training.kind == args["kind"],
            )
            .order_by(Booking.created_at.desc())
            .all()
        )
        return [b.to_dict() for b in bookings]

    @blp.arguments(BookingCreateSchema, location="json")
    @blp.response(201, BookingSchema, description="Demande de réservation créée (pending).")
    @blp.alt_response(400, description="Règles métier violées (propre formation, pas de places, etc.)")
    @blp.alt_response(404, description="Formation introuvable.")
    @blp.alt_response(422, description="Données invalides.")
    def post(self, args: dict):
        """
        Crée une demande de réservation (status=pending).

        Règles :
        - Impossible de réserver sa propre formation.
        - La formation doit être `open`.
        - Le nombre de places demandées ne peut pas dépasser `available_seats`.
        """
        user = current_user()
        training = db.get_or_404(Training, args["training_id"])

        if training.provider_id == user.company_id:
            abort(400, message="Vous ne pouvez pas réserver votre propre formation.")

        if training.status != "open":
            abort(400, message="Cette formation n'accepte plus de réservations.")

        if args["seats"] > training.available_seats:
            abort(
                400,
                message=(
                    f"Seulement {training.available_seats} place(s) disponible(s)."
                ),
            )

        booking = Booking(
            training_id=training.id,
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
    """Mise à jour du statut et annulation d'une réservation."""

    decorators = [jwt_required()]

    @blp.arguments(BookingUpdateSchema, location="json")
    @blp.response(200, BookingSchema, description="Réservation mise à jour.")
    @blp.alt_response(400, description="Places insuffisantes pour confirmer.")
    @blp.alt_response(403, description="Vous n'êtes pas le provider de cette formation.")
    @blp.alt_response(404, description="Réservation introuvable.")
    def patch(self, args: dict, booking_id: int):
        """
        Le provider confirme ou refuse une demande de réservation.

        - `confirmed` : vérifie qu'il reste assez de places avant de valider.
        - `cancelled` : refuse la demande.
        """
        booking = db.get_or_404(Booking, booking_id)
        user = current_user()

        if booking.training.provider_id != user.company_id:
            abort(403, message="Vous n'êtes pas le provider de cette formation.")

        if args["status"] == "confirmed":
            if booking.seats > booking.training.available_seats:
                abort(
                    400,
                    message=(
                        f"Plus assez de places : "
                        f"{booking.training.available_seats} disponible(s)."
                    ),
                )

        booking.status = args["status"]
        db.session.commit()
        return booking.to_dict()

    @blp.response(200, MessageSchema, description="Désinscription effectuée.")
    @blp.alt_response(400, description="Impossible d'annuler une réservation confirmée.")
    @blp.alt_response(403, description="Cette réservation n'appartient pas à votre Company.")
    @blp.alt_response(404, description="Réservation introuvable.")
    def delete(self, booking_id: int):
        """
        Le booker annule sa demande de réservation.

        Impossible si la réservation est déjà confirmée.
        """
        booking = db.get_or_404(Booking, booking_id)
        user = current_user()

        if booking.company_id != user.company_id:
            abort(403, message="Cette réservation n'appartient pas à votre Company.")

        if booking.status != "pending":
            abort(
                400,
                message="Impossible d'annuler une réservation déjà confirmée.",
            )

        db.session.delete(booking)
        db.session.commit()
        return {"message": "Désinscription effectuée."}
