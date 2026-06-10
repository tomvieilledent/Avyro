# Avyro

Plateforme de mutualisation entre entreprises, bimodale :

- **Avyro Training** — partagez des places restantes sur vos formations
- **Avyro Room** — sous-louez vos salles de réunion inoccupées

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12, Flask 3, SQLAlchemy 2, Flask-JWT-Extended |
| API docs | flask-smorest (OpenAPI 3.0 / Swagger UI) |
| Base de données | SQLite (dev) · PostgreSQL (prod) |
| Migrations | Alembic via Flask-Migrate |
| Frontend | HTML5, Tailwind CSS v3, JavaScript vanilla |
| Police | Inter (Google Fonts) |
| Auth | JWT (access token + refresh token, localStorage) |
| Emails | SMTP + APScheduler (rappels J-1, purge automatique) |
| Serveur | Gunicorn (dev : Flask dev server) |
| Tests | pytest 8, pytest-cov |

---

## Lancement rapide

```bash
./run-local.sh
```

Le script :
1. Crée un venv Python et installe les dépendances
2. Recompile le CSS Tailwind (si npm est présent)
3. Crée les tables SQLite si nécessaire
4. Démarre Gunicorn sur **http://localhost:8080**

> Swagger UI disponible sur http://localhost:8080/api/docs

### Lancement manuel (développement)

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///dev.db"
export SECRET_KEY="dev-change-me"
export JWT_SECRET_KEY="dev-jwt-secret-please-change-me-32bytes"
export SERVE_FRONTEND="../frontend"
flask run --port 5000

# Frontend (recompilation CSS)
cd frontend
npm install && npm run build
```

### Seed de démonstration

```bash
cd backend
python3 seed_demo.py
```

Peuple la base avec 8 formations, 6 salles de réunion et renomme les entreprises avec des noms réalistes.

---

## Structure du projet

```
Avyro/
├── backend/
│   ├── app/
│   │   ├── api/            # Blueprints REST (auth, companies, trainings, rooms, bookings)
│   │   ├── models/         # SQLAlchemy models (Company, User, Training, Room, Booking)
│   │   ├── schemas/        # Marshmallow schemas (validation + sérialisation)
│   │   ├── services/       # Mailer SMTP + scheduler de maintenance
│   │   └── utils/          # Auth helpers, calcul géographique (Haversine)
│   ├── tests/              # 63 tests pytest
│   ├── seed_demo.py        # Données de démonstration
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   ├── index.html          # Page d'accueil publique
│   ├── login.html          # Connexion
│   ├── register.html       # Inscription
│   ├── dashboard.html      # Tableau de bord (Training + Room)
│   ├── profile.html        # Profil utilisateur et structure
│   ├── src/
│   │   ├── api.js          # Client HTTP (JWT, fetch)
│   │   ├── dashboard.js    # Logique dashboard bimodal
│   │   ├── profile.js      # Logique profil
│   │   └── input.css       # Source Tailwind CSS
│   └── dist/styles.css     # CSS compilé
├── run-local.sh
└── README.md
```

---

## API

Toutes les routes sont préfixées `/api`. L'authentification se fait via header `Authorization: Bearer <token>`.

### Auth — `/api/auth`

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/register` | Inscription (crée user + company) |
| `POST` | `/login` | Connexion → access\_token + refresh\_token |
| `POST` | `/refresh` | Renouvelle l'access token via le refresh token |
| `GET` | `/me` | Profil de l'utilisateur connecté |
| `PATCH` | `/me` | Mise à jour du profil (nom, email, téléphone, mot de passe) |
| `DELETE` | `/me` | Suppression du compte (RGPD Art. 17) |
| `GET` | `/me/export` | Export JSON des données personnelles (RGPD Art. 20) |
| `POST` | `/accept-invite` | Création de compte via invitation |

### Companies — `/api/companies`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/me` | Infos de la structure de l'utilisateur |
| `PATCH` | `/me` | Mise à jour (admin uniquement) |
| `POST` | `/me/invite` | Inviter un membre par email (admin) |
| `GET` | `/<id>` | Détails d'une structure (public) |
| `GET` | `/<id>/offerings` | Formations et salles actives d'une structure (public) |

