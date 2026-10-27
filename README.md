# Avyro

Plateforme B2B de mutualisation entre entreprises. Une entreprise publie les places ou créneaux inutilisés de ses formations et de ses salles. Les autres entreprises les réservent.

Un seul compte donne accès à deux services :

- **Avyro Training** : places restantes d'une formation inter-entreprises, prix par place.
- **Avyro Room** : créneaux de salles de réunion sous-louées.

## Stack

| Couche | Technologie |
|--------|-------------|
| Frontend | React 19 · Vite 8 · Tailwind CSS 3 · react-router-dom 7 · Inter (`@fontsource/inter`) |
| Backend | Python 3.12 · Flask 3 · SQLAlchemy 2 (Flask-SQLAlchemy 3.1) · Flask-JWT-Extended · flask-smorest (OpenAPI 3.0) · Flask-Limiter · Flask-Migrate (Alembic) · APScheduler · Gunicorn |
| Base de données | SQLite (dev) · PostgreSQL 16 (Docker) |
| Tests et qualité | pytest 8 · pytest-cov · Vitest 4 · Testing Library · ESLint 10 |

Le backend sert aussi le build frontend (`SERVE_FRONTEND`). Une seule application répond sur le même port.

## Prérequis

- Python 3.12
- Node.js 22 et npm
- Docker et Docker Compose (optionnel)

## Structure du projet

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Blueprints : auth, companies, trainings, rooms, bookings, geocode
│   │   ├── models/       # Company, User, Training, Room, Booking, TokenBlocklist
│   │   ├── schemas/      # Schémas marshmallow (validation, sérialisation)
│   │   ├── services/     # mailer.py (SMTP ou outbox), maintenance.py (scheduler)
│   │   ├── utils/        # auth, geo (Haversine), offers (verrous), tokens (invitations), jwt_handlers
│   │   ├── config.py     # Configs development / testing / production
│   │   ├── security.py   # En-têtes HTTP, CSP, ProxyFix
│   │   └── extensions.py
│   ├── migrations/       # Révisions Alembic (0001, 0002)
│   ├── tests/            # Suite pytest
│   ├── seed_demo.py      # Données de démonstration
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── pages/        # Landing, Login, Register, Invite, Dashboard, Profile, Company, Privacy
│       ├── components/   # dashboard/ : catalogue, offres, réservations, rapports, calendrier
│       ├── lib/          # api.js (client HTTP), contextes Auth/Dashboard/Toast, csv, geocode
│       └── test/         # Setup Vitest
├── docs/specs/cahier-des-charges.md
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── run-local.sh
└── .env.example
```

## Installation et lancement en développement

### Option 1 : script complet

```bash
./run-local.sh
```

Le script :

1. crée `backend/.venv` et installe `requirements.txt` ;
2. installe les dépendances frontend et compile `frontend/dist` (si npm est présent) ;
3. crée la base SQLite `backend/dev.db` avec `db.create_all()` ;
4. démarre Gunicorn sur **http://localhost:8080** (SPA + API).

Swagger UI : **http://localhost:8080/api/docs**

Le script fixe des secrets de développement. Ne pas réutiliser ces valeurs ailleurs.

### Option 2 : frontend avec rechargement à chaud

Terminal 1 (backend sur `:8080`) :

```bash
./run-local.sh
```

Terminal 2 (frontend) :

```bash
cd frontend
npm install
npm run dev
```

Ouvrir **http://localhost:5173**. Vite relaie `/api` vers `http://localhost:8080`. Le client appelle des chemins relatifs `/api/...` : ne pas coder d'URL absolue.

