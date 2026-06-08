"""
Routes d'authentification : inscription, connexion, refresh token, profil.
Préfixe : /api/auth
"""
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from flask_smorest import Blueprint, abort

from app.extensions import db, limiter
from app.models import User, Company
from app.schemas import (
    RegisterSchema,
    LoginSchema,
    UpdateProfileSchema,
    UserSchema,
    TokenResponseSchema,
    AccessTokenSchema,
)
from app.utils.auth import current_user

blp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
    description="Authentification et gestion du profil utilisateur.",
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_token_response(user: User) -> dict:
    """Construit la réponse d'authentification avec les deux tokens JWT."""
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
        "user": user.to_dict(),
    }


# ── Vues ─────────────────────────────────────────────────────────────────────

@blp.route("/register")
class RegisterView(MethodView):
    """Inscription : crée une Company et son premier utilisateur (admin)."""

    # Rate limit serré : anti-abus / création de masse de comptes
    decorators = [limiter.limit("10 per hour")]

    @blp.doc(security=[])  # Endpoint public : pas de JWT requis
    @blp.arguments(RegisterSchema, location="json")
    @blp.response(201, TokenResponseSchema, description="Compte créé. Retourne les tokens JWT.")
    @blp.alt_response(409, description="Email déjà utilisé.")
    @blp.alt_response(422, description="Données invalides.")
    def post(self, args: dict):
        """
        Crée un compte entreprise (Company) et son premier utilisateur (admin).

        Si `company_name` est absent ou vide, le nom de la Company vaut
        « Prénom Nom » de l'utilisateur.
        """
        if User.query.filter_by(email=args["email"]).first():
            abort(409, message="Cet email est déjà utilisé.")

        company_name = (args.get("company_name") or "").strip() or (
            f"{args['first_name']} {args['last_name']}".strip()
        )
        company = Company(
            name=company_name,
            kind="pro" if args.get("company_name") else "private",
        )
        db.session.add(company)
        db.session.flush()  # Génère company.id sans commit

        user = User(
            email=args["email"],
            first_name=args["first_name"],
            last_name=args["last_name"],
            phone=args["phone"],
            role="admin",  # Premier utilisateur = admin de sa structure
            company_id=company.id,
        )
        user.set_password(args["password"])
        db.session.add(user)
        db.session.commit()

        return _build_token_response(user)


@blp.route("/login")
class LoginView(MethodView):
    """Connexion : retourne un access token + refresh token."""

    # Rate limit strict : protection contre le brute-force
    decorators = [limiter.limit("20 per minute")]

    @blp.doc(security=[])
    @blp.arguments(LoginSchema, location="json")
    @blp.response(200, TokenResponseSchema, description="Connexion réussie.")
    @blp.alt_response(401, description="Email ou mot de passe incorrect.")
    @blp.alt_response(422, description="Données invalides.")
    def post(self, args: dict):
        """Authentifie l'utilisateur et retourne ses tokens JWT."""
        user = User.query.filter_by(email=args["email"]).first()
        if not user or not user.check_password(args["password"]):
            # Message volontairement vague pour ne pas révéler l'existence du compte
            abort(401, message="Email ou mot de passe incorrect.")
        return _build_token_response(user)


@blp.route("/refresh")
class RefreshView(MethodView):
    """Renouvelle l'access token via le refresh token."""

    decorators = [jwt_required(refresh=True)]

    @blp.response(200, AccessTokenSchema, description="Nouvel access token.")
    def post(self):
        """Émet un nouvel access token (nécessite le refresh token en Bearer)."""
        identity = get_jwt_identity()
        return {"access_token": create_access_token(identity=identity)}


@blp.route("/me")
class MeView(MethodView):
    """Consultation et mise à jour du profil de l'utilisateur connecté."""

    decorators = [jwt_required()]

    @blp.response(200, UserSchema, description="Profil de l'utilisateur.")
    def get(self):
        """Retourne le profil complet de l'utilisateur authentifié."""
        return current_user().to_dict()

    @blp.arguments(UpdateProfileSchema, location="json")
    @blp.response(200, UserSchema, description="Profil mis à jour.")
    @blp.alt_response(409, description="Email déjà utilisé par un autre compte.")
    @blp.alt_response(422, description="Données invalides.")
    def patch(self, args: dict):
        """
        Met à jour le profil de l'utilisateur.

        Seuls les champs fournis sont modifiés (PATCH sémantique).
        """
        user = current_user()

        if "email" in args and args["email"] != user.email:
            if User.query.filter_by(email=args["email"]).first():
                abort(409, message="Cet email est déjà utilisé.")
            user.email = args["email"]

        for field in ("first_name", "last_name", "phone"):
            if field in args:
                setattr(user, field, args[field])

        if "password" in args:
            user.set_password(args["password"])

        db.session.commit()
        return user.to_dict()
