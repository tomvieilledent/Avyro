"""
Point d'entrée WSGI.

Démarrage gunicorn :
    gunicorn wsgi:app --bind 0.0.0.0:8080

Démarrage développement (Flask CLI via .flaskenv) :
    flask run

La variable FLASK_ENV est lue par create_app ; valeur par défaut : 'production'
(fail-safe : on préfère le mode le plus restrictif en cas d'oubli).
"""
import os

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    port = int(os.getenv("HTTP_PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
