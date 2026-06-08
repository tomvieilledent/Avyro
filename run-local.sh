#!/usr/bin/env bash
# Lance Avyro en local SANS Docker.
# Un seul process gunicorn sert le frontend + l'API sur http://localhost:8080.
# Usage : ./run-local.sh   (depuis la racine du projet)
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

# ── 1. Dépendances Python ────────────────────────────────────────────────────
echo "==> Backend : dépendances Python"
cd "$ROOT/backend"
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -r requirements.txt

# ── 2. Frontend : recompilation Tailwind CSS (optionnel) ─────────────────────
echo "==> Frontend : Tailwind CSS"
cd "$ROOT/frontend"
if command -v npm >/dev/null 2>&1; then
  npm install --silent
  npm run build
  echo "   CSS compilé."
else
  echo "   (npm absent — dist/styles.css existant conservé)"
fi

# ── 3. Base de données SQLite ─────────────────────────────────────────────────
echo "==> Base de données SQLite"
cd "$ROOT/backend"
export FLASK_ENV=development
export DATABASE_URL="sqlite:///$ROOT/backend/dev.db"
export SECRET_KEY="dev-change-me"
export JWT_SECRET_KEY="dev-jwt-secret-please-change-me-32bytes"
export RUN_SCHEDULER=0
export SERVE_FRONTEND="$ROOT/frontend"

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
