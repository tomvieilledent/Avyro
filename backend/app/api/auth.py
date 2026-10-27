"""
Routes d'authentification : inscription, connexion, refresh token, profil.
Préfixe : /api/auth
"""
import logging

from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    jwt_required,
    get_jwt_identity,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError
from flask_smorest import Blueprint, abort
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import User, Company, Booking
from app.schemas import (
    RegisterSchema,
    LoginSchema,
    UpdateProfileSchema,
    UserSchema,
    ProfileUpdateResponseSchema,
    TokenResponseSchema,
    AccessTokenSchema,
    AcceptInviteSchema,
    InviteInfoQuerySchema,
    InviteInfoSchema,
    MessageSchema,
    LogoutSchema,
)
from app.utils.jwt_handlers import revoke_token
from app.utils.auth import current_user, db_get_user, _identity_to_id
from app.utils.tokens import InvalidInviteToken, read_invite_token

logger = logging.getLogger(__name__)

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
    claims = {"tv": user.token_version or 0}
    return {
        "access_token": create_access_token(identity=identity, additional_claims=claims),
        "refresh_token": create_refresh_token(identity=identity, additional_claims=claims),
        "user": user.to_dict(),
    }


def _email_taken(email: str, exclude_id: "int | None" = None) -> bool:
    """Unicité insensible à la casse (couvre aussi d'éventuelles lignes legacy)."""
    q = User.query.filter(func.lower(User.email) == email.lower())
    if exclude_id is not None:
        q = q.filter(User.id != exclude_id)
    return q.first() is not None


def _commit_or_conflict(message: str) -> None:
    """Commit ; en cas de violation d'unicité (course) : rollback + 409."""
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        logger.warning("IntegrityError lors d'un commit de compte")
        abort(409, message=message)


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
        if _email_taken(args["email"]):
            abort(409, message="Cet email est déjà utilisé.")

        explicit_name = (args.get("company_name") or "").strip()
        company_name = explicit_name or (
            f"{args['first_name']} {args['last_name']}".strip()
        )
        company = Company(
            name=company_name,
            kind="pro" if explicit_name else "private",
        )
        if args.get("tags"):
            company.tags = args["tags"]
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
        _commit_or_conflict("Cet email est déjà utilisé.")

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
        user = User.query.filter(
            func.lower(User.email) == args["email"].lower()
        ).first()
        if not user or not user.check_password(args["password"]):
            # Message volontairement vague pour ne pas révéler l'existence du compte
            abort(401, message="Email ou mot de passe incorrect.")
        return _build_token_response(user)


@blp.route("/refresh")
class RefreshView(MethodView):
    """Renouvelle l'access token via le refresh token."""

    decorators = [limiter.limit("30 per minute"), jwt_required(refresh=True)]

    @blp.response(200, AccessTokenSchema, description="Nouvel access token.")
    @blp.alt_response(401, description="Compte inexistant ou token invalide.")
    def post(self):
        """Émet un nouvel access token (nécessite le refresh token en Bearer)."""
        identity = get_jwt_identity()
        user_id = _identity_to_id(identity)
        user = db_get_user(user_id) if user_id is not None else None
        if user is None:
            abort(401, message="Session expirée, reconnectez-vous.")
        return {
            "access_token": create_access_token(
                identity=identity,
                additional_claims={"tv": user.token_version or 0},
            )
        }


@blp.route("/logout")
class LogoutView(MethodView):
    """Révoque le token présenté (et, si fourni, le refresh token associé)."""

    decorators = [jwt_required(verify_type=False)]

    @blp.arguments(LogoutSchema, location="json")
    @blp.response(200, MessageSchema, description="Session terminée.")
    @blp.alt_response(400, description="Refresh token invalide.")
    def post(self, args: dict):
        """Déconnexion : le token Bearer et le refresh token fourni sont révoqués."""
        payload = get_jwt()
        refresh_payload = None
        if args.get("refresh_token"):
            try:
                refresh_payload = decode_token(args["refresh_token"])
            except (JWTExtendedException, PyJWTError):
                abort(400, message="Refresh token invalide.")
            if (
                refresh_payload.get("type") != "refresh"
                or refresh_payload.get("sub") != payload.get("sub")
            ):
                abort(400, message="Refresh token invalide.")
        revoke_token(payload)
        if refresh_payload is not None:
            revoke_token(refresh_payload)
        else:
            # Refresh token inconnu : invalide tous les refresh tokens existants
            user = current_user()
            user.token_version = (user.token_version or 0) + 1
        db.session.commit()
        return {"message": "Déconnecté."}


