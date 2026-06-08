#!/usr/bin/env bash
# Lance Avyro en local SANS Docker : un seul process gunicorn sert
# le frontend + l'API sur http://localhost:8080 (base SQLite).
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "==> Backend : dépendances Python"
cd "$ROOT/backend"
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -r requirements.txt

echo "==> Frontend : build Tailwind CSS"
cd "$ROOT/frontend"
if command -v npm >/dev/null 2>&1; then
  npm install --silent
  npm run build
else
  echo "   (npm absent : CSS non recompilé. Le site marche mais sans styles si dist/ est vide.)"
fi

echo "==> Base de données (SQLite) + tables"
cd "$ROOT/backend"
export FLASK_ENV=development
export DATABASE_URL="sqlite:///$ROOT/backend/dev.db"
export SECRET_KEY="dev-change-me"
export JWT_SECRET_KEY="dev-jwt-secret-please-change-me-32bytes"
export RUN_SCHEDULER=1
export SCHEDULER_INTERVAL_MINUTES=5
export SERVE_FRONTEND="$ROOT/frontend"
python -c "import app.models; from app import create_app; from app.extensions import db; a=create_app(); c=a.app_context(); c.push(); db.create_all(); print('   tables OK')"

echo "==> Démarrage sur http://localhost:8080  (Ctrl+C pour arrêter)"
exec gunicorn -b 0.0.0.0:8080 -k gthread -w 1 --threads 8 --timeout 120 wsgi:app