### Backend seul

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
flask db upgrade
flask run --port 8080
```

- `.flaskenv` fixe `FLASK_APP=wsgi.py` et `FLASK_ENV=development`.
- `flask run` écoute sur le port 5000 par défaut. `--port 8080` est nécessaire pour le proxy Vite.
- Sans `DATABASE_URL`, SQLite utilise `backend/instance/dev.db`.

## Données de démonstration

Prérequis : base migrée et au moins un compte créé (`/register`).

```bash
cd backend
DATABASE_URL=sqlite:///dev.db .venv/bin/python seed_demo.py
```

Le script :

- renomme les structures existantes avec des noms de démonstration ;
- **supprime** les formations, salles et réservations existantes ;
- insère 8 formations et 6 salles.

Refusé si `FLASK_ENV=production`.

## Fonctionnalités

### Offres (formations et salles)

- Champs : titre, description, lieu ou distanciel, début et fin, places proposées (`shared_seats`), prix par place, téléphone de contact, coordonnées GPS optionnelles, tags libres.
- Statut stocké : `open`, `closed`, `cancelled`. Le front affiche aussi « En cours » (début passé) et « Complète » (0 place).
- Seul le provider modifie ou supprime son offre. Une modification ne peut pas descendre sous les places déjà confirmées.
- Le catalogue ne liste que les offres `open`. Le détail d'une offre non `open` renvoie 404, sauf pour son propriétaire.

### Catalogue et recherche

`GET /api/trainings` et `GET /api/rooms` acceptent :

| Paramètre | Effet |
|-----------|-------|
| `q` | Recherche sur titre, lieu, description |
| `tag` | Filtre sur un tag |
| `date_from`, `date_to` | Plage de dates de début |
| `price_max` | Prix par place maximum |
| `seats_min` | Places disponibles minimum |
| `remote_only` | Offres à distance uniquement |
| `lat`, `lng`, `radius` | Filtre géographique (rayon en km, défaut 25) |
| `mine=true` | Offres de ma structure |

- Géolocalisation : distance Haversine. L'interface propose 5, 10, 25, 50 et 100 km.
- Les offres à distance sont toujours incluses.
- Les offres physiques sans coordonnées sont exclues du filtre géographique.
- Indicateur de remplissage : vert < 60 %, orange < 90 %, rouge ≥ 90 %.
- Vue liste (défaut) et vue calendrier mensuel.

### Réservations

- `POST /api/bookings` crée une demande `pending` (`training_id` **ou** `room_id`, `seats` ≥ 1, `note` ≤ 500 caractères).
- Refus si : offre de sa propre structure, offre non `open`, offre passée, places insuffisantes, ou demande `pending`/`confirmed` déjà existante pour la structure (409).
- `PATCH /api/bookings/<id>` avec `{"status": "confirmed"}` ou `{"status": "cancelled"}` : réservé au provider, uniquement depuis `pending`. La confirmation revérifie les places.
- `DELETE /api/bookings/<id>` : le demandeur annule sa demande `pending` (statut `cancelled`).
- Les créations et confirmations verrouillent l'offre (`SELECT … FOR UPDATE`). Pas de surbooking.
- `GET /api/bookings/counts` donne le nombre de demandes en attente. Le badge « Demandes reçues » est rafraîchi au chargement et après les actions. Il n'est pas temps réel.

### Emails

| Événement | Destinataire |
|-----------|--------------|
| Nouvelle demande | Provider (`contact_email` de la structure, sinon admin) |
| Demande confirmée | Demandeur |
| Demande refusée | Demandeur |
| Annulation par le demandeur | Provider |
| Invitation de collaborateur | Adresse invitée |
| Rappel J-1 ouvré avec liste des inscrits | Tous les utilisateurs de la structure provider |

Le rappel est envoyé une seule fois (`reminder_sent`).

Un échec d'envoi est journalisé. Il ne fait pas échouer la requête.

### Comptes rendus

- `GET /api/trainings/reports` et `GET /api/rooms/reports` : inscrits confirmés par offre.
- L'export CSV est généré dans le navigateur, sans appel API supplémentaire.

### Structures, équipe et invitations

- Inscription : crée une structure et son premier utilisateur `admin`. Sans nom de structure, le nom vaut « Prénom Nom ».
- Seul l'admin modifie la structure (`PATCH /api/companies/me`) et invite des membres (`POST /api/companies/me/invite`, rôle `member` ou `admin`).
- Lien d'invitation : `${PUBLIC_URL}/invite?token=…`. Jeton signé (itsdangerous), valable 7 jours. Le compte créé consomme l'invitation.
- Fiche publique : `/company?id=<id>` côté front, données via `GET /api/companies/<id>/offerings`.

### SIRET requis pour publier

- `POST /api/trainings` et `POST /api/rooms` renvoient **403** si `siret` de la structure est vide. Message : « Un numéro SIRET/SIREN est requis pour publier… ».
- Le SIRET se renseigne via `PATCH /api/companies/me` (admin). Il est unique (409 si déjà utilisé). Longueur max 20. Aucun contrôle de format.
- Le contrôle porte sur la **création** d'offre. La modification d'une offre existante et la réservation ne sont pas bloquées.
- Tout membre de la structure peut publier une fois le SIRET renseigné.

### Authentification, déconnexion et révocation

- Access token valide 30 min (`JWT_ACCESS_MINUTES`). Refresh token valide 30 jours (`JWT_REFRESH_DAYS`).
- `POST /api/auth/refresh` : nouvel access token, avec le refresh token en Bearer.
- Le front renouvelle le token sur 401. Les requêtes concurrentes attendent le même renouvellement. Les tokens sont stockés dans `localStorage`.
- `POST /api/auth/logout` :
  - en-tête `Authorization: Bearer <access>` ;
  - corps JSON optionnel `{"refresh_token": "…"}`.
  - Révoque l'access token (ajouté à la table `token_blocklist`).
  - Révoque aussi le refresh token fourni, s'il appartient au même utilisateur. Sinon 400.
- Un token révoqué renvoie 401 : « Session révoquée, reconnectez-vous. ».
- Changer son mot de passe (`PATCH /api/auth/me` avec `password`) incrémente `users.token_version`. Les refresh tokens émis avant ce changement sont refusés.
- Les access tokens déjà émis restent valides jusqu'à leur expiration, sauf logout.
- Supprimer son compte révoque le token courant.
- Les entrées expirées de `token_blocklist` sont purgées par la maintenance.

### RGPD

| Droit | Endpoint |
|-------|----------|
| Accès et portabilité | `GET /api/auth/me/export` (JSON) |
| Rectification | `PATCH /api/auth/me`, `PATCH /api/companies/me` |
| Effacement | `DELETE /api/auth/me` |

- Effacement : si l'utilisateur est le dernier admin, la structure et ses offres sont supprimées. Sinon, seul le compte est supprimé.
- Les réservations survivantes gardent `requested_by_id = NULL`.
- Le formulaire d'inscription affiche une case de consentement avec lien vers `/privacy`. Le backend ne contrôle pas ce champ.

## Scheduler et maintenance

Le scheduler APScheduler démarre si `RUN_SCHEDULER=1`. Il exécute toutes les `SCHEDULER_INTERVAL_MINUTES` minutes (défaut 60), avec une première exécution au démarrage :

1. **Rappels** : envoie les rappels J-1 ouvré.
2. **Purge des offres terminées** : supprime les `Training` **et** les `Room` dont `ends_at` est dépassé. Leurs réservations sont supprimées en cascade. La suppression est définitive.
3. **Purge de la blocklist** : supprime les jetons révoqués expirés.

Lancement manuel :

```bash
cd backend
flask maintenance
```

**Un seul process avec le scheduler.** Avec `RUN_SCHEDULER=1` dans plusieurs workers, les jobs seraient dupliqués.

- Docker : `WEB_CONCURRENCY=1`, concurrence via `GUNICORN_THREADS` (défaut 4).
- Plusieurs workers : `RUN_SCHEDULER=0` sur les workers, et un scheduler dans une instance dédiée.

## Migrations

Révisions présentes :

| Révision | Contenu |
|----------|---------|
| `0001` | Schéma initial, dont l'index unique `uq_users_email_lower` (`lower(email)`) |
| `0002` | Table `token_blocklist`, colonne `users.token_version` |

Commandes :

```bash
cd backend
flask db upgrade                       # applique les migrations
flask db migrate -m "description"      # génère une révision depuis les modèles, à relire avant upgrade
```

- En Docker, `docker-entrypoint.sh` lance `flask db upgrade` au démarrage. `RUN_MIGRATIONS=0` désactive cette étape.
- `flask create-db` (création par `create_all`) est refusé en production.

### Base de production existante

Base créée avant les migrations (sans table `alembic_version`) :

```bash
cd backend
flask db stamp 0001
psql "$DATABASE_URL" -c "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));"
flask db upgrade
```

- `stamp 0001` marque la révision comme appliquée sans l'exécuter. L'index doit donc être créé à la main.
- `upgrade` applique `0002`.
- La création de l'index échoue si deux emails ne diffèrent que par la casse. Corriger ces doublons avant.

## Configuration

Variables lues par `backend/app/config.py`. Les fichiers `.env` de la racine et de `backend/` sont chargés pour les lancements locaux. Une variable déjà présente dans l'environnement n'est pas écrasée.

| Variable | Défaut | Rôle |
|----------|--------|------|
| `FLASK_ENV` | `development` (`create_app`, CLI) · `production` (`wsgi.py`) | `development`, `testing` ou `production` |
| `DATABASE_URL` | dev : `sqlite:///dev.db` · prod : `postgresql://avyro:avyro@db:5432/avyro` | `postgres://` et `postgresql://` utilisent psycopg2 |
| `SECRET_KEY` | dev : valeur de dev | **Obligatoire en prod.** ≥ 32 car., distincte de `JWT_SECRET_KEY` |
| `JWT_SECRET_KEY` | dev : valeur de dev | **Obligatoire en prod.** ≥ 32 car., distincte de `SECRET_KEY` |
| `JWT_ACCESS_MINUTES` | `30` | Durée de l'access token |
| `JWT_REFRESH_DAYS` | `30` | Durée du refresh token |
| `PUBLIC_URL` | dev : `http://localhost:5173` | **Obligatoire en prod.** Base des liens d'invitation |
| `CORS_ORIGINS` | dev : `*` · prod : vide | **Obligatoire en prod.** Origines séparées par des virgules, ou `*` (dev/test seulement) |
| `SERVE_FRONTEND` | non défini | Dossier du build (`frontend/dist`) servi par Flask |
| `RUN_SCHEDULER` | non défini | `1` active le scheduler (voir plus haut) |
| `SCHEDULER_INTERVAL_MINUTES` | `60` | Intervalle du scheduler |
| `RATELIMIT_STORAGE_URI` | `memory://` | Stockage du rate limiting. En prod, utiliser un stockage partagé (ex. `redis://…`) : sinon avertissement au démarrage. Désactivé en dev/test |
| `TRUSTED_PROXY_COUNT` | `0` | Nombre de reverse proxies devant l'app (ProxyFix). Indiquer le nombre réel : une valeur trop haute laisse les clients falsifier `X-Forwarded-For` |
| `API_DOCS_ENABLED` | `0` | Prod uniquement. `1` ou `true` expose `/api/docs` et `/api/openapi.json`. Actif par défaut en dev/test |
| `MAIL_SERVER` | non défini | Serveur SMTP. Absent : emails écrits dans `backend/dev_outbox.log` |
| `MAIL_PORT` | `587` | Port SMTP |
| `MAIL_USE_TLS` | `true` | STARTTLS |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | vide | Identifiants SMTP |
| `MAIL_FROM` | `no-reply@avyro.app` | Expéditeur |
| `MAIL_DEV_OUTBOX` | `backend/dev_outbox.log` | Fichier de l'outbox de développement |
| `HTTP_PORT` | `8080` | Port de `wsgi.py` et des conteneurs |
| `RUN_MIGRATIONS` | `1` | Docker : `flask db upgrade` au démarrage |
| `WEB_CONCURRENCY` | `1` | Docker : nombre de workers Gunicorn |
| `GUNICORN_THREADS` | `4` | Docker : threads par worker |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `avyro`, **requis**, `avyro` | Docker Compose uniquement |

