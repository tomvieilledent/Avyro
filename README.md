# Avyro

Webapp de mutualisation de formations : une structure publie ses places
restantes, d'autres (pro ou particuliers) les réservent pour partager les coûts.

## Stack

- **Backend** : Python / Flask REST API, SQLAlchemy, JWT
- **Base de données** : SQLite (local), PostgreSQL possible en prod
- **Frontend** : HTML + Tailwind CSS + JS vanilla
- Un seul process Gunicorn sert le frontend **et** l'API.

## Architecture

```
Avyro/
├── run-local.sh                  # lance toute l'app sur :8080
├── backend/
│   ├── app/
│   │   ├── __init__.py           # app factory (+ sert le frontend si SERVE_FRONTEND)
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/               # Company, User, Training, Booking
│   │   ├── schemas/              # validation Marshmallow
│   │   ├── api/                  # blueprints REST (auth, trainings, bookings, companies)
│   │   ├── services/             # mailer, maintenance (scheduler)
│   │   └── utils/
│   ├── tests/
│   └── wsgi.py
└── frontend/
    ├── *.html                    # landing, login, register, dashboard, profile
    ├── src/                      # api.js, dashboard.js, profile.js, input.css
    └── tailwind.config.js
```

## Démarrage (sans Docker)

```bash
./run-local.sh
```

Le script installe les dépendances Python, compile le CSS Tailwind (si `npm`
présent), crée la base SQLite et lance l'app sur **http://localhost:8080**
(frontend + API). `Ctrl+C` pour arrêter.

Pré-requis : `python3` (+ `node`/`npm` pour recompiler le CSS).

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
