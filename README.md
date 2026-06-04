# Avyro

Webapp de mutualisation de formations : une structure publie ses places
restantes, d'autres (pro ou particuliers) les réservent pour partager les coûts.

## Stack

- **Backend** : Python / Flask REST API, SQLAlchemy, Flask-Migrate, JWT
- **Base de données** : PostgreSQL
- **Frontend** : HTML + Tailwind CSS + JS vanilla, servi par nginx
- **Orchestration** : Docker Compose

## Architecture

```
Avyro/
├── docker-compose.yml            # db + backend + frontend
├── docker-compose.override.yml   # surcharge dev (hot-reload)
├── .env.example
├── backend/
│   ├── app/
│   │   ├── __init__.py           # app factory
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/               # Company, User, Training, Booking
│   │   ├── schemas/              # validation Marshmallow
│   │   ├── api/                  # blueprints REST (auth, trainings, bookings, companies)
│   │   └── utils/
│   ├── tests/
│   ├── Dockerfile
│   └── wsgi.py
└── frontend/
    ├── *.html                    # landing, login, register, dashboard
    ├── src/                      # api.js, dashboard.js, input.css
    ├── tailwind.config.js
    ├── Dockerfile                # build Tailwind -> nginx
    └── nginx.conf                # proxy /api -> backend
```

## Démarrage

```bash
cp .env.example .env
docker compose up --build
```

- Application : http://localhost:8080
- API : http://localhost:8080/api (le backend n'est pas exposé directement,
  tout passe par le 8080)

Les migrations sont appliquées automatiquement au démarrage du backend.

## API (principaux endpoints)

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/register` | Crée structure + compte admin |
| POST | `/api/auth/login` | Connexion (JWT) |
| GET | `/api/auth/me` | Profil courant |
| GET/POST | `/api/trainings` | Catalogue / publier une formation |
| PATCH/DELETE | `/api/trainings/<id>` | Modifier / supprimer (propriétaire) |
| GET/POST | `/api/bookings` | Mes réservations / réserver des places |
| GET | `/api/bookings/incoming` | Demandes reçues sur mes formations |
| PATCH | `/api/bookings/<id>` | Confirmer / refuser |

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Modèle de données

- **Company** : structure (pro ou particulier), possède des users.
- **User** : compte rattaché à une Company (rôle admin/member).
- **Training** : formation publiée par une Company, places totales et places
  mutualisées (`shared_seats`).
- **Booking** : réservation de places par une autre Company (pending →
  confirmed/cancelled).
