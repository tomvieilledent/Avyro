"""Tests de l'API Company (/api/companies/*)."""
from tests.conftest import auth_headers_for, register_and_login, create_training, create_room


# ── Consultation ──────────────────────────────────────────────────────────────

def test_get_my_company(client):
    headers = auth_headers_for(client, "co@x.com", company_name="My Firm")
    res = client.get("/api/companies/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "My Firm"
    assert data["kind"] == "pro"


def test_get_company_by_id(client):
    data = register_and_login(client, "by_id@x.com", company_name="Lookup Co")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]

    res = client.get(f"/api/companies/{company_id}", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["name"] == "Lookup Co"


def test_get_company_by_id_public_no_auth(client):
    """La fiche entreprise est accessible sans JWT."""
    data = register_and_login(client, "pub@x.com", company_name="Public Co")
    company_id = data["user"]["company_id"]
    res = client.get(f"/api/companies/{company_id}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Public Co"


def test_get_company_404(client):
    headers = auth_headers_for(client, "nf@x.com")
    res = client.get("/api/companies/9999", headers=headers)
    assert res.status_code == 404


# ── Mise à jour ───────────────────────────────────────────────────────────────

def test_update_company_as_admin(client):
    headers = auth_headers_for(client, "admin@x.com", company_name="Old Name")
    res = client.patch(
        "/api/companies/me",
        headers=headers,
        json={"name": "New Name", "siret": "12345678901234"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "New Name"
    assert data["siret"] == "12345678901234"


def test_update_company_contact_email(client):
    headers = auth_headers_for(client, "email_co@x.com", company_name="EmailCo")
    res = client.patch(
        "/api/companies/me",
        headers=headers,
        json={"contact_email": "contact@emailco.fr"},
    )
    assert res.status_code == 200
    assert res.get_json()["contact_email"] == "contact@emailco.fr"


def test_update_company_tags(client):
    headers = auth_headers_for(client, "tags_co@x.com", company_name="TagsCo")
    res = client.patch(
        "/api/companies/me",
        headers=headers,
        json={"tags": ["IT", "RH"]},
    )
    assert res.status_code == 200
    assert "IT" in res.get_json()["tags"]


def test_update_company_clear_siret(client):
    headers = auth_headers_for(client, "siret@x.com", company_name="Siret Co")
    client.patch("/api/companies/me", headers=headers, json={"siret": "123456789"})
    res = client.patch("/api/companies/me", headers=headers, json={"siret": None})
    assert res.status_code == 200
    assert res.get_json()["siret"] is None


def test_update_company_requires_admin(client, app):
    from app.extensions import db
    from app.models import User

    data = register_and_login(client, "adm@x.com", company_name="Corp")
    company_id = data["user"]["company_id"]

    with app.app_context():
        member = User(
            email="member@x.com",
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
        json={"email": "member@x.com", "password": "password123"},
    )
    member_headers = {
        "Authorization": f"Bearer {login_res.get_json()['access_token']}"
    }
    res = client.patch(
        "/api/companies/me", headers=member_headers, json={"name": "Hack"}
    )
    assert res.status_code == 403


# ── Offerings publiques ───────────────────────────────────────────────────────

def test_offerings_empty(client):
    data = register_and_login(client, "off@x.com", company_name="OffCo")
    company_id = data["user"]["company_id"]
    res = client.get(f"/api/companies/{company_id}/offerings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["trainings"] == []
    assert data["rooms"] == []


def test_offerings_includes_open_trainings(client):
    data = register_and_login(client, "off2@x.com", company_name="Off2Co")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]
    client.patch("/api/companies/me", headers=headers,
                 json={"siret": "12345678901234"})

    create_training(client, headers, title="Formation publique")

    res = client.get(f"/api/companies/{company_id}/offerings")
    assert res.status_code == 200
    assert len(res.get_json()["trainings"]) == 1


def test_offerings_includes_open_rooms(client):
    data = register_and_login(client, "off3@x.com", company_name="Off3Co")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]
    client.patch("/api/companies/me", headers=headers,
                 json={"siret": "12345678901234"})

    create_room(client, headers, title="Salle publique")

    res = client.get(f"/api/companies/{company_id}/offerings")
    assert len(res.get_json()["rooms"]) == 1


def test_offerings_excludes_closed_trainings(client):
    data = register_and_login(client, "off4@x.com", company_name="Off4Co")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]
    client.patch("/api/companies/me", headers=headers,
                 json={"siret": "12345678901234"})

    t = create_training(client, headers, title="Fermée")
    client.patch(f"/api/trainings/{t['id']}", headers=headers,
                 json={"status": "closed"})

    res = client.get(f"/api/companies/{company_id}/offerings")
    assert res.get_json()["trainings"] == []


# ── Invitation de membres ─────────────────────────────────────────────────────

def test_invite_sends_successfully(client, monkeypatch):
    """L'invite retourne 200 et envoie un email (mocké)."""
    from app.api import companies as co_module
    sent = []
    monkeypatch.setattr(co_module, "send_email", lambda **kw: sent.append(kw))

    headers = auth_headers_for(client, "inv_admin@x.com",
                               company_name="InvCo")
    res = client.post(
        "/api/companies/me/invite",
        headers=headers,
        json={"email": "newmember@x.com", "role": "member"},
    )
    assert res.status_code == 200
    assert len(sent) == 1


def test_invite_requires_admin(client, app):
    from app.extensions import db
    from app.models import User

    data = register_and_login(client, "inv_adm2@x.com", company_name="InvCo2")
    company_id = data["user"]["company_id"]

    with app.app_context():
        member = User(
            email="inv_mem@x.com",
            first_name="M",
            last_name="Em",
            phone="0600000000",
            role="member",
            company_id=company_id,
        )
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()

    login_res = client.post(
        "/api/auth/login",
        json={"email": "inv_mem@x.com", "password": "password123"},
    )
    member_headers = {
        "Authorization": f"Bearer {login_res.get_json()['access_token']}"
    }
    res = client.post(
        "/api/companies/me/invite",
        headers=member_headers,
        json={"email": "target@x.com"},
    )
    assert res.status_code == 403


def test_invite_duplicate_email_returns_409(client, monkeypatch):
    from app.api import companies as co_module
    monkeypatch.setattr(co_module, "send_email", lambda **kw: None)

    register_and_login(client, "existing@x.com")
    headers = auth_headers_for(client, "inv3@x.com", company_name="InvCo3")

    res = client.post(
        "/api/companies/me/invite",
        headers=headers,
        json={"email": "existing@x.com"},
    )
    assert res.status_code == 409
