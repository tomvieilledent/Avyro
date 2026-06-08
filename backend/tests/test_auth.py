"""Tests de l'API d'authentification (/api/auth/*)."""
from tests.conftest import register_and_login, auth_headers_for


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


# ── Inscription ───────────────────────────────────────────────────────────────

def test_register_returns_tokens(client):
    data = register_and_login(client, "bob@example.com", company_name="Globex")
    assert "access_token" in data
    assert "refresh_token" in data
    user = data["user"]
    assert user["email"] == "bob@example.com"
    assert user["role"] == "admin"


def test_register_creates_company_from_name(client):
    data = register_and_login(client, "c@c.com", company_name="My Corp")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company = client.get("/api/companies/me", headers=headers).get_json()
    assert company["name"] == "My Corp"
    assert company["kind"] == "pro"


def test_register_defaults_company_to_full_name(client):
    """Sans company_name, la Company prend le nom complet de l'utilisateur."""
    res = client.post(
        "/api/auth/register",
        json={
            "email": "jane@x.com",
            "password": "pass1234",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "0600000000",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company = client.get("/api/companies/me", headers=headers).get_json()
    assert company["name"] == "Jane Doe"
    assert company["kind"] == "private"


def test_register_duplicate_email_returns_409(client):
    register_and_login(client, "dup@x.com")
    res = client.post(
        "/api/auth/register",
        json={
            "email": "dup@x.com",
            "password": "pass1234",
            "first_name": "A",
            "last_name": "B",
            "phone": "0600000000",
        },
    )
    assert res.status_code == 409
    assert res.get_json()["error"] == "conflict"


def test_register_missing_required_field_returns_422(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "x@x.com", "password": "pass1234"},
    )
    assert res.status_code == 422
    assert res.get_json()["error"] == "validation"


# ── Connexion ─────────────────────────────────────────────────────────────────

def test_login_success(client):
    register_and_login(client, "alice@x.com")
    res = client.post(
        "/api/auth/login",
        json={"email": "alice@x.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_login_bad_password_returns_401(client):
    register_and_login(client, "bob@x.com")
    res = client.post(
        "/api/auth/login",
        json={"email": "bob@x.com", "password": "wrong"},
    )
    assert res.status_code == 401
    assert res.get_json()["error"] == "unauthorized"


def test_login_unknown_email_returns_401(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@x.com", "password": "pass1234"},
    )
    assert res.status_code == 401


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_refresh_token(client):
    data = register_and_login(client, "r@x.com")
    refresh_headers = {"Authorization": f"Bearer {data['refresh_token']}"}
    res = client.post("/api/auth/refresh", headers=refresh_headers)
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_refresh_with_access_token_fails(client):
    """Le refresh endpoint nécessite le refresh token, pas l'access token."""
    data = register_and_login(client, "rr@x.com")
    access_headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = client.post("/api/auth/refresh", headers=access_headers)
    assert res.status_code == 422


# ── /me : profil ──────────────────────────────────────────────────────────────

def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_user(client):
    headers = auth_headers_for(client, "me@x.com")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["email"] == "me@x.com"


def test_update_profile_name(client):
    headers = auth_headers_for(client, "upd@x.com")
    res = client.patch(
        "/api/auth/me",
        headers=headers,
        json={"first_name": "Nouveau", "last_name": "Nom"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["full_name"] == "Nouveau Nom"


def test_update_profile_email(client):
    headers = auth_headers_for(client, "old@x.com")
    res = client.patch(
        "/api/auth/me",
        headers=headers,
        json={"email": "new@x.com"},
    )
    assert res.status_code == 200
    assert res.get_json()["email"] == "new@x.com"


def test_update_profile_duplicate_email_returns_409(client):
    auth_headers_for(client, "taken@x.com")
    headers = auth_headers_for(client, "other@x.com")
    res = client.patch(
        "/api/auth/me",
        headers=headers,
        json={"email": "taken@x.com"},
    )
    assert res.status_code == 409
