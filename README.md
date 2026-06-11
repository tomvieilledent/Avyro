# Avyro

> **Plateforme B2B de mutualisation entre entreprises**

Avyro permet aux entreprises de rentabiliser leurs ressources inutilisées en les mettant à disposition d'autres structures. La plateforme est bimodale : chaque compte accède aux deux services avec un seul login.

---

## Concept

Les entreprises disposent régulièrement de ressources sous-utilisées :

- Une **formation** organisée en interne avec des places restantes
- Une **salle de réunion** inoccupée sur certains créneaux

Avyro connecte les entreprises qui ont ces ressources avec celles qui en ont besoin — et leur permet de **partager les coûts** ou **générer des revenus complémentaires**.

---

## Deux services, un seul compte

### Avyro Training
Mutualisez vos formations inter-entreprises. Publiez vos places restantes, fixez un prix par place, recevez des demandes de réservation et confirmez les inscrits. L'objectif : ne plus payer seul une formation dont les places sont à moitié vides.

### Avyro Room
Sous-louez vos salles de réunion inoccupées. Publiez vos créneaux disponibles, gérez les demandes et rentabilisez des espaces qui coûtent de l'argent même sans personne dedans.

---

## Fonctionnalités actuelles

### Gestion des offres
- **Publication** d'une formation ou salle avec titre, description, dates de début/fin, lieu ou mode distanciel, nombre de places proposées, prix par place et tags métier
- **Édition et suppression** des offres publiées par le provider
- **Statuts automatiques** : ouverte, complète (places épuisées), en cours, terminée
- **Tags** libres pour catégoriser les offres (IT, Management, RH, Sécurité, Langues…)
- **Mode distanciel** : les offres à distance sont signalées et toujours incluses dans les recherches géolocalisées

### Catalogue et recherche
- **Recherche textuelle** sur le titre, le lieu et la description
- **Filtre par tag** via un menu déroulant dans la barre de recherche
- **Géolocalisation** : filtre "Autour de moi" basé sur la position GPS du navigateur avec rayon configurable (5 / 10 / 25 / 50 / 100 km) — algorithme Haversine
- **Filtres avancés** combinables : plage de dates, prix maximum, nombre de places minimum, distanciel uniquement
- **Indicateur de remplissage** par carte : vert < 60 %, orange < 90 %, rouge ≥ 90 %
- **Vue liste** (défaut) et **vue calendrier mensuelle** avec navigation mois par mois — les jours avec des offres affichent un point bleu, un clic révèle le détail

### Système de réservation
- Demande de réservation avec choix du nombre de places et note optionnelle (500 car.) pour le provider
- Cycle complet : `pending → confirmed / cancelled`
- Le provider confirme ou refuse depuis l'onglet "Demandes reçues"
- Le demandeur peut annuler une réservation en attente
- Badge de notification en temps réel sur l'onglet "Demandes reçues"

### Notifications email
Emails transactionnels envoyés automatiquement à chaque étape clé :

| Événement | Destinataire |
|-----------|-------------|
| Nouvelle demande reçue | Provider |
| Réservation confirmée | Demandeur |
| Réservation refusée | Demandeur |
| Annulation par le demandeur | Provider |

### Comptes rendus et export
- Onglet **Comptes rendus** : liste des inscrits confirmés par offre
- **Export CSV** directement depuis le navigateur (structure, places, contact, email) — sans appel API supplémentaire
- **Rappel automatique** par email au provider 1 jour ouvré avant le début d'une offre, avec la liste live des inscrits

### Gestion d'équipe et de structure
- Compte **admin** (créateur de la structure) et **membres**
- Invitation de collaborateurs par email avec lien JWT (valable 7 jours)
- Page de profil pour modifier ses informations personnelles et les données de la structure
- Fiche publique entreprise (`/company.html?id=...`) listant les offres actives d'une structure

### Sécurité et conformité RGPD
- Authentification JWT avec access token (30 min) et refresh token
- **Droit d'accès** : données visibles dans le profil
- **Droit de rectification** : modification du profil et de la structure
- **Droit à l'effacement** : suppression du compte avec cascade (formations, salles, réservations, structure si dernier admin)
- **Droit à la portabilité** : export JSON de toutes les données personnelles
- Consentement explicite à l'inscription avec lien vers la politique de confidentialité

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12 · Flask 3 · SQLAlchemy 2 · Flask-JWT-Extended |
| API docs | flask-smorest (OpenAPI 3.0 / Swagger UI) |
| Base de données | SQLite (dev) · PostgreSQL (prod) |
| Migrations | Alembic via Flask-Migrate |
| Frontend | HTML5 · Tailwind CSS v3 · JavaScript vanilla |
| Police | Inter (Google Fonts) |
| Emails | SMTP + APScheduler |
| Serveur | Gunicorn |
| Tests | pytest 8 · pytest-cov (63 tests) |

