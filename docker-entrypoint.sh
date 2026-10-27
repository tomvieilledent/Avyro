#!/bin/sh
set -e
# Migrations avant le démarrage (la DB est healthy grâce à depends_on)
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  RUN_SCHEDULER=0 flask db upgrade
fi
exec "$@"
