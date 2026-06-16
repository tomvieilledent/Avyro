"""Tests de l'API d'authentification (/api/auth/*)."""
from flask_jwt_extended import create_access_token

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


def test_register_short_password_returns_422(client):
    res = client.post(
        "/api/auth/register",
        json={
            "email": "short@x.com",
            "password": "123",
            "first_name": "A",
            "last_name": "B",
            "phone": "0600000000",
        },
    )
    assert res.status_code == 422


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


def test_login_missing_field_returns_422(client):
    res = client.post("/api/auth/login", json={"email": "a@x.com"})
    assert res.status_code == 422


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_refresh_token(client):
    data = register_and_login(client, "r@x.com")
    refresh_headers = {"Authorization": f"Bearer {data['refresh_token']}"}
    res = client.post("/api/auth/refresh", headers=refresh_headers)
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_refresh_with_access_token_fails(client):
    data = register_and_login(client, "rr@x.com")
    access_headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = client.post("/api/auth/refresh", headers=access_headers)
    assert res.status_code == 422


def test_refresh_without_token_returns_401(client):
    res = client.post("/api/auth/refresh")
    assert res.status_code == 401


# ── /me : consultation du profil ──────────────────────────────────────────────

def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_user(client):
    headers = auth_headers_for(client, "me@x.com")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["email"] == "me@x.com"
    assert "company_id" in data


# ── /me : mise à jour du profil ───────────────────────────────────────────────

def test_update_profile_name(client):
    headers = auth_headers_for(client, "upd@x.com")
    res = client.patch(
        "/api/auth/me",
        headers=headers,
        json={"first_name": "Nouveau", "last_name": "Nom"},
    )
    assert res.status_code == 200
    assert res.get_json()["full_name"] == "Nouveau Nom"


def test_update_profile_phone(client):
    headers = auth_headers_for(client, "phone@x.com")
    res = client.patch(
        "/api/auth/me", headers=headers, json={"phone": "0700000001"}
    )
    assert res.status_code == 200
    assert res.get_json()["phone"] == "0700000001"


def test_update_profile_email(client):
    headers = auth_headers_for(client, "old@x.com")
    res = client.patch(
        "/api/auth/me", headers=headers, json={"email": "new@x.com"}
    )
    assert res.status_code == 200
    assert res.get_json()["email"] == "new@x.com"


def test_update_profile_duplicate_email_returns_409(client):
    auth_headers_for(client, "taken@x.com")
    headers = auth_headers_for(client, "other@x.com")
    res = client.patch(
        "/api/auth/me", headers=headers, json={"email": "taken@x.com"}
    )
    assert res.status_code == 409


def test_update_profile_password_then_login(client):
    """Après changement de mot de passe, l'ancien ne fonctionne plus."""
    register_and_login(client, "pw@x.com", password="oldpassword")
    headers = auth_headers_for(client, "pw2@x.com", password="oldpassword")
    client.patch(
        "/api/auth/me", headers=headers, json={"password": "newpassword123"}
    )
    # Nouveau mot de passe fonctionne
    res = client.post(
        "/api/auth/login",
        json={"email": "pw2@x.com", "password": "newpassword123"},
    )
    assert res.status_code == 200
    # Ancien mot de passe ne fonctionne plus
    res2 = client.post(
        "/api/auth/login",
        json={"email": "pw2@x.com", "password": "oldpassword"},
    )
    assert res2.status_code == 401


def test_update_profile_requires_auth(client):
    res = client.patch("/api/auth/me", json={"first_name": "X"})
    assert res.status_code == 401


# ── /me : suppression du compte ───────────────────────────────────────────────

def test_delete_account_last_admin_deletes_company(client, app):
    """Le dernier admin d'une Company supprime aussi la Company."""
    from app.extensions import db
    from app.models import Company

    data = register_and_login(client, "del@x.com", company_name="ToDelete")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]

    res = client.delete("/api/auth/me", headers=headers)
    assert res.status_code == 200

    with app.app_context():
        assert db.session.get(Company, company_id) is None


def test_delete_account_member_keeps_company(client, app):
    """Un membre supprimé ne supprime pas la Company."""
    from app.extensions import db
    from app.models import User

    data = register_and_login(client, "adm2@x.com", company_name="Corp")
    company_id = data["user"]["company_id"]

    with app.app_context():
        member = User(
            email="member2@x.com",
            first_name="M",
            last_name="Ember",
            phone="0600000000",
            role="member",
            company_id=company_id,
        )
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()

    login_res = client.post(
        "/api/auth/login",
        json={"email": "member2@x.com", "password": "password123"},
    )
    member_headers = {
        "Authorization": f"Bearer {login_res.get_json()['access_token']}"
    }
    client.delete("/api/auth/me", headers=member_headers)

    # La Company existe toujours
    admin_headers = {"Authorization": f"Bearer {data['access_token']}"}
    res = client.get(f"/api/companies/{company_id}", headers=admin_headers)
    assert res.status_code == 200


def test_delete_account_requires_auth(client):
    assert client.delete("/api/auth/me").status_code == 401


# ── /me/export : portabilité RGPD ────────────────────────────────────────────

def test_export_personal_data_structure(client):
    headers = auth_headers_for(client, "export@x.com")
    res = client.get("/api/auth/me/export", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "user" in data
    assert "company" in data
    assert "bookings" in data
    assert data["user"]["email"] == "export@x.com"


def test_export_requires_auth(client):
    assert client.get("/api/auth/me/export").status_code == 401


# ── /accept-invite : invitation ───────────────────────────────────────────────

def test_accept_invite_success(client, app):
    """Crée un compte depuis un token d'invitation valide."""
    data = register_and_login(client, "admin_inv@x.com", company_name="InvCorp")
    admin_headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]

    # Génère un token d'invitation directement (sans email SMTP)
    with app.app_context():
        from datetime import timedelta
        token = create_access_token(
            identity="invite:invited@x.com",
            expires_delta=timedelta(days=7),
            additional_claims={
                "invite": True,
                "invite_email": "invited@x.com",
                "invite_role": "member",
                "company_id": company_id,
            },
        )

    res = client.post(
        "/api/auth/accept-invite",
        json={
            "token": token,
            "first_name": "New",
            "last_name": "Member",
            "phone": "0600000000",
            "password": "password123",
        },
    )
    assert res.status_code == 201
    resp = res.get_json()
    assert resp["user"]["company_id"] == company_id
    assert resp["user"]["role"] == "member"


def test_accept_invite_invalid_token_returns_400(client):
    res = client.post(
        "/api/auth/accept-invite",
        json={
            "token": "not.a.valid.token",
            "first_name": "X",
            "last_name": "Y",
            "phone": "0600000000",
            "password": "password123",
        },
    )
    assert res.status_code == 400


def test_accept_invite_duplicate_email_returns_409(client, app):
    """Email déjà utilisé → 409."""
    register_and_login(client, "taken_inv@x.com")
    data = register_and_login(client, "adminx@x.com", company_name="CorpX")
    company_id = data["user"]["company_id"]

    with app.app_context():
        from datetime import timedelta
        token = create_access_token(
            identity="invite:taken_inv@x.com",
            expires_delta=timedelta(days=7),
            additional_claims={
                "invite": True,
                "invite_email": "taken_inv@x.com",
                "invite_role": "member",
                "company_id": company_id,
            },
        )

    res = client.post(
        "/api/auth/accept-invite",
        json={
            "token": token,
            "first_name": "X",
            "last_name": "Y",
            "phone": "0600000000",
            "password": "password123",
        },
    )
    assert res.status_code == 409
