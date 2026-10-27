# Cahier des charges – Avyro

Document destiné à l'orchestrateur. Mis à jour le 2026-10-27 d'après le code de `main` (HEAD `343e4c3`).
Priorités : P0 bloquant, P1 important, P2 dette.
Légende d'état : ✅ fait et vérifié dans le code · ⚠️ partiel · ❌ à faire · ❓ non vérifié.

## 1. Finalité

Avyro est une plateforme B2B de mutualisation entre entreprises. Un seul compte donne accès à deux services :

- **Avyro Training** : une entreprise publie les places restantes d'une formation inter-entreprises (prix par place) ; d'autres entreprises les réservent.
- **Avyro Room** : une entreprise sous-loue des salles de réunion inoccupées sur des créneaux ; d'autres entreprises les réservent.

Objectif : partager les coûts (demandeur) et rentabiliser les ressources inutilisées (fournisseur).

## 2. Contraintes techniques (issues de `CLAUDE.md`)

- Backend : Python uniquement (Flask 3, SQLAlchemy 2, Flask-JWT-Extended, flask-smorest/OpenAPI, Flask-Migrate, Flask-Limiter, Flask-Cors, APScheduler, Gunicorn). SQLite en dev, PostgreSQL en prod.
- Frontend : React 19 + Vite + Tailwind CSS 3, SPA routée par `react-router-dom` 7. Police Inter via `@fontsource/inter`.
- Pas de CSS hors classes Tailwind et `src/index.css`. Pas de `style=""` sauf valeurs dynamiques calculées en JS (toute exception est à signaler).
- Le client appelle l'API en chemins relatifs `/api/...` (`src/lib/api.js`). En dev, Vite relaie `/api` vers Flask sur `:8080`. Aucune URL absolue.
- Flask (`SERVE_FRONTEND`) sert `index.html` en fallback pour toute route non-`/api/*` sans fichier statique correspondant.
- L'email d'invitation pointe vers `/invite?token=...` (route client).
- Commits : Conventional Commits, un type par commit, jamais de trailer `Co-Authored-By`.

## 3. Périmètre fonctionnel

### 3.1 Acteurs et comptes

- **Company** (structure) : nom, SIRET (requis pour publier), adresse, fiche publique.
- **User** : rattaché à une Company, rôle `admin` (créateur) ou `member`.
- Inscription avec consentement RGPD ; connexion JWT (access 30 min + refresh) ; profil modifiable ; fiche entreprise.
- Invitation de collaborateurs par email (lien à jeton signé, 7 jours, usage unique).
- RGPD : export JSON des données (`GET /api/auth/me/export`), suppression du compte (`DELETE /api/auth/me`, anonymisation des réservations : `Booking.requested_by_id` nullable).

### 3.2 Offres (Training / Room)

- Champs : titre, description, début/fin, lieu ou distanciel, places proposées (`shared_seats`), prix par place, tags, géolocalisation.
- Statuts : ouverte, complète, en cours, terminée (calcul automatique), plus `closed`/`cancelled`.
- CRUD réservé au fournisseur propriétaire ; rapports (`/reports`) listant les inscrits confirmés.

### 3.3 Catalogue

- Recherche texte (titre, lieu, description), filtre par tag.
- Filtre « autour de moi » (Haversine, rayon 5–100 km) ; les offres distancielles sont toujours incluses.
- Filtres combinables : dates, prix max, places min, distanciel.
- Indicateur de remplissage (vert < 60 %, orange < 90 %, rouge ≥ 90 %), vue liste et vue calendrier mensuel.
- Géocodage d'adresses via proxy backend `/api/geocode`.

### 3.4 Réservations

- Création d'une demande (`pending`) avec nombre de places et note (500 car.).
- Le fournisseur confirme ou refuse (`PATCH`) ; le demandeur annule sa demande en attente (statut `cancelled`).
- Transition autorisée uniquement depuis `pending` ; surbooking évité par verrou (`with_for_update`, `utils/offers.py`).
- Compteurs de demandes en attente (badge) ; liste des demandes reçues.

### 3.5 Notifications et tâches planifiées

