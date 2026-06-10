"""
Seed de démonstration Avyro.
Remplace les données de formation/salle par des exemples cohérents
et renomme les companies avec des noms réalistes.
"""
import os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DATABASE_URL", "sqlite:////root/Holberton/Avyro/backend/dev.db")
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("SECRET_KEY", "dev-change-me")
os.environ.setdefault("JWT_SECRET_KEY", "dev-jwt-secret-please-change-me-32bytes")

from app import create_app
from app.extensions import db
from app.models.company import Company
from app.models.training import Training
from app.models.booking import Booking

app = create_app("development")

# ── Noms réalistes pour les companies ────────────────────────────────────────
COMPANY_NAMES = [
    "TechVision SAS",
    "FormaCap France",
    "Groupe Meridian",
    "Synergie Conseil",
    "DataLab Solutions",
    "Cap Formation",
    "Alliance Pro",
    "Sud Formation",
    "Novaformation",
]

# ── Données Training ──────────────────────────────────────────────────────────
TRAININGS = [
    {
        "title": "Excel Avancé & Power BI",
        "description": (
            "Maîtrisez les fonctions avancées d'Excel (tableaux croisés dynamiques, "
            "macros VBA) et créez vos premiers dashboards Power BI. "
            "Formation pratique avec cas d'usage réels en entreprise."
        ),
        "location": "75009 Paris — Espace Opéra",
        "contact_phone": "01 42 33 77 20",
        "starts_at": datetime(2026, 6, 25, 9, 0),
        "ends_at":   datetime(2026, 6, 26, 17, 30),
        "latitude": 48.8738,
        "longitude": 2.3311,
        "shared_seats": 6,
        "price_per_seat": 390.0,
    },
    {
        "title": "Leadership & Management d'équipe",
        "description": (
            "Développez votre posture de manager : communication bienveillante, "
            "gestion des conflits, conduite du changement et motivation d'équipe. "
            "Mises en situation et coaching collectif inclus."
        ),
        "location": "69003 Lyon — Centre de congrès",
        "contact_phone": "04 72 51 09 40",
        "starts_at": datetime(2026, 7, 3, 9, 0),
        "ends_at":   datetime(2026, 7, 4, 17, 0),
        "latitude": 45.7576,
        "longitude": 4.8324,
        "shared_seats": 4,
        "price_per_seat": 450.0,
    },
    {
        "title": "Marketing Digital & Réseaux Sociaux",
        "description": (
            "Stratégie de contenu, SEO, campagnes Google Ads et Meta Ads. "
            "Apprenez à mesurer vos performances avec Google Analytics 4 "
            "et à construire une présence digitale efficace."
        ),
        "location": "À distance",
        "is_remote": True,
        "contact_phone": "09 70 44 22 81",
        "starts_at": datetime(2026, 7, 10, 9, 30),
        "ends_at":   datetime(2026, 7, 10, 17, 30),
        "latitude": None,
        "longitude": None,
        "shared_seats": 10,
        "price_per_seat": 260.0,
    },
    {
        "title": "Gestion de projet Agile / Scrum",
        "description": (
            "Certification Scrum Master préparée en 2 jours : rôles, cérémonies, "
            "artefacts et mise en œuvre dans des équipes pluridisciplinaires. "
            "Passage de l'examen PSM I en fin de session."
        ),
        "location": "33000 Bordeaux — Cité Numérique",
        "contact_phone": "05 56 79 14 50",
        "starts_at": datetime(2026, 7, 14, 8, 30),
        "ends_at":   datetime(2026, 7, 15, 17, 30),
        "latitude": 44.8378,
        "longitude": -0.5792,
        "shared_seats": 5,
        "price_per_seat": 420.0,
    },
    {
        "title": "Cybersécurité pour les PME",
        "description": (
            "Comprendre les menaces actuelles (phishing, ransomware, BYOD) "
            "et mettre en place les bonnes pratiques : politique de mots de passe, "
            "sauvegardes, sensibilisation des collaborateurs, RGPD."
        ),
        "location": "75002 Paris — Sentier Tech Hub",
        "contact_phone": "01 55 34 92 10",
        "starts_at": datetime(2026, 8, 27, 9, 0),
        "ends_at":   datetime(2026, 8, 27, 17, 30),
        "latitude": 48.8651,
        "longitude": 2.3516,
        "shared_seats": 8,
        "price_per_seat": 310.0,
    },
    {
        "title": "Prise de parole en public",
        "description": (
            "Structurer et délivrer un discours percutant. Gestion du trac, "
            "techniques de présentation visuelle, improvisation maîtrisée. "
            "Training intensif avec vidéo-coaching et retours individualisés."
        ),
        "location": "À distance",
        "is_remote": True,
        "contact_phone": "09 81 77 30 45",
        "starts_at": datetime(2026, 9, 4, 9, 0),
        "ends_at":   datetime(2026, 9, 4, 17, 0),
        "latitude": None,
        "longitude": None,
        "shared_seats": 12,
        "price_per_seat": 220.0,
    },
    {
        "title": "Droit du travail : actualités 2026",
        "description": (
            "Panorama des évolutions législatives récentes : réforme du temps de "
            "travail, télétravail, rupture conventionnelle et contentieux prud'homal. "
            "Animé par un avocat spécialisé en droit social."
        ),
        "location": "44000 Nantes — Quartier Euronantes",
        "contact_phone": "02 40 47 88 21",
        "starts_at": datetime(2026, 9, 11, 9, 0),
        "ends_at":   datetime(2026, 9, 11, 17, 30),
        "latitude": 47.2184,
        "longitude": -1.5536,
        "shared_seats": 5,
        "price_per_seat": 380.0,
    },
    {
        "title": "IA & Automatisation des processus métier",
        "description": (
            "Identifier les usages concrets de l'IA générative en entreprise : "
            "automatisation documentaire, analyse de données, chatbots internes. "
            "Atelier Make (Integromat) et découverte de Copilot 365."
        ),
        "location": "75013 Paris — Station F",
        "contact_phone": "01 89 16 42 70",
        "starts_at": datetime(2026, 9, 24, 9, 0),
        "ends_at":   datetime(2026, 9, 25, 17, 30),
        "latitude": 48.8301,
        "longitude": 2.3641,
        "shared_seats": 6,
        "price_per_seat": 510.0,
    },
]

