from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models import Training
from app.schemas import TrainingSchema
from app.utils.auth import current_user

bp = Blueprint("trainings", __name__)


@bp.get("/reports")
@jwt_required()
def list_reports():
    """Compte rendu LIVE des inscrits, pour chaque formation proposée."""
    user = current_user()
    kind = request.args.get("kind", "training")
    trainings = (
        Training.query.filter_by(provider_id=user.company_id, kind=kind)
        .order_by(Training.starts_at.asc())
        .all()
    )
    return jsonify(
        [
            {
                "training_id": t.id,
                "training_title": t.title,
                "starts_at": t.starts_at.isoformat(),
                "total_seats": t.booked_seats,
                "attendees": t.attendees(),
            }
            for t in trainings
        ]
    ), 200


@bp.get("")
@jwt_required()
def list_trainings():
    kind = request.args.get("kind", "training")

    if request.args.get("mine") == "true":
        user = current_user()
        query = Training.query.filter_by(provider_id=user.company_id, kind=kind)
    else:
        query = Training.query.filter_by(status="open", kind=kind)

    if search := request.args.get("q"):
        query = query.filter(Training.title.ilike(f"%{search}%"))

    trainings = query.order_by(Training.starts_at.asc()).all()
    return jsonify([t.to_dict() for t in trainings]), 200


@bp.get("/<int:training_id>")
@jwt_required()
def get_training(training_id):
    training = Training.query.get_or_404(training_id)
    return jsonify(training.to_dict()), 200


@bp.post("")
@jwt_required()
def create_training():
    try:
        data = TrainingSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    user = current_user()
    # On ne demande que les places proposées ; total_seats les reflète.
    training = Training(
        provider_id=user.company_id, total_seats=data["shared_seats"], **data
    )
    db.session.add(training)
    db.session.commit()
    return jsonify(training.to_dict()), 201


@bp.patch("/<int:training_id>")
@jwt_required()
def update_training(training_id):
    training = Training.query.get_or_404(training_id)
    user = current_user()
    if training.provider_id != user.company_id:
        return jsonify(error="forbidden", message="Not your training"), 403

    try:
        data = TrainingSchema(partial=True).load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    for key, value in data.items():
        setattr(training, key, value)
    db.session.commit()
    return jsonify(training.to_dict()), 200


@bp.delete("/<int:training_id>")
@jwt_required()
def delete_training(training_id):
    training = Training.query.get_or_404(training_id)
    user = current_user()
    if training.provider_id != user.company_id:
        return jsonify(error="forbidden", message="Not your training"), 403

    db.session.delete(training)
    db.session.commit()
    return jsonify(message="deleted"), 200