### Formations — `/api/trainings`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Catalogue (status=open, hors propre company) — public |
| `GET` | `/?mine=true` | Mes formations publiées |
| `GET` | `/?q=terme` | Recherche (titre, lieu, description) |
| `GET` | `/?tag=IT` | Filtre par tag |
| `GET` | `/?date_from=&date_to=` | Filtre par plage de dates |
| `GET` | `/?price_max=&seats_min=` | Filtre par prix max / places min |
| `GET` | `/?remote_only=true` | Formations à distance uniquement |
| `GET` | `/?lat=&lng=&radius=` | Filtre géographique (Haversine) |
| `POST` | `/` | Publier une formation |
| `PATCH` | `/<id>` | Modifier (provider uniquement) |
| `DELETE` | `/<id>` | Supprimer (provider uniquement) |
| `GET` | `/reports` | Inscrits confirmés par formation |

### Salles — `/api/rooms`

Même interface que `/api/trainings`, appliquée aux salles de réunion.

### Réservations — `/api/bookings`

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Mes demandes de réservation |
| `GET` | `/?kind=training` | Filtrer par type (training / room) |
| `GET` | `/incoming` | Demandes reçues sur mes offres |
| `POST` | `/` | Créer une demande (`training_id` ou `room_id` + `seats`) |
| `PATCH` | `/<id>` | Confirmer / refuser (provider uniquement) |
| `DELETE` | `/<id>` | Se désinscrire (demandeur, si pending) |

---

## Modèle de données

```
Company (1) ──< User          (N membres par structure)
Company (1) ──< Training      (N formations publiées)
Company (1) ──< Room          (N salles publiées)
Training  (1) ──< Booking     (N demandes de réservation)
Room      (1) ──< Booking
Booking  >── Company          (booker = company qui réserve)
Booking  >── User             (requested_by = utilisateur demandeur)
```

### Cycle de vie d'une offre

```
open  →  closed     (fermeture manuelle)
open  →  cancelled  (annulation)
```

### Cycle de vie d'une réservation

```
pending  →  confirmed  (provider confirme)
pending  →  cancelled  (provider refuse ou demandeur annule)
```

---

## Recherche géographique

Le filtre "Autour de moi" utilise la **formule de Haversine** (grand cercle) :

- Offres **distantes** (`is_remote=true`) : toujours incluses, pas de badge km
- Offres **avec coordonnées** : filtrées par rayon, triées par distance croissante
- Offres **sans coordonnées** : toujours incluses

Rayon disponible dans l'UI : 5 / 10 / 25 / 50 / 100 km.

Le code postal saisi à la création est résolu vers une ville + coordonnées GPS via une table statique couvrant les principaux départements français.

---

## Vue calendrier du catalogue

Le catalogue dispose d'un toggle **Liste / Calendrier** :
- **Vue liste** : affichage par cartes (défaut)
- **Vue calendrier** : grille mensuelle avec navigation mois par mois. Les jours avec des offres affichent un point bleu. Un clic sur un jour affiche le détail des offres de la journée.

---

## Export CSV des comptes rendus

Dans l'onglet **Comptes rendus**, chaque formation/salle dispose d'un bouton **⬇ CSV** qui télécharge directement la liste des inscrits confirmés au format CSV (Structure, Places, Contact, Email). Aucun appel API supplémentaire — généré côté client depuis les données déjà chargées.

---

## Fiche publique entreprise

La page `company.html?id=<id>` affiche le profil public d'une Company avec ses formations et salles actives.

- `GET /api/companies/<id>` — informations de la Company (public, JWT optionnel)
- `GET /api/companies/<id>/offerings` — formations et salles ouvertes (public)
- Le nom du provider sur les cartes catalogue est un lien cliquable vers sa fiche

---

## Indicateur de remplissage

Chaque carte du catalogue affiche une barre de progression colorée :
- **Vert** : moins de 60% des places occupées
- **Orange** : entre 60% et 90%
- **Rouge** : 90% et plus (quasi complet)

---

## Filtres avancés du catalogue

Le bouton **Filtres** dans la barre de recherche déploie un panneau de filtres avancés :

| Filtre | Paramètre API | Description |
|--------|--------------|-------------|
| Date de début (du/au) | `date_from`, `date_to` | Plage de dates pour `starts_at` |
| Prix max | `price_max` | Prix/place ≤ valeur |
| Places disponibles min | `seats_min` | `available_seats` ≥ valeur |
| À distance uniquement | `remote_only=true` | Offres distancielles uniquement |

Combinables avec la recherche texte, les tags et la géolocalisation.

---

## Tags et catégories

Les formations et salles peuvent être taguées (liste libre, ex: `["IT", "management", "sécurité"]`).

