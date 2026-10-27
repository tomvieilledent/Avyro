# syntax=docker/dockerfile:1

# ── Étape 1 : build du frontend (Vite/React) ─────────────────────────────────
FROM node:22.11-alpine3.20 AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Étape 2 : image d'exécution (Flask + Gunicorn) ───────────────────────────
FROM python:3.12.7-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=wsgi.py \
    SERVE_FRONTEND=/app/frontend/dist \
    HTTP_PORT=8080

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
COPY --from=frontend /frontend/dist /app/frontend/dist
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh \
 && chown -R app:app /app

USER app
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/api/health' % os.getenv('HTTP_PORT','8080'), timeout=4)" || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
# Un seul worker (scheduler APScheduler dans ce process), voir docker-compose.yml
CMD ["sh", "-c", "exec gunicorn -b 0.0.0.0:${HTTP_PORT} -k gthread -w ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-4} --timeout 120 wsgi:app"]
