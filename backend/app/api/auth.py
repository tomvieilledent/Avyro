from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from marshmallow import ValidationError

from app.extensions import db
from app.models import User, Company
from app.schemas import RegisterSchema, LoginSchema, UpdateProfileSchema
from app.utils.auth import current_user

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    try:
        data = RegisterSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    if User.query.filter_by(email=data["email"]).first():
        return jsonify(error="conflict", message="Email already used"), 409

    company_name = (data.get("company_name") or "").strip() or (
        f"{data['first_name']} {data['last_name']}".strip()
    )
    company = Company(
        name=company_name,
        kind="pro" if data.get("company_name") else "private",
    )
    db.session.add(company)
    db.session.flush()

    user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        role="admin",  # premier user = admin de sa structure
        company_id=company.id,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return _token_response(user), 201


@bp.post("/login")
def login():
    try:
        data = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify(error="unauthorized", message="Bad credentials"), 401

    return _token_response(user), 200


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    return jsonify(access_token=create_access_token(identity=identity)), 200


@bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    return jsonify(user.to_dict()), 200


@bp.patch("/me")
@jwt_required()
def update_me():
    try:
        data = UpdateProfileSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify(error="validation", messages=err.messages), 422

    user = current_user()
    if "email" in data and data["email"] != user.email:
        if User.query.filter_by(email=data["email"]).first():
            return jsonify(error="conflict", message="Email already used"), 409
        user.email = data["email"]
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "phone" in data:
        user.phone = data["phone"]
    if "password" in data:
        user.set_password(data["password"])
    db.session.commit()
    return jsonify(user.to_dict()), 200


def _token_response(user):
    identity = str(user.id)
    return jsonify(
        access_token=create_access_token(identity=identity),
        refresh_token=create_refresh_token(identity=identity),
        user=user.to_dict(),
    )