Un fichier `.env` est copié à partir de `.env.example` :

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # générer SECRET_KEY et JWT_SECRET_KEY
```

### Variables transmises au conteneur

`.dockerignore` exclut `.env`. Le conteneur ne reçoit que les variables listées dans le bloc `environment` de `docker-compose.yml`. Absentes de ce bloc aujourd'hui : `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `GUNICORN_THREADS`, `RUN_MIGRATIONS`. Les ajouter au service `app` si besoin.

Compose ne fournit pas de service Redis.

### Règles de validation en production

Au démarrage (`FLASK_ENV=production`), la configuration est refusée (`ConfigError`) si :

- `SECRET_KEY` ou `JWT_SECRET_KEY` est absent, fait moins de 32 caractères, ou commence par `dev-`, `change-me` ou `changeme` ;
- `SECRET_KEY` et `JWT_SECRET_KEY` sont identiques ;
- `PUBLIC_URL` ou `CORS_ORIGINS` est vide.

## Docker

```bash
cp .env.example .env          # renseigner SECRET_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD
docker compose up -d --build
curl http://localhost:8080/api/health
```

Réponse attendue : `{"env": "production", "status": "ok"}`.

- `db` : `postgres:16.4-alpine`, volume `pgdata`, healthcheck `pg_isready`.
- `app` : image construite par le `Dockerfile` (build Vite avec `node:22.11`, puis `python:3.12.7-slim-bookworm`), utilisateur non-root.
- Au démarrage : `flask db upgrade`, puis Gunicorn (`-w 1`, `--threads 4`, `--timeout 120`). `RUN_SCHEDULER=1`.