# ── Données Room ──────────────────────────────────────────────────────────────
ROOMS = [
    {
        "title": "Salle Lumière — 12 personnes",
        "description": (
            "Salle de réunion lumineuse au cœur du 8ème arrondissement. "
            "Équipée d'un écran interactif 75\", système de visioconférence Logitech Rally, "
            "tableau blanc digital et connexion fibre 1 Gbps. Café et eau inclus."
        ),
        "location": "75008 Paris — Rue du Faubourg Saint-Honoré",
        "contact_phone": "01 42 65 30 10",
        "starts_at": datetime(2026, 6, 23, 8, 0),
        "ends_at":   datetime(2026, 6, 27, 18, 0),
        "latitude": 48.8726,
        "longitude": 2.309,
        "shared_seats": 12,
        "price_per_seat": 18.0,
    },
    {
        "title": "Espace Confluence — 20 personnes",
        "description": (
            "Grand espace modulable idéal pour séminaires, ateliers et workshops. "
            "Tables repositionnables, 2 écrans 65\", système audio intégré. "
            "À 5 min de la gare Part-Dieu. Parking possible sur demande."
        ),
        "location": "69003 Lyon — Quartier Part-Dieu",
        "contact_phone": "04 78 62 19 33",
        "starts_at": datetime(2026, 7, 1, 7, 30),
        "ends_at":   datetime(2026, 7, 31, 19, 0),
        "latitude": 45.7576,
        "longitude": 4.8324,
        "shared_seats": 20,
        "price_per_seat": 12.0,
    },
    {
        "title": "Studio de formation équipé — 15 places",
        "description": (
            "Studio spécialement conçu pour les formations en présentiel. "
            "Sièges ergonomiques, 15 postes informatiques, logiciels professionnels "
            "préinstallés (Office 365, Adobe, outils métier). Climatisation, accès PMR."
        ),
        "location": "33000 Bordeaux — Cité Numérique Bâtiment B",
        "contact_phone": "05 57 22 48 90",
        "starts_at": datetime(2026, 7, 6, 8, 0),
        "ends_at":   datetime(2026, 8, 29, 18, 0),
        "latitude": 44.8378,
        "longitude": -0.5792,
        "shared_seats": 15,
        "price_per_seat": 22.0,
    },
    {
        "title": "Salle de conseil panoramique — La Défense",
        "description": (
            "Salle prestige avec vue panoramique sur Paris depuis le 18ème étage. "
            "Mobilier haut de gamme, écran 86\", système de présentation sans fil Barco, "
            "service traiteur disponible. Idéale pour comités de direction et investisseurs."
        ),
        "location": "92400 Courbevoie — La Défense, Tour Ariane",
        "contact_phone": "01 46 35 77 00",
        "starts_at": datetime(2026, 6, 24, 8, 0),
        "ends_at":   datetime(2026, 9, 30, 20, 0),
        "latitude": 48.8917,
        "longitude": 2.2421,
        "shared_seats": 10,
        "price_per_seat": 45.0,
    },
    {
        "title": "Espace coworking & réunion modulable — 25 places",
        "description": (
            "Espace ouvert transformable : réunion plénière, groupes de travail ou "
            "open-space partagé. Wifi 2 Gbps, imprimantes, café illimité, casiers sécurisés. "
            "En plein centre de Nantes, à 3 min du tramway."
        ),
        "location": "44200 Nantes — Île de Nantes",
        "contact_phone": "02 51 83 60 44",
        "starts_at": datetime(2026, 7, 1, 7, 0),
        "ends_at":   datetime(2026, 9, 30, 20, 0),
        "latitude": 47.2052,
        "longitude": -1.5681,
        "shared_seats": 25,
        "price_per_seat": 9.0,
    },
    {
        "title": "Salle de réunion premium — Marseille Vieux-Port",
        "description": (
            "Salle lumineuse avec vue sur le Vieux-Port. Capacité 8 personnes, "
            "écran interactif, système de visioconférence intégré, accueil personnalisé. "
            "Idéale pour réunions clients, entretiens RH ou sessions de coaching."
        ),
        "location": "13001 Marseille — Quai du Port",
        "contact_phone": "04 91 54 28 63",
        "starts_at": datetime(2026, 6, 24, 8, 0),
        "ends_at":   datetime(2026, 9, 30, 19, 0),
        "latitude": 43.2965,
        "longitude": 5.3698,
        "shared_seats": 8,
        "price_per_seat": 25.0,
    },
]


