from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Company
from app.utils.auth import current_user

bp = Blueprint("companies", __name__)


@bp.get("/me")
@jwt_required()
def my_company():
    user = current_user()
    return jsonify(user.company.to_dict()), 200


@bp.patch("/me")
@jwt_required()
def update_my_company():
    user = current_user()
    if user.role != "admin":
        return jsonify(error="forbidden", message="Admin only"), 403

    company = user.company
    data = request.get_json() or {}
    for field in ("name", "kind", "siret", "contact_email"):
        if field in data:
            setattr(company, field, data[field])
    db.session.commit()
    return jsonify(company.to_dict()), 200


@bp.get("/<int:company_id>")
@jwt_required()
def get_company(company_id):
    company = Company.query.get_or_404(company_id)
    return jsonify(company.to_dict()), 200
