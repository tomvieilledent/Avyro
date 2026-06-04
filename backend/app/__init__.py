import os

from flask import Flask, jsonify

from .config import config_by_name
from .extensions import db, migrate, jwt, cors


def create_app(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    from . import models  # noqa: F401  (register models)

    from .api.auth import bp as auth_bp
    from .api.companies import bp as companies_bp
    from .api.trainings import bp as trainings_bp
    from .api.bookings import bp as bookings_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(companies_bp, url_prefix="/api/companies")
    app.register_blueprint(trainings_bp, url_prefix="/api/trainings")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    register_cli(app)
    register_error_handlers(app)

    # Scheduler in-process (à n'activer que sur UNE instance backend).
    if os.getenv("RUN_SCHEDULER") == "1":
        from .services.maintenance import start_scheduler

        start_scheduler(app)

    return app


def register_cli(app):
    @app.cli.command("maintenance")
    def maintenance():
        """Génère les comptes rendus dus et purge les formations démarrées."""
        from .services.maintenance import run_maintenance

        run_maintenance(app)
        print("Maintenance terminée.")


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="bad_request", message=str(e.description)), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(error="unauthorized", message=str(e.description)), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found", message="Resource not found"), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify(error="unprocessable", message=str(e.description)), 422
