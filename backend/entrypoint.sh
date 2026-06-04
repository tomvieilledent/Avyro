#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "import psycopg2, os; psycopg2.connect(os.environ['DATABASE_URL'])" 2>/dev/null; do
  sleep 1
done
echo "Database ready."

# Crée les tables si elles n'existent pas (idempotent, fiable).
python -c "import app.models; from app import create_app; from app.extensions import db; a=create_app(); c=a.app_context(); c.push(); db.create_all(); print('Tables prêtes')"

exec "$@"