`docker compose down` conserve le volume de données. `docker compose down -v` supprime la base.

Les variables de `.env.example` (ex. `POSTGRES_PASSWORD=avyro`) sont des exemples. Les remplacer.

## Lancement en production sans Docker

```bash
cd backend
# Remplacer chaque valeur entre crochets.
export FLASK_ENV=production SECRET_KEY='<secret>' JWT_SECRET_KEY='<autre-secret>' \
       PUBLIC_URL='https://<domaine>' CORS_ORIGINS='https://<domaine>' \
       DATABASE_URL='postgresql://<user>:<password>@<hote>:5432/<base>' \
       SERVE_FRONTEND='/chemin/vers/frontend/dist' RUN_SCHEDULER=1
flask db upgrade
gunicorn -b 0.0.0.0:8080 -k gthread -w 1 --threads 4 --timeout 120 wsgi:app
```

Le frontend doit être compilé au préalable (`cd frontend && npm run build`).

## Tests

### Backend

```bash
cd backend
. .venv/bin/activate
pytest                          # suite complète
pytest --cov=app                # avec couverture
pytest tests/test_trainings.py  # un fichier
```

`create_app("testing")` utilise SQLite en mémoire. Le rate limiting est désactivé.

### Frontend

```bash
cd frontend
npm install
npm run lint     # ESLint
npm test         # Vitest (jsdom), équivalent à vitest run
npm run build    # build Vite vers frontend/dist
```

