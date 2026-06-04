#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "import psycopg2, os; psycopg2.connect(os.environ['DATABASE_URL'])" 2>/dev/null; do
  sleep 1
done
echo "Database ready."

# Initialise les migrations au premier démarrage, sinon applique les migrations.
if [ ! -d "migrations/versions" ]; then
  flask db init
  flask db migrate -m "init"
fi
flask db upgrade

exec "$@"
