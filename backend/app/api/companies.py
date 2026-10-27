"""
Routes Company : consultation et mise à jour de la structure de l'utilisateur.
Préfixe : /api/companies
"""
from flask.views import MethodView
from flask import current_app
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Company, User
from app.schemas import UpdateCompanySchema, CompanySchema, InviteSchema, MessageSchema
from app.services.mailer import send_email
from app.utils.auth import current_user
from app.utils.tokens import create_invite_token

blp = Blueprint(
    "companies",
    __name__,
    url_prefix="/api/companies",
    description="Gestion des structures (entreprises/particuliers).",
)


@blp.route("/me")
class MyCompanyView(MethodView):
    """Consultation et mise à jour de la Company de l'utilisateur connecté."""

    decorators = [jwt_required()]

    @blp.response(200, CompanySchema, description="Données de la Company.")
    def get(self):
        """Retourne la Company de l'utilisateur authentifié."""
        return current_user().company.to_dict()

    @blp.arguments(UpdateCompanySchema, location="json")
    @blp.response(200, CompanySchema, description="Company mise à jour.")
    @blp.alt_response(403, description="Réservé aux administrateurs.")
    @blp.alt_response(422, description="Données invalides.")
    def patch(self, args: dict):
        """
        Met à jour les informations de la Company.

        Réservé à l'utilisateur avec le rôle `admin` dans la Company.
        Seuls les champs fournis sont modifiés (PATCH sémantique).
        """
        user = current_user()
        if user.role != "admin":
            abort(403, message="Seul l'administrateur peut modifier la structure.")

        company = user.company
        for field in ("name", "kind", "siret", "contact_email"):
            if field in args and args[field] is not None:
                setattr(company, field, args[field])
            elif field in args:
                setattr(company, field, None)
        if "tags" in args:
            company.tags = args["tags"] or []

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409, message="Ce SIRET est déjà utilisé.")
        return company.to_dict()


@blp.route("/me/invite")
class InviteView(MethodView):
    """Invite un nouveau membre dans la Company de l'admin."""

    decorators = [jwt_required()]

    @blp.arguments(InviteSchema, location="json")
    @blp.response(200, MessageSchema)
    def post(self, args: dict):
        """Envoie un lien d'invitation par email (admin uniquement)."""
        user = current_user()
        if user.role != "admin":
            abort(403, message="Seul l'administrateur peut inviter des membres.")

        invite_email = args["email"]
        if User.query.filter(func.lower(User.email) == invite_email).first():
            abort(409, message="Un compte existe déjà avec cet email.")

        token = create_invite_token(
            invite_email, args.get("role", "member"), user.company_id
        )
        base = current_app.config["PUBLIC_URL"].rstrip("/")
        invite_url = f"{base}/invite?token={token}"

        sent = send_email(
            to=invite_email,
            subject=f"Invitation à rejoindre {user.company.name} sur Avyro",
            body=(
                f"Bonjour,\n\n"
                f"{user.full_name} vous invite à rejoindre {user.company.name} "
                f"sur la plateforme Avyro.\n\n"
                f"Cliquez sur le lien suivant pour créer votre compte "
                f"(valable 7 jours) :\n\n{invite_url}\n\n"
                f"Si vous n'attendiez pas cette invitation, ignorez ce message."
            ),
        )
        if not sent:
            return {"message": "Invitation créée, mais l'email n'a pas pu être envoyé."}
        return {"message": "Invitation envoyée."}


@blp.route("/<int:company_id>")
class CompanyDetailView(MethodView):
    """Consultation publique d'une Company par son id."""

    decorators = [jwt_required(optional=True)]

    @blp.response(200, CompanySchema, description="Données de la Company.")
    @blp.alt_response(404, description="Company introuvable.")
    def get(self, company_id: int):
        """Retourne une Company par son identifiant (public)."""
        company = db.get_or_404(Company, company_id)
        return company.to_dict()


@blp.route("/<int:company_id>/offerings")
class CompanyOfferingsView(MethodView):
    """Offres actives (formations et salles) d'une Company."""

    decorators = [jwt_required(optional=True)]

    @blp.response(200, description="Offres actives de la Company.")
    def get(self, company_id: int):
        """Retourne les formations et salles ouvertes publiées par cette Company."""
        from app.models import Training, Room
        company = db.get_or_404(Company, company_id)
        trainings = [
            t.to_dict() for t in
            Training.query.filter_by(provider_id=company_id, status="open")
            .order_by(Training.starts_at.asc()).all()
        ]
        rooms = [
            r.to_dict() for r in
            Room.query.filter_by(provider_id=company_id, status="open")
            .order_by(Room.starts_at.asc()).all()
        ]
        return {"company": company.to_dict(), "trainings": trainings, "rooms": rooms}
