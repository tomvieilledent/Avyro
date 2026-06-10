"""
Routes Room : CRUD salles de réunion mutualisées.
Préfixe : /api/rooms
"""
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort

from app.extensions import db
from app.models import Room
from app.schemas import (
    RoomCreateSchema,
    RoomUpdateSchema,
    RoomQuerySchema,
    RoomSchema,
    RoomReportSchema,
    MessageSchema,
)
from app.utils.auth import current_user, current_user_optional
from app.utils.geo import apply_geo_filter

blp = Blueprint(
    "rooms",
    __name__,
    url_prefix="/api/rooms",
    description="Gestion des salles de réunion (Avyro Room).",
)


@blp.route("/reports")
class RoomReportsView(MethodView):
    decorators = [jwt_required()]

    @blp.arguments(RoomQuerySchema, location="query")
    @blp.response(200, RoomReportSchema(many=True))
    def get(self, args: dict):
        """Liste live des occupants confirmés pour chaque salle du provider."""
        user = current_user()
        rooms = (
            Room.query
            .filter_by(provider_id=user.company_id)
            .order_by(Room.starts_at.asc())
            .all()
        )
        return [
            {
                "room_id": r.id,
                "room_title": r.title,
                "starts_at": r.starts_at.isoformat(),
                "total_seats": r.booked_seats,
                "attendees": r.attendees(),
            }
            for r in rooms
        ]


@blp.route("")
class RoomListView(MethodView):
    decorators = [jwt_required(optional=True)]

    @blp.arguments(RoomQuerySchema, location="query")
    @blp.response(200, RoomSchema(many=True))
    def get(self, args: dict):
        """Catalogue des salles disponibles ou mes salles (mine=true)."""
        user = current_user_optional()
        if args["mine"]:
            if user is None:
                return []
            query = Room.query.filter_by(provider_id=user.company_id)
        else:
            query = Room.query.filter_by(status="open")
        if args.get("q"):
            q = f"%{args['q']}%"
            query = query.filter(
                Room.title.ilike(q)
                | Room.location.ilike(q)
                | Room.description.ilike(q)
            )
        if args.get("date_from"):
            from datetime import datetime
            query = query.filter(Room.starts_at >= datetime.combine(args["date_from"], datetime.min.time()))
        if args.get("date_to"):
            from datetime import datetime
            query = query.filter(Room.starts_at <= datetime.combine(args["date_to"], datetime.max.time()))
        if args.get("price_max") is not None:
            query = query.filter(Room.price_per_seat <= args["price_max"])
        if args.get("seats_min") is not None:
            query = query.filter(Room.shared_seats - Room.booked_seats >= args["seats_min"])
        if args.get("remote_only"):
            query = query.filter(Room.is_remote == True)
        items = [r.to_dict() for r in query.order_by(Room.starts_at.asc()).all()]
        if args.get("tag"):
            items = [i for i in items if args["tag"] in (i.get("tags") or [])]
        if args.get("lat") is not None and args.get("lng") is not None:
            items = apply_geo_filter(items, args["lat"], args["lng"], args["radius"])
        return items

    @blp.arguments(RoomCreateSchema, location="json")
    @blp.response(201, RoomSchema)
    def post(self, args: dict):
        """Publie une nouvelle salle de réunion."""
        user = current_user()
        if not user.company.siret:
            abort(403, message="Un numéro SIRET/SIREN est requis pour publier une salle. Renseignez-le dans votre profil.")
        tags = args.pop("tags", None)
        room = Room(provider_id=user.company_id, **args)
        room.tags = tags
        db.session.add(room)
        db.session.commit()
        return room.to_dict()


@blp.route("/<int:room_id>")
class RoomDetailView(MethodView):
    decorators = [jwt_required()]

    @blp.response(200, RoomSchema)
    def get(self, room_id: int):
        return db.get_or_404(Room, room_id).to_dict()

    @blp.arguments(RoomUpdateSchema, location="json")
    @blp.response(200, RoomSchema)
    def patch(self, args: dict, room_id: int):
        """Met à jour une salle (provider uniquement)."""
        room = db.get_or_404(Room, room_id)
        if room.provider_id != current_user().company_id:
            abort(403, message="Vous n'êtes pas le provider de cette salle.")
        tags = args.pop("tags", None)
        for key, value in args.items():
            setattr(room, key, value)
        if tags is not None:
            room.tags = tags
        db.session.commit()
        return room.to_dict()

    @blp.response(200, MessageSchema)
    def delete(self, room_id: int):
        """Supprime une salle (provider uniquement)."""
        room = db.get_or_404(Room, room_id)
        if room.provider_id != current_user().company_id:
            abort(403, message="Vous n'êtes pas le provider de cette salle.")
        db.session.delete(room)
        db.session.commit()
        return {"message": "Supprimé."}
