"""
Configuration Avyro.

Trois environnements : development (SQLite local), testing (SQLite in-memory),
production (PostgreSQL). Sélection via la variable d'env FLASK_ENV.
"""
import os
from datetime import timedelta


class Config:
    # ── Sécurité ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "30"))
    )

    # ── Base de données ───────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://avyro:avyro@db:5432/avyro"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Relance la connexion si elle est périmée dans le pool
        "pool_pre_ping": True,
        # Recycle les connexions toutes les 5 minutes
        "pool_recycle": 300,
    }

    # ── OpenAPI / Swagger UI (flask-smorest) ──────────────────────────────────
    API_TITLE = "Avyro API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    # Tous les endpoints de la spec sont préfixés par /api
    OPENAPI_URL_PREFIX = "/api"
    # Swagger UI disponible à  /api/docs
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    # Spec JSON disponible à /api/openapi.json
    OPENAPI_JSON_PATH = "openapi.json"
    API_SPEC_OPTIONS = {
        "info": {
            "description": (
                "API REST Avyro — mutualisation de formations (Avyro Training) "
                "et de salles de réunion (Avyro Room).\n\n"
                "Toutes les routes protégées nécessitent un Bearer JWT obtenu "
                "via `POST /api/auth/login`. Les tokens expirent au bout de 30 min ; "
                "utilisez `POST /api/auth/refresh` pour en obtenir un nouveau."
            ),
            "contact": {"email": "contact@avyro.app"},
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
        # Toutes les routes sont protégées par défaut ;
        # les routes publiques overrident avec security=[]
        "security": [{"bearerAuth": []}],
    }

    # ── Rate limiting (flask-limiter) ─────────────────────────────────────────
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    # Désactivé en test ; activé en prod
    RATELIMIT_ENABLED = True

    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    # Limites désactivées en dev pour ne pas gêner le développement
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Tokens longue durée pour les tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