- Emails SMTP : nouvelle demande (fournisseur), confirmation, refus (demandeur), annulation (fournisseur), invitation. Sans `MAIL_SERVER`, écriture dans `backend/dev_outbox.log`.
- Rappel fournisseur J-1 ouvré avec liste des inscrits ; purge des offres terminées. Planificateur activé par `RUN_SCHEDULER=1`.

### 3.6 Export

- Export CSV des inscrits côté navigateur, avec neutralisation de l'injection de formules.

## 4. Architecture

### 4.1 API (préfixe `/api`, doc Swagger `/api/docs`)

| Préfixe | Routes |
|---|---|
| `/auth` | `POST /register`, `POST /login`, `POST /refresh`, `GET/PATCH/DELETE /me`, `GET /me/export`, `GET /invite-info`, `POST /accept-invite` |
| `/companies` | `GET/PATCH /me`, `POST /me/invite`, `GET /<id>`, `GET /<id>/offerings` |
| `/trainings`, `/rooms` | `GET /reports`, `GET/POST ""`, `GET/PATCH/DELETE /<id>` |
| `/bookings` | `GET /counts`, `GET /incoming`, `GET/POST ""`, `PATCH/DELETE /<id>` |
| `/geocode` | `GET ""` (proxy Nominatim) |
| `/health` | Santé |

### 4.2 Backend (`backend/app`)

`api/` (blueprints) · `models/` (Company, User, Training, Room, Booking) · `schemas/` (Marshmallow) · `services/` (mailer, maintenance) · `utils/` (auth, geo, offers, tokens) · `config.py` (Dev/Test/Prod, validation des secrets) · `extensions.py`.

### 4.3 Frontend (`frontend/src`)

Routes : `/` Landing, `/login`, `/register`, `/invite`, `/dashboard`, `/profile`, `/company`, `/privacy` ; toute autre route redirige vers `/`.
`pages/` · `components/dashboard/` (Catalog, Mine, Incoming, Bookings, Reports, CalendarView, OfferCard, modales) · `lib/` (api, contextes Auth/Dashboard/Toast, geocode, format).
Client API avec refresh transparent du token et file d'attente des requêtes concurrentes.

### 4.4 Configuration (`.env.example`)

`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY` (≥ 32 car., refus des valeurs faibles en prod), `PUBLIC_URL` (obligatoire en prod), `CORS_ORIGINS`, `RATELIMIT_STORAGE_URI`, `SERVE_FRONTEND`, `RUN_SCHEDULER`, `MAIL_*`, `POSTGRES_*`.

## 5. État actuel

| Mesure | Valeur |
|---|---|
| Tests backend | **214 passent**, 0 échec |
| Couverture backend | **95 %** (mailer 81 %, maintenance 85 %, utils/auth 76 %) |
| Build frontend (`vite build`) | OK |
| Tests / lint frontend | Aucun |
| Dernier commit | `343e4c3 docs: ajouter le cahier des charges` |
| Working tree | propre (hors `.claude/` non suivi) |

### 5.1 Corrigé depuis le brouillon précédent

| ID | Sujet | État |
|---|---|---|
| B1 | Jeton d'invitation dédié (itsdangerous, `utils/tokens.py`) | ✅ |
| B2 | Échec au démarrage en prod si secret absent/faible ; `PUBLIC_URL` obligatoire | ✅ |
| B3 | PATCH booking exige `pending` ; verrou anti-surbooking | ✅ |
| B6 | Suppression de compte : anonymisation du demandeur | ✅ |
| S1 | Refresh transparent côté front | ✅ |
| S6 | CORS configurable (`CORS_ORIGINS`, vide par défaut en prod) | ✅ |
| S9 | URL d'invitation basée sur `PUBLIC_URL` | ✅ |
| S11 | `style=` statiques retirés (restent 8 usages dynamiques légitimes : largeur de barre `OfferCard`, filtres `grayscale` `LandingPage`) | ✅ |
| S12 | Géocodage via proxy backend | ✅ |
| S13 | Neutralisation des formules CSV | ✅ |
| S18 | Annulation = statut `cancelled` | ✅ |
| D11 | `register.html` vide supprimé | ✅ |

### 5.2 Reste à faire (vérifié dans le code)

