# Cahier des charges – Avyro

Statut : brouillon. Priorités : P0 bloquant, P1 important, P2 dette.

## 1. Finalité et périmètre existant

Avyro est une plateforme B2B de mutualisation. Des entreprises publient des offres (places de formation, salles) et d'autres entreprises les réservent.

- Backend : Python / Flask (flask-smorest, SQLAlchemy).
- Frontend : React (Vite) + Tailwind CSS, SPA routée par `react-router-dom`.
- Règles de stack : voir `CLAUDE.md` (pas de CSS hors Tailwind et `src/index.css`, API en chemins relatifs `/api/...`).

Périmètre de ce document : état actuel, écarts constatés, besoins déduits, lots de correction.

## 2. Existant

### 2.1 Modèles

| Modèle | Rôle |
|---|---|
| Company | Entreprise (SIRET requis pour publier) |
| User | Utilisateur rattaché à une Company |
| Training | Offre de formation (places partagées, statut) |
| Room | Offre de salle (statut `open`, etc.) |
| Booking | Réservation d'une Training ou d'une Room par une Company ; `requested_by_id` NOT NULL ; statuts dont `pending`, `confirmed` |

### 2.2 API

| Préfixe | Routes |
|---|---|
| `/api/auth` | `POST /register`, `POST /login`, `POST /refresh`, `GET/PATCH/DELETE /me`, `GET /me/export`, `POST /accept-invite` |
| `/api/companies` | `GET/PATCH /me`, `POST /me/invite`, `GET /<id>`, `GET /<id>/offerings` |
| `/api/trainings` | `GET /reports`, `GET/POST /`, `GET/PATCH/DELETE /<id>` |
| `/api/rooms` | `GET /reports`, `GET/POST /`, `GET/PATCH/DELETE /<id>` |
| `/api/bookings` | `GET /counts`, `GET /incoming`, `GET/POST /`, `PATCH/DELETE /<id>` |
| `/api/health` | Santé |

### 2.3 Pages frontend

`/` (Landing), `/login`, `/register`, `/invite` (jeton en query), `/dashboard`, `/profile`, `/company`, `/privacy`. Toute autre route redirige vers `/`.

### 2.4 Fonctionnalités transverses

- Cycle de réservation : demande (`pending`), confirmation par le propriétaire de l'offre, annulation.
- Emails : notifications de réservation, invitation de collaborateur.
- Rappel J-1 : tâche planifiée (scheduler, `RUN_SCHEDULER`).
- RGPD : export (`GET /api/auth/me/export`) et suppression (`DELETE /api/auth/me`) du compte.

### 2.5 Qualité

- 164 tests backend passent.
- Build frontend OK.
- Couverture backend : 93 %.

## 3. Écarts et besoins déduits

### 3.1 P0 – Sécurité / robustesse

| ID | Constat | Besoin | Réf. |
|---|---|---|---|
| B1 | Le jeton d'invitation est un access JWT ; utilisé en Bearer, il provoque un 500 | Jeton distinct à usage unique (itsdangerous ou JWT dédié) | companies.py:82-91, utils/auth.py:14,23 |
| B2 | Secrets par défaut utilisables en prod | Échec au démarrage en `ProductionConfig` si secret absent ou faible | config.py:13-14 |
| B3 | PATCH booking sans contrôle de transition ; surbooking non atomique | Exiger l'état `pending` ; verrou `with_for_update` | bookings.py:180-193 |
| B4 | `send_email` après commit sans try/except : 500 alors que l'action est faite | Capturer et journaliser l'échec d'envoi | bookings.py:155,198,212,249 |
| B5 | Emails non normalisés, unicité sensible à la casse, `IntegrityError` → 500 | Minuscules, unicité insensible à la casse, 409 propre | auth.py:72-97, companies.py:79 |
| B6 | `DELETE /me` avec réservations → `IntegrityError` (`Booking.requested_by_id` NOT NULL) | Stratégie d'anonymisation ou de réaffectation | models/booking.py |
| B7 | `company_name` non strippé | `strip()` à l'entrée | auth.py:75,80 |

### 3.2 P1 – Important

| ID | Constat | Besoin |
|---|---|---|
| S1 | Refresh token jamais utilisé côté front : session de 30 min puis redirection brutale (api.js:56-59) | Rafraîchissement transparent |
| S2 | Refresh ne vérifie pas l'existence de l'utilisateur | Vérifier l'utilisateur |
| S3 | POST booking sans contrôle d'offre future ni de doublon (bookings.py:135-139) | Refuser offre passée et doublon |
| S4 | PATCH offre : `shared_seats` sous les places confirmées ; validation de dates partielle (trainings.py:128-133, rooms.py) | Valider contre l'état persistant |
| S5 | `GET /trainings/<id>` expose les offres closed/cancelled (trainings.py:118-119) | Restreindre la visibilité |
| S6 | CORS `*` (`__init__.py:52`) | Liste d'origines configurable |
| S7 | Rate limit `memory://` sans ProxyFix ; pas de limite sur accept-invite et refresh | Stockage partagé, ProxyFix, limites ajoutées |
| S8 | Pas de révocation de token | Mécanisme de révocation |
| S9 | URL d'invitation basée sur `request.host_url` (companies.py:93) | Config `PUBLIC_URL` |
| S10 | Google Fonts externe (index.css:1), enjeu RGPD | Auto-héberger les polices |
| S11 | `style=` statiques dans CalendarView.jsx:74,77 (viole CLAUDE.md) | Classes Tailwind |
| S12 | Nominatim appelé en direct (nominatim.js) | Proxy backend |
| S13 | Injection de formules CSV (ReportsPanel.jsx:6-14) | Neutraliser `= + - @` en début de cellule |
| S14 | En-têtes de sécurité absents ; `/api/docs` public en prod | Ajouter les en-têtes ; désactiver ou protéger la doc en prod |
| S15 | Pas de migrations Alembic (`create_all`), contrairement au README | Mettre en place Alembic |
| S16 | `purge_finished_trainings` supprime aussi les Room | Corriger le périmètre de la purge |
| S17 | Scheduler désactivé par défaut (`RUN_SCHEDULER`) | Documenter et définir le déploiement du scheduler |
| S18 | Annulation par le demandeur = DELETE physique ; README annonce « cancelled » | Aligner code et README (statut `cancelled`) |

