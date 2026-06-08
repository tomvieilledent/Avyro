# Avyro — Plateforme de mutualisation

Plateforme de **mutualisation de formations** (*Avyro Training* — bleu) et de
**salles de réunion** (*Avyro Room* — vert). Les entreprises proposent leurs
places disponibles à d'autres structures qui peuvent les réserver en partageant
les coûts.

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework | Flask 3.x (Python 3.12) |
| ORM | SQLAlchemy 2.x via Flask-SQLAlchemy 3.x |
| Migrations | Alembic via Flask-Migrate |
| Auth | JWT — Flask-JWT-Extended |
| Doc API | OpenAPI 3.0 — flask-smorest + Swagger UI |
| Rate limit | flask-limiter |
| Emails | SMTP (APScheduler pour les rappels planifiés) |
| DB dev | SQLite |
| DB prod | PostgreSQL |
| Frontend | HTML + Tailwind CSS + JS vanilla |

---

## Structure du projet

```
Avyro/
├── run-local.sh                  # Lance toute l'app sur :8080 (sans Docker)
├── README.md
├── backend/
│   ├── wsgi.py                   # Point d'entrée WSGI (gunicorn)
│   ├── requirements.txt
│   ├── .flaskenv                 # FLASK_APP / FLASK_ENV pour `flask run`
│   └── app/
│       ├── __init__.py           # Application factory
│       ├── config.py             # Config dev / test / prod
│       ├── extensions.py         # Instances des extensions Flask
│       ├── models/               # Modèles SQLAlchemy
│       │   ├── mixins.py         # TimestampMixin (created_at / updated_at)
│       │   ├── company.py        # Company (entreprise ou particulier)
│       │   ├── user.py           # User (rattaché à une Company)
│       │   ├── training.py       # Training (formation OU salle, kind=discriminant)
│       │   └── booking.py        # Booking (demande de réservation)
│       ├── schemas/              # Schemas marshmallow (validation + doc OpenAPI)
│       │   ├── auth.py
│       │   ├── company.py
│       │   ├── training.py
│       │   └── booking.py
│       ├── api/                  # Routes HTTP (Flask MethodView + flask-smorest)
│       │   ├── auth.py           # /api/auth/*
│       │   ├── companies.py      # /api/companies/*
│       │   ├── trainings.py      # /api/trainings/*
│       │   └── bookings.py       # /api/bookings/*
│       ├── services/
│       │   ├── mailer.py         # Envoi d'emails (SMTP ou outbox fichier en dev)
│       │   └── maintenance.py    # Rappels planifiés + purge formations terminées
│       └── utils/
│           └── auth.py           # current_user(), admin_required
├── tests/
│   ├── conftest.py               # Fixtures pytest (app, client, helpers)
│   ├── test_auth.py              # 15 tests
│   ├── test_companies.py         # 6 tests
│   ├── test_trainings.py         # 16 tests
│   ├── test_bookings.py          # 15 tests
│   └── test_maintenance.py       # 6 tests — rappels email + purge
└── frontend/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── profile.html
    └── src/
        ├── api.js                # Client HTTP (fetch + gestion JWT)
        ├── dashboard.js          # Logique dashboard (catalog, bookings, etc.)
        └── profile.js            # Logique page profil
```

---

## Démarrage rapide (dev sans Docker)

```bash
# 1. Installer les dépendances Python
pip install -r backend/requirements.txt

# 2. Configurer l'environnement
export FLASK_ENV=development
export SERVE_FRONTEND=$(pwd)/frontend   # Flask sert aussi le frontend en dev

# 3. Créer la base de données SQLite
cd backend
flask create-db

# 4. Lancer le serveur
flask run --port 8080
# → http://localhost:8080        (frontend)
# → http://localhost:8080/api/docs  (Swagger UI)
```

Ou avec le script fourni :

```bash
./run-local.sh
```

---

## Documentation API interactive (Swagger UI)

```
http://localhost:8080/api/docs
```

Spec OpenAPI 3.0 JSON : `http://localhost:8080/api/openapi.json`

**Authentification dans Swagger :** cliquer sur *Authorize* et saisir uniquement
le token JWT (sans le préfixe `Bearer`).

---

## Endpoints

### Auth

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/api/auth/register` | — | Crée un compte + Company |
| POST | `/api/auth/login` | — | Connexion, retourne les tokens JWT |
| POST | `/api/auth/refresh` | Refresh JWT | Renouvelle l'access token |
| GET | `/api/auth/me` | JWT | Profil de l'utilisateur connecté |
| PATCH | `/api/auth/me` | JWT | Met à jour le profil |

### Companies

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/api/companies/me` | JWT | Company de l'utilisateur |
| PATCH | `/api/companies/me` | JWT (admin) | Met à jour la Company |
| GET | `/api/companies/<id>` | JWT | Consulte une Company par id |

