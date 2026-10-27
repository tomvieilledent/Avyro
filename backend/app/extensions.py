"""
Instances des extensions Flask (pas encore liées à une app).
Importées ici pour éviter les imports circulaires.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_smorest import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
# render_as_batch : ALTER TABLE compatibles SQLite (no-op sur PostgreSQL)
migrate = Migrate(render_as_batch=True)
jwt = JWTManager()
cors = CORS()
# Nommé 'smorest' pour éviter la collision avec le sous-package app/api/
smorest = Api()
# Clé de rate-limit = adresse IP du client
limiter = Limiter(key_func=get_remote_address)