| ID | Prio | Constat | Besoin |
|---|---|---|---|
| S15 | P1 | Aucun dossier `migrations/` ; schéma créé par `create_all` | Initialiser Alembic, migration initiale, retirer `create_all` du chemin prod |
| S14 | P1 | Aucun en-tête de sécurité ; `/api/docs` public en prod | En-têtes (CSP, nosniff, frame, HSTS) ; doc désactivée ou protégée en prod |
| S7 | P1 | Limiteur sur `memory://` par défaut, pas de ProxyFix | Stockage partagé en prod, `ProxyFix`, limites sur `accept-invite` et `refresh` (à vérifier) |
| S8 | P1 | Pas de révocation de token (pas de `jti`/blocklist) | Mécanisme de révocation (logout, suppression de compte) |
| S10 | P1 | `frontend/index.html:8` garde un `preconnect` vers `fonts.googleapis.com` (police déjà auto-hébergée) | Supprimer le lien |
| S16 | P1 | `purge_finished_trainings` supprime aussi les `Room` (docstring parle de Training seulement) | Trancher le comportement voulu, aligner code et docstring |
| S17 | P1 | Scheduler désactivé par défaut | Documenter le déploiement (un seul worker) |
| D16 | P2 | `.env.example` non chargé (pas de `load_dotenv`) | Charger `.env` |
| D17 | P2 | Pas de Docker alors que `POSTGRES_*` existe | Dockerfile + compose |
| D12 | P2 | Aucun test ni lint frontend | Vitest + ESLint, CI |
| D14 | P2 | README obsolète (HTML/JS vanilla, 63 tests, `dist/styles.css`, `/company.html`, Google Fonts) | Réécrire selon la stack réelle |
| D1 | P2 | Duplication `trainings.py`/`rooms.py` et logique bookings | Factoriser sans régression |
| D13/D19 | P2 | Couverture : `utils/auth.py` 76 %, mailer 81 % | Combler, viser ≥ 85 % partout |
| D15 | P2 | `seed_demo.py` : chemin en dur, SQL brut | Nettoyer |
| D18 | P2 | Règle « SIRET requis pour publier » non documentée | Documenter |

### 5.3 À re-vérifier (état incertain, non contrôlé dans cette passe)

S2 (refresh d'un utilisateur supprimé), S3 (offre passée / doublon), S4 (PATCH offre sous les places confirmées), S5 (visibilité `closed`/`cancelled` sur `GET /<id>`), B4 (try/except sur `send_email`), B5/B7 (normalisation email, strip `company_name`), D2–D10.

## 6. Critères d'acceptation des lots restants

| Lot | Contenu | Critères |
|---|---|---|
| L-A Migrations & déploiement (P1) | S15, S16, S17, D16, D17 | `flask db upgrade` crée le schéma depuis zéro ; `create_all` absent du chemin prod ; purge conforme à la décision prise ; Docker reproductible ; scheduler documenté |
| L-B Durcissement (P1) | S7, S8, S14, S5 | En-têtes présents ; `/api/docs` inaccessible en prod ; limiteur à stockage partagé et ProxyFix ; token révoqué refusé ; tests dédiés |
| L-C Conformité front (P1) | S10 | Aucune requête vers `fonts.googleapis.com` ni `nominatim.openstreetmap.org` depuis le navigateur |
| L-D Vérifications (P1) | §5.3 | Chaque point confirmé par un test ou corrigé |
| L-E Qualité (P2) | D1, D12–D15, D18, D19 | 214 tests toujours verts, couverture ≥ 95 % ; tests + lint frontend en CI ; README aligné sur le code |

## 7. Fonctionnalités envisagées (hors périmètre actuel)

PWA/mobile · tableau de bord analytique · avis · liste d'attente · offres récurrentes · vue carte · paiement Stripe + factures PDF · forfaits multi-places · contrats de sous-location · vérification SIRET · messagerie par réservation · catalogue public · export iCal · SSO/SAML · webhooks · API publique · interface admin · i18n · archivage légal.

## 8. Questions ouvertes

- Purge : les `Room` terminées doivent-elles être supprimées avec les `Training` (comportement actuel) ?
- Cible de déploiement (hébergeur, Docker, nombre de workers) pour trancher le scheduler et le stockage du limiteur.
