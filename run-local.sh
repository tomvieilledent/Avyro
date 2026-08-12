#!/usr/bin/env bash
# Lance Avyro en local SANS Docker.
# Un seul process gunicorn sert le frontend (build Vite/React) + l'API sur
# http://localhost:8080.
# Usage : ./run-local.sh   (depuis la racine du projet)
#
# Pour développer le frontend avec rechargement à chaud (React + Vite) :
#   1. Lancer le backend seul (voir étapes 1/3/4 ci-dessous, sans le build
#      frontend), ou simplement laisser ce script tourner dans un terminal.
#   2. Dans un second terminal : cd frontend && npm run dev
#      → http://localhost:5173, les appels /api/* sont relayés vers le
#      backend Flask sur :8080 (voir frontend/vite.config.js).
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

# ── 1. Dépendances Python ────────────────────────────────────────────────────
echo "==> Backend : dépendances Python"
cd "$ROOT/backend"
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -r requirements.txt

# ── 2. Frontend : build Vite (React) ──────────────────────────────────────────
echo "==> Frontend : build Vite"
cd "$ROOT/frontend"
if command -v npm >/dev/null 2>&1; then
  npm install --silent
  npm run build
  echo "   Frontend compilé dans frontend/dist/."
else
  echo "   (npm absent — frontend/dist existant conservé, sinon Flask n'aura rien à servir)"
fi

# ── 3. Base de données SQLite ─────────────────────────────────────────────────
echo "==> Base de données SQLite"
cd "$ROOT/backend"
export FLASK_ENV=development
export DATABASE_URL="sqlite:///$ROOT/backend/dev.db"
export SECRET_KEY="dev-change-me"
export JWT_SECRET_KEY="dev-jwt-secret-please-change-me-32bytes"
export RUN_SCHEDULER=0
export SERVE_FRONTEND="$ROOT/frontend/dist"

python -c "
from app import create_app
from app.extensions import db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('   tables OK')
"

# ── 4. Démarrage ──────────────────────────────────────────────────────────────
echo ""
echo "==> Avyro démarre sur http://localhost:8080"
echo "    Swagger UI : http://localhost:8080/api/docs"
echo "    Ctrl+C pour arrêter"
echo ""
exec gunicorn -b 0.0.0.0:8080 -k gthread -w 1 --threads 4 --timeout 120 wsgi:app