### Formatage des pages HTML

```bash
npm install                 # à la racine : installe Prettier
npm run format:check
npm run format
```

## Documentation

- API interactive : `/api/docs` (dev ; prod si `API_DOCS_ENABLED=1`). Spec JSON : `/api/openapi.json`.
- Cahier des charges, état des lots et backlog : `docs/specs/cahier-des-charges.md`.
- Règles de développement : `CLAUDE.md`.

## Sécurité HTTP

En-têtes ajoutés à chaque réponse :

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(self), camera=(), microphone=()`
- `Strict-Transport-Security` (production uniquement)

Politique CSP :

- SPA : `default-src 'self'`, `script-src 'self'`, `style-src 'self'`, `img-src 'self' data: blob:`, `font-src 'self'`, `connect-src 'self'`, `frame-ancestors 'none'`.
- API JSON : `default-src 'none'`.
- Swagger UI : autorise `https://cdn.jsdelivr.net` et `'unsafe-inline'`. Actif en dev, ou en prod avec `API_DOCS_ENABLED=1`.

### Exception CSP : `style-src-attr 'unsafe-inline'`

La SPA déclare `style-src-attr 'unsafe-inline'`. C'est une exception explicite, prévue par `CLAUDE.md`.

Elle autorise uniquement les attributs `style` **dynamiques** calculés en JS :

- largeur de la barre de remplissage (`components/dashboard/OfferCard.jsx`) ;
- filtre `grayscale` de la page d'accueil (`pages/LandingPage.jsx`).