@blp.route("/me")
class MeView(MethodView):
    """Consultation et mise à jour du profil de l'utilisateur connecté."""

    decorators = [jwt_required()]

    @blp.response(200, UserSchema, description="Profil de l'utilisateur.")
    def get(self):
        """Retourne le profil complet de l'utilisateur authentifié."""
        return current_user().to_dict()

    @blp.arguments(UpdateProfileSchema, location="json")
    @blp.response(
        200, ProfileUpdateResponseSchema,
        description="Profil mis à jour. Si le mot de passe change, la réponse "
                    "contient aussi `access_token` et `refresh_token` neufs.",
    )
    @blp.alt_response(409, description="Email déjà utilisé par un autre compte.")
    @blp.alt_response(422, description="Données invalides.")
    def patch(self, args: dict):
        """
        Met à jour le profil de l'utilisateur.

        Seuls les champs fournis sont modifiés (PATCH sémantique).
        """
        user = current_user()

        if "email" in args and args["email"] != user.email:
            if _email_taken(args["email"], exclude_id=user.id):
                abort(409, message="Cet email est déjà utilisé.")
            user.email = args["email"]

        for field in ("first_name", "last_name", "phone"):
            if field in args:
                setattr(user, field, args[field])

        password_changed = "password" in args
        if password_changed:
            user.set_password(args["password"])

        _commit_or_conflict("Cet email est déjà utilisé.")
        if password_changed:
            # token_version incrémenté : les anciens tokens sont invalides,
            # on réémet une paire neuve pour la session courante.
            tokens = _build_token_response(user)
            return {
                **user.to_dict(),
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
            }
        return user.to_dict()

    @blp.response(200, MessageSchema, description="Compte supprimé.")
    def delete(self):
        """
        Droit à l'effacement (RGPD Art. 17).

        Supprime le compte utilisateur. Si l'utilisateur est le dernier
        admin de sa Company, supprime également la Company et toutes ses données
        (formations, salles, réservations) par cascade SQLAlchemy.
        """
        user = current_user()
        company = user.company
        is_last_admin = (
            user.role == "admin"
            and not User.query.filter(
                User.company_id == company.id,
                User.role == "admin",
                User.id != user.id,
            ).first()
        )
        # Anonymise le demandeur des réservations qui survivent à la suppression
        db.session.execute(
            update(Booking)
            .where(Booking.requested_by_id == user.id)
            .values(requested_by_id=None)
        )
        if is_last_admin:
            db.session.delete(company)  # cascade → supprime User aussi
        else:
            db.session.delete(user)
        revoke_token(get_jwt())
        db.session.commit()
        return {"message": "Compte supprimé conformément au droit à l'effacement."}


@blp.route("/me/export")
class MeExportView(MethodView):
    """Export des données personnelles (RGPD Art. 20 — portabilité)."""

    decorators = [jwt_required()]

    def get(self):
        """Retourne toutes les données personnelles de l'utilisateur (JSON)."""
        from flask import jsonify
        from app.models import Booking
        user = current_user()
        bookings = Booking.query.filter_by(requested_by_id=user.id).all()
        data = {
            "user": user.to_dict(),
            "company": user.company.to_dict(),
            "bookings": [b.to_dict() for b in bookings],
        }
        return jsonify(data)


@blp.route("/invite-info")
class InviteInfoView(MethodView):
    """Aperçu public d'une invitation (pré-remplissage du formulaire)."""

    decorators = [limiter.limit("20 per minute")]

    @blp.doc(security=[])
    @blp.arguments(InviteInfoQuerySchema, location="query")
    @blp.response(200, InviteInfoSchema)
    @blp.alt_response(400, description="Invitation invalide, expirée ou déjà utilisée.")
    def get(self, args: dict):
        """Retourne email, structure et rôle d'une invitation valide."""
        try:
            claims = read_invite_token(args["token"])
        except InvalidInviteToken:
            abort(400, message="Lien d'invitation invalide ou expiré.")
        email = claims["email"].strip().lower()
        company = db.session.get(Company, claims["company_id"])
        if company is None or _email_taken(email):
            abort(400, message="Lien d'invitation invalide ou expiré.")
        return {"email": email, "company_name": company.name, "role": claims["role"]}


@blp.route("/accept-invite")
class AcceptInviteView(MethodView):
    """Finalise la création de compte suite à une invitation."""

    decorators = [limiter.limit("10 per minute")]

    @blp.doc(security=[])
    @blp.arguments(AcceptInviteSchema, location="json")
    @blp.response(201, TokenResponseSchema)
    def post(self, args: dict):
        """Crée un compte membre via un token d'invitation (usage unique)."""
        try:
            claims = read_invite_token(args["token"])
        except InvalidInviteToken:
            abort(400, message="Lien d'invitation invalide ou expiré.")

        invite_email = claims["email"].strip().lower()
        # Usage unique : l'invitation est consommée dès que le compte existe
        if _email_taken(invite_email):
            abort(409, message="Un compte existe déjà avec cet email.")

        company = db.session.get(Company, claims["company_id"])
        if company is None:
            abort(400, message="Lien d'invitation invalide ou expiré.")

        user = User(
            email=invite_email,
            first_name=args["first_name"],
            last_name=args["last_name"],
            phone=args["phone"],
            role=claims["role"],
            company_id=company.id,
        )
        user.set_password(args["password"])
        db.session.add(user)
        _commit_or_conflict("Un compte existe déjà avec cet email.")
        return _build_token_response(user)