with app.app_context():
    conn = db.engine.raw_connection()
    cur  = conn.cursor()

    # ── 1. Renommage des companies ────────────────────────────────────────────
    cur.execute("SELECT id FROM companies ORDER BY id")
    ids = [row[0] for row in cur.fetchall()]
    for i, cid in enumerate(ids):
        if i < len(COMPANY_NAMES):
            cur.execute("UPDATE companies SET name=? WHERE id=?", (COMPANY_NAMES[i], cid))
    print(f"Companies renommées : {len(ids)}")

    # ── 2. Suppression de toutes les données existantes ───────────────────────
    cur.execute("DELETE FROM bookings")
    cur.execute("DELETE FROM trainings")
    cur.execute("DELETE FROM rooms")
    print("Trainings, rooms et réservations existants supprimés.")

    now = datetime.utcnow().isoformat()
    n = len(ids)

    # ── 3. Insertion des formations (table trainings) ─────────────────────────
    sql_training = """
        INSERT INTO trainings
          (kind, title, description, location, is_remote, contact_phone,
           starts_at, ends_at, latitude, longitude,
           total_seats, shared_seats, price_per_seat,
           status, reminder_sent, provider_id, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    for i, data in enumerate(TRAININGS):
        provider_id = ids[i % n]
        cur.execute(sql_training, (
            "training",
            data["title"], data["description"],
            data.get("location", ""), int(data.get("is_remote", False)),
            data["contact_phone"],
            data["starts_at"].isoformat(), data["ends_at"].isoformat(),
            data.get("latitude"), data.get("longitude"),
            data["shared_seats"], data["shared_seats"],
            data["price_per_seat"],
            "open", 0, provider_id, now, now,
        ))
    print(f"{len(TRAININGS)} formations Training insérées.")

    # ── 4. Insertion des salles (table rooms) ─────────────────────────────────
    sql_room = """
        INSERT INTO rooms
          (title, description, location, is_remote, contact_phone,
           starts_at, ends_at, latitude, longitude,
           shared_seats, price_per_seat,
           status, reminder_sent, provider_id, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    for i, data in enumerate(ROOMS):
        provider_id = ids[(i + 2) % n]
        cur.execute(sql_room, (
            data["title"], data["description"],
            data.get("location", ""), 0,
            data["contact_phone"],
            data["starts_at"].isoformat(), data["ends_at"].isoformat(),
            data.get("latitude"), data.get("longitude"),
            data["shared_seats"],
            data["price_per_seat"],
            "open", 0, provider_id, now, now,
        ))
    print(f"{len(ROOMS)} salles Room insérées.")

    conn.commit()
    conn.close()

    print(f"\n✓ Seed démo terminé.")
    print(f"  {len(TRAININGS)} formations Training · {len(ROOMS)} salles Room")
    raw = db.engine.raw_connection()
    cr  = raw.cursor()
    cr.execute("""
        SELECT c.name,
               (SELECT COUNT(*) FROM trainings t WHERE t.provider_id=c.id) AS tr,
               (SELECT COUNT(*) FROM rooms r WHERE r.provider_id=c.id) AS ro
        FROM companies c ORDER BY c.id
    """)
    for row in cr.fetchall():
        print(f"  {row[0]} → {row[1]} formation(s) · {row[2]} salle(s)")
    raw.close()