- **Création/édition** : champ "Tags" dans la modale (valeurs séparées par des virgules)
- **Filtre catalogue** : menu déroulant de filtrage dans la barre de recherche
- **Filtre API** : `GET /api/trainings?tag=IT` ou `GET /api/rooms?tag=management`
- Les tags sont affichés en badges bleus sur les cartes du catalogue

---

## Invitations membres d'équipe

Un admin peut inviter des collaborateurs à rejoindre sa structure depuis la page **Profil → Inviter un membre**.

- `POST /api/companies/me/invite` — génère un JWT d'invitation (7 jours) et envoie un email avec le lien
- `POST /api/auth/accept-invite` — valide le token et crée le compte dans la même Company
- Page dédiée `invite.html?token=<jwt>` pour finaliser l'inscription

---

## Note sur la réservation

Lors d'une réservation, le demandeur peut ajouter une **note optionnelle** (max 500 caractères) destinée au provider. La note est :
- Affichée dans l'onglet "Demandes reçues" du provider
- Incluse dans l'email de notification au provider

---

## Badges de notifications

L'onglet **Demandes reçues** affiche un badge rouge avec le nombre de réservations en attente de traitement (`GET /api/bookings/counts`). Le badge se met à jour après chaque confirmation, refus ou nouvelle réservation.

---

## Notifications email automatiques

Des emails sont envoyés automatiquement aux parties concernées à chaque étape clé d'une réservation :

| Événement | Destinataire | Sujet |
|-----------|-------------|-------|
| Nouvelle demande de réservation | Provider (contact ou admin) | `Nouvelle demande de réservation — {titre}` |
| Réservation confirmée | Booker (demandeur) | `Réservation confirmée — {titre}` |
| Réservation refusée | Booker (demandeur) | `Réservation refusée — {titre}` |
| Annulation par le booker | Provider | `Annulation de réservation — {titre}` |

En développement, les emails sont écrits dans `backend/dev_outbox.log`.

---

## Maintenance automatique

Le scheduler APScheduler (activé via `RUN_SCHEDULER=1`) exécute quotidiennement :

1. **Rappels** — email au provider 1 jour ouvré avant le début de chaque offre, avec la liste live des inscrits confirmés
2. **Purge** — suppression immédiate des offres dont `ends_at` est dépassé (Training et Room)

---

## Conformité RGPD

| Droit | Implémentation |
|-------|---------------|
| **Consentement (Art. 7)** | Checkbox obligatoire à l'inscription + lien vers `privacy.html` |
| **Accès (Art. 15)** | Toutes les données visibles dans le profil |
| **Rectification (Art. 16)** | `PATCH /api/auth/me` et `PATCH /api/companies/me` |
| **Effacement (Art. 17)** | `DELETE /api/auth/me` — supprime user (et Company si dernier admin) |
| **Portabilité (Art. 20)** | `GET /api/auth/me/export` — téléchargement JSON depuis le profil |
| **Information (Art. 13)** | Page `privacy.html` avec finalités, durées et contacts |

La suppression d'une Company entraîne la suppression en cascade de toutes ses données (users, trainings, rooms, bookings) via SQLAlchemy.

---

## Variables d'environnement

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `DATABASE_URL` | oui | ex. `sqlite:///dev.db` ou `postgresql://...` |
| `SECRET_KEY` | oui | Clé Flask |
| `JWT_SECRET_KEY` | oui | Clé signature JWT (min. 32 caractères) |
| `SERVE_FRONTEND` | non | Chemin absolu du dossier frontend (Flask sert les fichiers statiques) |
| `RUN_SCHEDULER` | non | `1` pour activer le scheduler APScheduler |
| `MAIL_SERVER` | non | Serveur SMTP (défaut : log fichier) |
| `MAIL_PORT` | non | Port SMTP (défaut : 587) |
| `MAIL_USERNAME` | non | Identifiant SMTP |
| `MAIL_PASSWORD` | non | Mot de passe SMTP |
| `MAIL_FROM` | non | Adresse expéditeur |
| `FLASK_ENV` | non | `development` / `production` (défaut : `development`) |

---

## Tests

```bash
cd backend
pytest                         # tous les tests
pytest --cov=app               # avec couverture
pytest tests/test_trainings.py # un fichier
```

63 tests couvrant : authentification, gestion des structures, formations, salles, réservations et maintenance.

---

## Développement frontend

```bash
cd frontend
npm run build   # compilation one-shot
npm run watch   # recompilation automatique
```

La police **Inter** est chargée depuis Google Fonts. Le CSS compilé est `dist/styles.css`.
