"""
Fixtures pytest partagées pour tous les tests Avyro.

Chaque test démarre avec une base de données vide (SQLite in-memory) et
des clients HTTP frais — aucun état n'est partagé entre les tests.
"""
import pytest

from app import create_app
from app.extensions import db as _db


# ── Application et client HTTP ────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    """Crée une instance Flask en mode test avec une DB in-memory."""
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Client HTTP Flask pour les tests."""
    return app.test_client()


# ── Helpers d'inscription / connexion ────────────────────────────────────────

def register_and_login(client, email: str, password: str = "password123",
                       company_name: str | None = None) -> dict:
    """
    Inscrit un utilisateur et retourne le dict complet de la réponse
    (access_token, refresh_token, user).
    """
    payload = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": email.split("@")[0].capitalize(),
        "phone": "0600000000",
    }
    if company_name:
        payload["company_name"] = company_name

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, f"Register failed: {res.get_json()}"
    return res.get_json()


_siret_counter = 0


def auth_headers_for(client, email: str, password: str = "password123",
                     company_name: str | None = None,
                     with_siret: bool = False) -> dict:
    """
    Retourne les headers Authorization prêts à l'emploi.
    Si with_siret=True, patche la Company avec un SIRET unique (requis pour publier).
    """
    global _siret_counter
    data = register_and_login(client, email, password, company_name)
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    if with_siret:
        _siret_counter += 1
        siret = str(_siret_counter).zfill(14)
        client.patch(
            "/api/companies/me",
            headers=headers,
            json={"siret": siret},
        )
    return headers


# ── Fixtures nommées pour les tests ──────────────────────────────────────────

@pytest.fixture
def auth_headers(client):
    """Headers JWT pour alice@a.com avec SIRET (peut publier des offres)."""
    return auth_headers_for(client, "alice@a.com", company_name="Acme",
                            with_siret=True)


@pytest.fixture
def provider_headers(client):
    """Headers JWT pour le provider avec SIRET."""
    return auth_headers_for(client, "prov@example.com",
                            company_name="Prov Corp", with_siret=True)


@pytest.fixture
def booker_headers(client):
    """Headers JWT pour le booker (pas besoin de SIRET pour réserver)."""
    return auth_headers_for(client, "booker@example.com",
                            company_name="Booker Inc")


# ── Helpers de création de ressources ────────────────────────────────────────

def create_training(client, headers: dict, **overrides) -> dict:
    """Crée une formation via /api/trainings et retourne son dict."""
    payload = {
        "title": "Formation test",
        "contact_phone": "0600000000",
        "starts_at": "2026-09-01T09:00:00",
        "ends_at": "2026-09-01T17:00:00",
        "shared_seats": 5,
        "price_per_seat": 100.0,
        **overrides,
    }
    res = client.post("/api/trainings", headers=headers, json=payload)
    assert res.status_code == 201, f"Create training failed: {res.get_json()}"
    return res.get_json()


def create_room(client, headers: dict, **overrides) -> dict:
    """Crée une salle via /api/rooms et retourne son dict."""
    payload = {
        "title": "Salle test",
        "contact_phone": "0600000000",
        "starts_at": "2026-09-01T09:00:00",
        "ends_at": "2026-09-01T17:00:00",
        "shared_seats": 4,
        "price_per_seat": 50.0,
        **overrides,
    }
    res = client.post("/api/rooms", headers=headers, json=payload)
    assert res.status_code == 201, f"Create room failed: {res.get_json()}"
    return res.get_json()


def create_booking(client, headers: dict, training_id: int = None,
                   room_id: int = None, seats: int = 2) -> dict:
    """Crée une demande de réservation et retourne son dict."""
    body = {"seats": seats}
    if training_id is not None:
        body["training_id"] = training_id
    if room_id is not None:
        body["room_id"] = room_id
    res = client.post("/api/bookings", headers=headers, json=body)
    assert res.status_code == 201, f"Create booking failed: {res.get_json()}"
    return res.get_json()
