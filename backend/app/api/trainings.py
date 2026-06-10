"""
Routes Training : CRUD formations mutualisées.
Préfixe : /api/trainings
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
from app.utils.auth import current_user, current_user_optional
from app.utils.geo import apply_geo_filter

blp = Blueprint(
    "trainings",
    __name__,
    url_prefix="/api/trainings",
    description="Gestion des formations (Avyro Training).",
)


@blp.route("/reports")
class TrainingReportsView(MethodView):
    decorators = [jwt_required()]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, TrainingReportSchema(many=True))
    def get(self, args: dict):
        """Inscrits confirmés pour chaque formation du provider."""
        user = current_user()
        trainings = (
            Training.query
            .filter_by(provider_id=user.company_id)
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
    decorators = [jwt_required(optional=True)]

    @blp.arguments(TrainingQuerySchema, location="query")
    @blp.response(200, TrainingSchema(many=True))
    def get(self, args: dict):
        """Catalogue des formations ou mes formations (mine=true)."""
        user = current_user_optional()
        if args["mine"]:
            if user is None:
                return []
            query = Training.query.filter_by(provider_id=user.company_id)
        else:
            query = Training.query.filter_by(status="open")
        if args.get("q"):
            q = f"%{args['q']}%"
            query = query.filter(
                Training.title.ilike(q)
                | Training.location.ilike(q)
                | Training.description.ilike(q)
            )
        if args.get("date_from"):
            from datetime import datetime
            query = query.filter(Training.starts_at >= datetime.combine(args["date_from"], datetime.min.time()))
        if args.get("date_to"):
            from datetime import datetime
            query = query.filter(Training.starts_at <= datetime.combine(args["date_to"], datetime.max.time()))
        if args.get("price_max") is not None:
            query = query.filter(Training.price_per_seat <= args["price_max"])
        if args.get("seats_min") is not None:
            query = query.filter(Training.shared_seats - Training.booked_seats >= args["seats_min"])
        if args.get("remote_only"):
            query = query.filter(Training.is_remote == True)
        items = [t.to_dict() for t in query.order_by(Training.starts_at.asc()).all()]
        if args.get("tag"):
            items = [i for i in items if args["tag"] in (i.get("tags") or [])]
        if args.get("lat") is not None and args.get("lng") is not None:
            items = apply_geo_filter(items, args["lat"], args["lng"], args["radius"])
        return items

    @blp.arguments(TrainingCreateSchema, location="json")
    @blp.response(201, TrainingSchema)
    def post(self, args: dict):
        """Publie une nouvelle formation."""
        user = current_user()
        if not user.company.siret:
            abort(403, message="Un numéro SIRET/SIREN est requis pour publier une formation. Renseignez-le dans votre profil.")
        tags = args.pop("tags", None)
        training = Training(provider_id=user.company_id, **args)
        training.tags = tags
        db.session.add(training)
        db.session.commit()
        return training.to_dict()


@blp.route("/<int:training_id>")
class TrainingDetailView(MethodView):
    decorators = [jwt_required()]

    @blp.response(200, TrainingSchema)
    def get(self, training_id: int):
        return db.get_or_404(Training, training_id).to_dict()

    @blp.arguments(TrainingUpdateSchema, location="json")
    @blp.response(200, TrainingSchema)
    def patch(self, args: dict, training_id: int):
        """Met à jour une formation (provider uniquement)."""
        training = db.get_or_404(Training, training_id)
        if training.provider_id != current_user().company_id:
            abort(403, message="Vous n'êtes pas le provider de cette formation.")
        tags = args.pop("tags", None)
        for key, value in args.items():
            setattr(training, key, value)
        if tags is not None:
            training.tags = tags
        db.session.commit()
        return training.to_dict()

    @blp.response(200, MessageSchema)
    def delete(self, training_id: int):
        """Supprime une formation (provider uniquement)."""
        training = db.get_or_404(Training, training_id)
        if training.provider_id != current_user().company_id:
            abort(403, message="Vous n'êtes pas le provider de cette formation.")
        db.session.delete(training)
        db.session.commit()
        return {"message": "Supprimé."}
