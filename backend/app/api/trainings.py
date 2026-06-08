"""
Routes Training : CRUD formations et salles, rapports d'inscrits.
Préfixe : /api/trainings

Les formations (kind='training') et les salles (kind='room') partagent
exactement le même workflow — seul le paramètre `kind` les distingue.
"""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from app.extensions import db
from app.models import Training
from app.schemas import (
    TrainingCreateSchema,
    TrainingUpdateSchema,
    TrainingQuerySchema,
    TrainingSchema,
    TrainingReportSchema,
    MessageSchema,
)
from app.utils.auth import current_user

blp = Blueprint(
    "trainings",
    __name__,
    url_prefix="/api/trainings",
    description="Gestion des formations (Avyro Training) et salles (Avyro Room).",
)


@blp.route("/reports")
class TrainingReportsView(MethodView):
    """
    Rapports live des inscrits pour chaque formation/salle du provider.
    Route déclarée avant `/<int:training_id>` pour que Flask ne confonde pas
    le segment 'reports' avec un entier.
    """

    decorators = [jwt_required()]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, TrainingReportSchema(many=True), description="Liste des rapports.")
    def get(self, args: dict):
        """
        Retourne la liste live des inscrits confirmés pour chaque Training
        proposée par la Company de l'utilisateur connecté.
        """
        user = current_user()
        trainings = (
            Training.query
            .filter_by(provider_id=user.company_id, kind=args["kind"])
            .order_by(Training.starts_at.asc())
            .all()
        )
        return [
            {
                "training_id": t.id,
                "training_title": t.title,
                "starts_at": t.starts_at.isoformat(),
                "total_seats": t.booked_seats,
                "attendees": t.attendees(),
            }
            for t in trainings
        ]


@blp.route("")
class TrainingListView(MethodView):
    """Liste et création de formations/salles."""

    decorators = [jwt_required()]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, TrainingSchema(many=True), description="Liste des formations/salles.")
    def get(self, args: dict):
        """
        Retourne la liste des formations ou salles.

        - Par défaut : catalogue public (status=open) trié par date.
        - `mine=true` : uniquement celles proposées par la Company de l'utilisateur.
        - `q=texte` : filtre par titre (insensible à la casse).
        - `kind=room` : bascule sur les salles de réunion.
        """
        kind = args["kind"]
        query = (
            Training.query.filter_by(provider_id=current_user().company_id, kind=kind)
            if args["mine"]
            else Training.query.filter_by(status="open", kind=kind)
        )

        if args.get("q"):
            query = query.filter(Training.title.ilike(f"%{args['q']}%"))

        trainings = query.order_by(Training.starts_at.asc()).all()
        return [t.to_dict() for t in trainings]

    @blp.arguments(TrainingCreateSchema, location="json")
    @blp.response(201, TrainingSchema, description="Formation/salle créée.")
    @blp.alt_response(422, description="Données invalides.")
    def post(self, args: dict):
        """
        Publie une nouvelle formation ou salle de réunion.

        La Company provider est déduite automatiquement du token JWT.
        """
        user = current_user()
        training = Training(provider_id=user.company_id, **args)
        db.session.add(training)
        db.session.commit()
        return training.to_dict()


@blp.route("/<int:training_id>")
class TrainingDetailView(MethodView):
    """Consultation, modification et suppression d'une formation/salle."""

    decorators = [jwt_required()]

    @blp.response(200, TrainingSchema, description="Détail de la formation/salle.")
    @blp.alt_response(404, description="Formation/salle introuvable.")
    def get(self, training_id: int):
        """Retourne les détails d'une formation ou salle par son id."""
        training = db.get_or_404(Training, training_id)
        return training.to_dict()

    @blp.arguments(TrainingUpdateSchema, location="json")
    @blp.response(200, TrainingSchema, description="Formation/salle mise à jour.")
    @blp.alt_response(403, description="Vous n'êtes pas le provider de cette formation.")
    @blp.alt_response(404, description="Formation/salle introuvable.")
    @blp.alt_response(422, description="Données invalides.")
    def patch(self, args: dict, training_id: int):
        """
        Met à jour une formation ou salle.

        Réservé au provider (Company propriétaire). PATCH sémantique :
        seuls les champs fournis sont modifiés.
        """
        training = db.get_or_404(Training, training_id)
        user = current_user()

        if training.provider_id != user.company_id:
            abort(403, message="Vous n'êtes pas le provider de cette formation.")

        for key, value in args.items():
            setattr(training, key, value)

        db.session.commit()
        return training.to_dict()

    @blp.response(200, MessageSchema, description="Formation/salle supprimée.")
    @blp.alt_response(403, description="Vous n'êtes pas le provider de cette formation.")
    @blp.alt_response(404, description="Formation/salle introuvable.")
    def delete(self, training_id: int):
        """
        Supprime une formation ou salle (cascade sur les bookings associés).

        Réservé au provider.
        """
        training = db.get_or_404(Training, training_id)
        user = current_user()

        if training.provider_id != user.company_id:
            abort(403, message="Vous n'êtes pas le provider de cette formation.")

        db.session.delete(training)
        db.session.commit()
        return {"message": "Supprimé."}
