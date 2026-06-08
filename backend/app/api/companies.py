"""
Routes Company : consultation et mise à jour de la structure de l'utilisateur.
Préfixe : /api/companies
"""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from app.extensions import db
from app.models import Company
from app.schemas import UpdateCompanySchema, CompanySchema
from app.utils.auth import current_user

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
                # Permet d'effacer siret / contact_email en envoyant null
                setattr(company, field, None)

        db.session.commit()
        return company.to_dict()


@blp.route("/<int:company_id>")
class CompanyDetailView(MethodView):
    """Consultation publique d'une Company par son id."""

    decorators = [jwt_required()]

    @blp.response(200, CompanySchema, description="Données de la Company.")
    @blp.alt_response(404, description="Company introuvable.")
    def get(self, company_id: int):
        """Retourne une Company par son identifiant."""
        company = db.get_or_404(Company, company_id)
        return company.to_dict()
