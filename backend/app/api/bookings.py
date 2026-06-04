from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models import Booking, Training
from app.schemas import BookingSchema
from app.utils.auth import current_user

bp = Blueprint("bookings", __name__)


@bp.get("")
@jwt_required()
def list_bookings():
    """Réservations de la société de l'utilisateur (en tant que demandeur)."""
    user = current_user()
    bookings = (
        Booking.query.filter_by(company_id=user.company_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return jsonify([b.to_dict() for b in bookings]), 200


@bp.get("/incoming")
@jwt_required()
def incoming_bookings():
    """Demandes reçues sur les formations dont l'utilisateur est fournisseur."""
    user = current_user()
    bookings = (
        Booking.query.join(Training)
        .filter(Training.provider_id == user.company_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return jsonify([b.to_dict() for b in bookings]), 200


@bp.post("")
@jwt_required()
def create_booking():
    try:
        data = BookingSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    user = current_user()
    training = Training.query.get_or_404(data["training_id"])

    if training.provider_id == user.company_id:
        return jsonify(error="invalid", message="Own training"), 400
    if training.status != "open":
        return jsonify(error="invalid", message="Training not open"), 400
    if data["seats"] > training.available_seats:
        return jsonify(
            error="invalid",
            message=f"Only {training.available_seats} seats left",
        ), 400

    booking = Booking(
        training_id=training.id,
        company_id=user.company_id,
        requested_by_id=user.id,
        seats=data["seats"],
        status="pending",
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify(booking.to_dict()), 201


@bp.patch("/<int:booking_id>")
@jwt_required()
def update_booking_status(booking_id):
    """Le fournisseur confirme/refuse une demande."""
    booking = Booking.query.get_or_404(booking_id)
    user = current_user()
    if booking.training.provider_id != user.company_id:
        return jsonify(error="forbidden", message="Not your training"), 403

    new_status = (request.get_json() or {}).get("status")
    if new_status not in ("confirmed", "cancelled"):
        return jsonify(error="invalid", message="Bad status"), 400

    if new_status == "confirmed" and booking.seats > booking.training.available_seats:
        return jsonify(error="invalid", message="Not enough seats"), 400

    booking.status = new_status
    db.session.commit()
    return jsonify(booking.to_dict()), 200


@bp.delete("/<int:booking_id>")
@jwt_required()
def cancel_booking(booking_id):
    """Désinscription : possible uniquement tant que la demande n'est pas validée."""
    booking = Booking.query.get_or_404(booking_id)
    user = current_user()
    if booking.company_id != user.company_id:
        return jsonify(error="forbidden", message="Not your booking"), 403
    if booking.status != "pending":
        return jsonify(
            error="invalid",
            message="Réservation déjà validée, désinscription impossible",
        ), 400

    db.session.delete(booking)
    db.session.commit()
    return jsonify(message="unsubscribed"), 200
