"""
Factory Flask pour Avyro.

Pattern Application Factory : permet de créer plusieurs instances (test,
prod, dev) avec des configs différentes sans état global.

Swagger UI disponible à /api/docs une fois l'app lancée.
"""
import os

import click
from flask import Flask, jsonify

from .security import init_security
from .config import config_by_name, validate_production_config
from .extensions import db, migrate, jwt, cors, smorest, limiter


def create_app(config_name: str | None = None) -> Flask:
    """
    Crée et configure l'application Flask.

    Args:
        config_name: 'development', 'testing' ou 'production'.
                     Valeur par défaut : variable d'env FLASK_ENV (development).
    """
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    app.config["APP_ENV"] = config_name
    if config_name == "production":
        validate_production_config(app.config)

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    init_security(app)
    _register_error_handlers(app)

    # Optionnel : sert aussi le frontend statique (dev sans proxy nginx)
    frontend_dir = os.getenv("SERVE_FRONTEND")
    if frontend_dir:
        _register_frontend(app, frontend_dir)

    # Scheduler APScheduler (uniquement sur l'instance principale, pas en test)
    if os.getenv("RUN_SCHEDULER") == "1":
        from .services.maintenance import start_scheduler
        start_scheduler(app)

    return app


def _init_extensions(app: Flask) -> None:
    """Initialise toutes les extensions Flask avec l'app."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    # flask-smorest : OpenAPI 3.0 + Swagger UI
    smorest.init_app(app)

    # Import des modèles pour que SQLAlchemy les enregistre (nécessaire pour
    # create_all et les migrations Alembic)
    from . import models  # noqa: F401
    from .utils.jwt_handlers import register_jwt_handlers
    register_jwt_handlers()


def _register_blueprints(app: Flask) -> None:
    """Enregistre tous les blueprints API sur l'instance flask-smorest."""
    from .api.auth import blp as auth_blp
    from .api.companies import blp as companies_blp
    from .api.trainings import blp as trainings_blp
    from .api.rooms import blp as rooms_blp
    from .api.bookings import blp as bookings_blp
    from .api.geocode import blp as geocode_blp

    smorest.register_blueprint(auth_blp)
    smorest.register_blueprint(companies_blp)
    smorest.register_blueprint(trainings_blp)
    smorest.register_blueprint(rooms_blp)
    smorest.register_blueprint(bookings_blp)
    smorest.register_blueprint(geocode_blp)

    # Health check (hors Swagger, appelé par les load balancers)
    @app.get("/api/health")
    def health():
        return jsonify(status="ok", env=app.config.get("APP_ENV", "unknown"))


def _register_frontend(app: Flask, frontend_dir: str) -> None:
    """
    Sert le build SPA (Vite/React) depuis Python (dev sans nginx).
    En production, nginx peut aussi servir directement le dossier frontend/.

    Toute route qui ne correspond ni à /api/*, ni à un fichier statique
    existant (JS/CSS/images du build) retombe sur index.html : c'est
    react-router-dom qui résout la page côté client (fallback SPA).
    """
    from flask import send_from_directory, abort as flask_abort

    @app.route("/")
    def _index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def _static(path):
        if path.startswith("api/"):
            flask_abort(404)
        if os.path.isfile(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")


def _register_cli(app: Flask) -> None:
    """Commandes Flask CLI."""

    @app.cli.command("maintenance")
    def maintenance_cmd():
        """Lance manuellement la tâche de maintenance (rappels + purge)."""
        from .services.maintenance import run_maintenance
        run_maintenance(app)
        print("Maintenance terminée.")

    @app.cli.command("create-db")
    def create_db_cmd():
        """Crée toutes les tables (dev/test uniquement ; prod : flask db upgrade)."""
        if app.config.get("APP_ENV") == "production":
            raise click.ClickException(
                "create-db est interdit en production : utilisez `flask db upgrade`."
            )
        db.create_all()
        print("Tables créées.")


def _register_error_handlers(app: Flask) -> None:
    """
    Handlers d'erreur globaux.

    Maintient le format de réponse cohérent avec le frontend :
      - Erreurs de validation : {"error": "validation", "messages": {...}}
      - Autres erreurs       : {"error": "...", "message": "..."}

    flask-smorest remonte les erreurs de validation marshmallow en 422 avec
    e.data["messages"] = {"json": {...}} ; on aplatit ce niveau pour garder
    la compatibilité avec le frontend.
    """

    @app.errorhandler(400)
    def bad_request(e):
        data = getattr(e, "data", {})
        msg = data.get("message") or str(e.description)
        return jsonify(error="bad_request", message=msg), 400

    @app.errorhandler(401)
    def unauthorized(e):
        # flask-smorest stocke le message dans e.data
        data = getattr(e, "data", {})
        msg = data.get("message") or str(e.description)
        return jsonify(error="unauthorized", message=msg), 401

    @app.errorhandler(403)
    def forbidden(e):
        data = getattr(e, "data", {})
        msg = data.get("message") or str(e.description)
        return jsonify(error="forbidden", message=msg), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found", message="Ressource introuvable."), 404

    @app.errorhandler(502)
    def bad_gateway(e):
        data = getattr(e, "data", {})
        msg = data.get("message") or "Service amont indisponible."
        return jsonify(error="bad_gateway", message=msg), 502

    @app.errorhandler(409)
    def conflict(e):
        data = getattr(e, "data", {})
        msg = data.get("message") or str(e.description)
        return jsonify(error="conflict", message=msg), 409

    @app.errorhandler(422)
    def unprocessable(e):
        # flask-smorest wraps les erreurs marshmallow dans e.data["messages"]
        # Format marshmallow : {"json": {"field": ["msg"]}} ou {"query": {...}}
        data = getattr(e, "data", {})
        messages = data.get("messages", {})
        # Aplatit le niveau "json" / "query" pour compatibilité frontend
        if "json" in messages:
            messages = messages["json"]
        elif "query" in messages:
            messages = messages["query"]
        return jsonify(error="validation", messages=messages or str(e.description)), 422

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify(
            error="rate_limit",
            message="Trop de requêtes. Réessayez dans quelques instants.",
        ), 429

    @app.errorhandler(500)
    def internal_error(e):
        # Ne pas exposer les détails en prod
        app.logger.exception("Internal server error")
        return jsonify(error="internal_error", message="Erreur interne."), 500