---

## Fonctionnalités envisagées

### Expérience utilisateur
- [ ] **PWA / application mobile** — accès hors ligne, notifications push, icône sur l'écran d'accueil
- [ ] **Tableau de bord analytique** — revenus générés, taux de remplissage historique, popularité des offres
- [ ] **Système d'avis** — notation des providers après une réservation confirmée
- [ ] **Liste d'attente** — s'inscrire sur une formation complète et être notifié en cas de désistement
- [ ] **Offres récurrentes** — publier une formation qui se répète chaque mois sans ressaisie
- [ ] **Vue carte** — affichage des offres sur une carte interactive (Leaflet / MapLibre)

### Fonctionnalités métier
- [ ] **Paiement intégré** — facturation en ligne via Stripe avec génération de facture PDF
- [ ] **Forfaits multi-places** — réserver un bloc de places à tarif dégressif
- [ ] **Contrats de sous-location** — génération automatique d'un PDF signable entre les parties
- [ ] **Vérification d'entreprise** — badge "structure vérifiée" après contrôle du SIRET
- [ ] **Messagerie interne** — fil de discussion par réservation entre demandeur et provider
- [ ] **Catalogue public** — accès en lecture sans compte pour favoriser l'acquisition

### Intégrations
- [ ] **Synchronisation agenda** — export iCal / Google Calendar / Outlook des réservations confirmées
- [ ] **SSO / SAML** — connexion via le compte d'entreprise (Azure AD, Okta…)
- [ ] **Webhooks** — notifications vers des outils tiers (Slack, Teams, Zapier) à chaque événement de réservation
- [ ] **API publique** — permettre aux entreprises d'intégrer Avyro dans leurs propres outils RH ou LMS

### Administration et conformité
- [ ] **Interface admin** — panneau de supervision des structures, offres et réservations
- [ ] **Multi-langue** — internationalisation (i18n) EN / FR / DE
- [ ] **Archivage légal** — conservation des contrats et historiques de réservations sur 5 ans

---

## Lancement rapide

```bash
./run-local.sh
```

Le script :
1. Crée un venv Python et installe les dépendances
2. Recompile le CSS Tailwind (si npm est disponible)
3. Crée les tables SQLite si nécessaire
4. Démarre Gunicorn sur **http://localhost:8080**

> Swagger UI disponible sur **http://localhost:8080/api/docs**

### Seed de démonstration

```bash
cd backend
python3 seed_demo.py
```

Peuple la base avec 8 formations, 6 salles et des entreprises aux noms réalistes.

---

## Structure du projet

```
Avyro/
├── backend/
│   ├── app/
│   │   ├── api/            # Blueprints REST (auth, companies, trainings, rooms, bookings)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Marshmallow schemas (validation + sérialisation)
│   │   ├── services/       # Mailer SMTP + scheduler APScheduler
│   │   └── utils/          # Auth helpers, Haversine
│   ├── tests/              # 63 tests pytest
│   ├── seed_demo.py
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   ├── index.html          # Page d'accueil publique
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html      # Tableau de bord bimodal
│   ├── profile.html
│   ├── company.html        # Fiche publique entreprise
│   ├── invite.html         # Acceptation d'invitation
│   ├── privacy.html        # Politique de confidentialité
│   ├── src/
│   │   ├── api.js          # Client HTTP (JWT + fetch)
│   │   ├── dashboard.js    # Logique dashboard
│   │   ├── profile.js
│   │   └── input.css       # Source Tailwind CSS
│   └── dist/styles.css     # CSS compilé
├── CLAUDE.md               # Règles de développement
├── run-local.sh
└── README.md
```

---

## Variables d'environnement

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `DATABASE_URL` | oui | `sqlite:///dev.db` ou `postgresql://...` |
| `SECRET_KEY` | oui | Clé Flask |
| `JWT_SECRET_KEY` | oui | Clé signature JWT (min. 32 caractères) |
| `SERVE_FRONTEND` | non | Chemin du dossier frontend (Flask sert les fichiers statiques) |
| `RUN_SCHEDULER` | non | `1` pour activer APScheduler |
| `MAIL_SERVER` | non | Serveur SMTP (défaut : log fichier `dev_outbox.log`) |
| `MAIL_PORT` | non | Port SMTP (défaut : 587) |
| `MAIL_USERNAME` | non | Identifiant SMTP |
| `MAIL_PASSWORD` | non | Mot de passe SMTP |
| `MAIL_FROM` | non | Adresse expéditeur |

---

## Tests

```bash
cd backend
pytest                          # tous les tests
pytest --cov=app                # avec couverture
pytest tests/test_trainings.py  # un fichier spécifique
```

---

## Développement frontend

```bash
cd frontend
npm run build   # compilation one-shot
npm run watch   # recompilation automatique à la sauvegarde
npm run format  # formatage Prettier des fichiers HTML
```