### Formations & Salles

Paramètre `kind` : `training` (Avyro Training, défaut) ou `room` (Avyro Room).

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/api/trainings?kind=...` | JWT | Catalogue ouvert |
| GET | `/api/trainings?mine=true` | JWT | Mes publications |
| GET | `/api/trainings/reports` | JWT | Rapports inscrits live |
| POST | `/api/trainings` | JWT | Publie une formation ou salle |
| GET | `/api/trainings/<id>` | JWT | Détail |
| PATCH | `/api/trainings/<id>` | JWT (provider) | Modifie |
| DELETE | `/api/trainings/<id>` | JWT (provider) | Supprime (cascade bookings) |

### Réservations

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/api/bookings` | JWT | Mes réservations |
| GET | `/api/bookings/incoming` | JWT | Demandes reçues |
| POST | `/api/bookings` | JWT | Crée une demande (status=pending) |
| PATCH | `/api/bookings/<id>` | JWT (provider) | Confirme ou refuse |
| DELETE | `/api/bookings/<id>` | JWT (booker) | Annule (pending seulement) |

---

## Modèle de données

```
Company (1) ──── (N) User
    │
    │ as provider
    │
    └──── (N) Training (kind = 'training' | 'room')
                │
                └──── (N) Booking ──── Company (as booker)
                                  └─── User (requested_by)
```

### Cycle de vie — Training

```
open ──→ closed     (fermeture manuelle par le provider)
open ──→ cancelled  (annulation)
```

Les formations dont `ends_at` est dépassé sont **supprimées automatiquement**
par la tâche de maintenance (cascade sur les bookings).

### Cycle de vie — Booking

```
pending ──→ confirmed   (provider valide)
pending ──→ cancelled   (provider refuse OU booker annule)
```

Une réservation confirmée ne peut plus être annulée par le booker via l'API.

---

## Tests

```bash
cd backend

# Tous les tests (63 au total)
pytest

# Avec rapport de couverture
pytest --cov=app --cov-report=term-missing

# Suite ciblée
pytest tests/test_bookings.py -v
```

---

## Maintenance planifiée

Activée avec `RUN_SCHEDULER=1`. Deux tâches au même intervalle
(`SCHEDULER_INTERVAL_MINUTES`, défaut 60 min) :

1. **Rappels email** — envoie la liste des inscrits au provider 1 jour ouvré
   avant le début. Idempotent (UPDATE conditionnel, safe multi-workers).

2. **Purge** — supprime les formations terminées (`ends_at ≤ now`).

Lancement manuel :

```bash
flask maintenance
```

---

## Configuration

| Variable | Défaut | Description |
|----------|--------|-------------|
| `FLASK_ENV` | `production` | `development` \| `testing` \| `production` |
| `DATABASE_URL` | SQLite (dev) / PostgreSQL (prod) | URL de connexion |
| `SECRET_KEY` | *dev-secret* | **Changer en production** |
| `JWT_SECRET_KEY` | *dev-jwt* | **Changer en production** |
| `JWT_ACCESS_MINUTES` | `30` | Durée access token (min) |
| `JWT_REFRESH_DAYS` | `30` | Durée refresh token (jours) |
| `MAIL_SERVER` | — | Serveur SMTP (absent → outbox fichier) |
| `MAIL_PORT` | `587` | Port SMTP |
| `MAIL_FROM` | `no-reply@avyro.app` | Expéditeur |
| `RUN_SCHEDULER` | — | `1` pour activer le scheduler |
| `SCHEDULER_INTERVAL_MINUTES` | `60` | Intervalle scheduler |
| `SERVE_FRONTEND` | — | Chemin frontend (dev sans nginx) |
| `RATELIMIT_STORAGE_URI` | `memory://` | `redis://...` recommandé en prod |

---

## Production (gunicorn)

```bash
# Variables obligatoires
DATABASE_URL=postgresql://user:pass@host:5432/avyro
SECRET_KEY=<32-bytes-random>
JWT_SECRET_KEY=<32-bytes-random>
FLASK_ENV=production

# Démarrage
gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 4
```

> **Note migrations** : en production, utiliser `flask db migrate && flask db upgrade`
> (Alembic via Flask-Migrate) plutôt que `flask create-db`.