### 3.3 P2 – Dette

| ID | Constat |
|---|---|
| D1 | `trainings.py` / `rooms.py` et logique bookings training/room dupliquées |
| D2 | `Training.__repr__` lit `self.kind` (training.py:85) |
| D3 | Docstring `geo.py` incohérente |
| D4 | `ilike` sans échappement, pas de pagination, N+1 |
| D5 | Imports inutiles ; `admin_required` inutilisé |
| D6 | `training_id=0` accepté (schemas/booking.py) |
| D7 | Pas de limites de longueur (company_name, tags, password) |
| D8 | `JSON.parse` sans try/catch (api.js:30) |
| D9 | `ProfilePage` duplique `clearSession` ; `catch{}` silencieux |
| D10 | Gros composants |
| D11 | `frontend/register.html` vide |
| D12 | Aucun test ni lint frontend |
| D13 | Tests manquants : jeton d'invitation en Bearer, transitions booking, concurrence |
| D14 | README obsolète (63 tests vs 164, scripts npm, Tailwind, pages, seed, Alembic) |
| D15 | `seed_demo.py` : chemin en dur et SQL brut |
| D16 | `.env.example` non chargé (pas de `load_dotenv`) |
| D17 | Pas de Docker alors que variables `POSTGRES_*` |
| D18 | SIRET requis pour publier non documenté |
| D19 | Mailer couvert à 53 % |

## 4. Critères d'acceptation par lot

| Lot | Critères |
|---|---|
| L1 | Jeton d'invitation en Bearer → 401/422, jamais 500. Jeton d'invitation inutilisable une 2e fois. Démarrage en production refusé si `SECRET_KEY` / `JWT_SECRET_KEY` absent ou faible. Test dédié pour chaque cas. |
| L2 | PATCH sur booking non `pending` → 409. Deux confirmations concurrentes ne dépassent pas `shared_seats`. Échec d'envoi d'email : réponse de succès et erreur journalisée. Doublon et offre passée refusés. PATCH offre sous les places confirmées refusé. |
| L3 | Emails stockés en minuscules ; doublon à casse différente → 409. `company_name` strippé. `DELETE /me` avec réservations → 204, aucune `IntegrityError`, export cohérent. Refresh transparent côté front ; refresh d'un utilisateur supprimé refusé. |
| L4 | Plus de `style=` statique (hors valeurs dynamiques JS). Aucune requête vers `fonts.googleapis.com` ni `nominatim.openstreetmap.org` depuis le navigateur. Export CSV : cellules débutant par `= + - @` neutralisées. |
| L5 | CORS limité aux origines configurées. Limiteur sur accept-invite et refresh, stockage partagé, ProxyFix actif. En-têtes de sécurité présents. `/api/docs` inaccessible en prod. `GET /trainings/<id>` n'expose pas closed/cancelled aux tiers. |
| L6 | `flask db upgrade` crée le schéma depuis zéro. `create_all` retiré du chemin de production. `PUBLIC_URL` utilisée dans les liens d'invitation. Déploiement reproductible (Docker ou équivalent). Scheduler documenté. Purge sans suppression de Room. |
| L7 | Logique training/room factorisée sans régression (164 tests verts, couverture >= 93 %). Tests et lint frontend en CI. README aligné sur le code. Mailer >= 80 % de couverture. |

## 5. Lots proposés

| Lot | Contenu | IDs | Priorité |
|---|---|---|---|
| L1 | Sécurité des tokens, secrets, config | B1, B2, S8, S9 | P0 |
| L2 | Intégrité des réservations (transitions, atomicité, emails, doublons) | B3, B4, S3, S4, S18 | P0 |
| L3 | Comptes (emails, suppression, refresh/session) | B5, B6, B7, S1, S2, D7 | P0 |
| L4 | Conformité CLAUDE.md / RGPD front (`style=`, polices, Nominatim, CSV) | S10, S11, S12, S13 | P1 |
| L5 | Durcissement (CORS, rate limit, en-têtes, docs, visibilité) | S5, S6, S7, S14 | P1 |
| L6 | Migrations et déploiement | S15, S16, S17, D16, D17 | P1 |
| L7 | Refactor, tests front, README | D1–D6, D8–D15, D18, D19 | P2 |

## 6. Questions ouvertes