Les balises `<style>` et les feuilles externes restent bloquées par `style-src 'self'`. Ne pas ajouter de `style` statique : utiliser une classe Tailwind ou `src/index.css`.

### Rate limiting

| Endpoint | Limite |
|----------|--------|
| `POST /api/auth/register` | 10 par heure |
| `POST /api/auth/login` | 20 par minute |
| `POST /api/auth/refresh` | 30 par minute |
| `GET /api/auth/invite-info` | 20 par minute |
| `POST /api/auth/accept-invite` | 10 par minute |
| `GET /api/geocode` | 30 par minute |

Clé : adresse IP du client. Limites désactivées en dev et en test.

### Géocodage

`GET /api/geocode?q=…` relaie Nominatim (OpenStreetMap), timeout 5 s. Le navigateur n'appelle pas Nominatim directement. Si Nominatim est injoignable : 502.

## Déploiement : rappels

- Un seul process avec `RUN_SCHEDULER=1` (voir *Scheduler et maintenance*).
- Derrière un reverse proxy : renseigner `TRUSTED_PROXY_COUNT` et utiliser un `RATELIMIT_STORAGE_URI` partagé.
- Lancer `flask db upgrade` avant chaque mise en service (fait automatiquement en Docker).

## Dépannage

| Symptôme | Cause et action |
|----------|-----------------|
| `ConfigError: … est obligatoire en production` ou `doit contenir au moins 32 caractères` | Variables de sécurité absentes ou faibles. Voir *Règles de validation en production*. `wsgi.py` démarre en `production` si `FLASK_ENV` n'est pas défini. |
| `docker compose` affiche `SECRET_KEY requis` ou `POSTGRES_PASSWORD requis` | `.env` incomplet. Renseigner les valeurs (non vides). |
| Variable définie dans `.env` mais sans effet en Docker | Le conteneur ne lit pas `.env`. Ajouter la variable au bloc `environment` de `docker-compose.yml`. |
| `403 … SIRET/SIREN est requis pour publier` | Renseigner le SIRET de la structure (`PATCH /api/companies/me`, admin). |
| Emails absents en dev | Lire `backend/dev_outbox.log`. |
| Emails absents en prod | Chercher « Échec d'envoi d'email » dans les logs. Vérifier `MAIL_*`. |
| Rappels ou purge jamais exécutés | `RUN_SCHEDULER=1`, un seul process. Test manuel : `flask maintenance`. |
| `flask db upgrade` : « table already exists » | Base créée par `create_all` (`run-local.sh`, `flask create-db`). Supprimer la base de dev, ou la marquer à jour avec `flask db stamp head` si son schéma correspond aux modèles. |
| `flask db upgrade` échoue sur `uq_users_email_lower` | Emails en doublon à la casse près. Corriger les données, puis relancer. |
| `429 rate_limit` derrière un proxy | Toutes les requêtes semblent venir du proxy. Renseigner `TRUSTED_PROXY_COUNT`. |
| `/api/docs` introuvable en prod | Normal. Définir `API_DOCS_ENABLED=1`. |
| Erreurs `ECONNREFUSED` ou 502 sur `/api` en `npm run dev` | Backend non démarré sur `:8080`. Lancer `./run-local.sh`. |
| `run-local.sh` ne sert pas le frontend | Pas de npm et pas de `frontend/dist`. Installer Node.js ou compiler le frontend. |
| `401 Session révoquée` après déconnexion | Comportement attendu. Se reconnecter. |
| Erreur CSP dans la console | Ressource externe bloquée par `default-src 'self'`. Servir la ressource en local ou ajuster la CSP dans `backend/app/security.py`. |
| `502 Service de géocodage indisponible` | Nominatim injoignable ou lent (timeout 5 s). Réessayer plus tard. |

## Hors périmètre actuel

PWA, tableau de bord analytique, avis, liste d'attente, offres récurrentes, vue carte, paiement, forfaits multi-places, contrats, vérification SIRET, messagerie, catalogue public, export iCal, SSO, webhooks, API publique, interface admin, i18n, archivage légal. Détails : `docs/specs/cahier-des-charges.md`, section 7.
