"""Tests de l'API Company (/api/companies/*)."""
from tests.conftest import auth_headers_for, register_and_login


def test_get_my_company(client):
    headers = auth_headers_for(client, "co@x.com", company_name="My Firm")
    res = client.get("/api/companies/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "My Firm"
    assert data["kind"] == "pro"


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


def test_update_company_requires_admin(client, app):
    """Un utilisateur 'member' ne peut pas modifier la Company."""
    from app.extensions import db
    from app.models import User

    # Crée un admin et récupère son company_id
    data = register_and_login(client, "adm@x.com", company_name="Corp")
    company_id = data["user"]["company_id"]

    # Crée un member dans la même company directement en DB
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
        "/api/companies/me",
        headers=member_headers,
        json={"name": "Hack"},
    )
    assert res.status_code == 403


def test_get_company_by_id(client):
    data = register_and_login(client, "by_id@x.com", company_name="Lookup Co")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    company_id = data["user"]["company_id"]

    res = client.get(f"/api/companies/{company_id}", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["name"] == "Lookup Co"


def test_get_company_404(client):
    headers = auth_headers_for(client, "nf@x.com")
    res = client.get("/api/companies/9999", headers=headers)
    assert res.status_code == 404


def test_update_company_clear_siret(client):
    """Envoyer siret=null efface la valeur."""
    headers = auth_headers_for(client, "siret@x.com", company_name="Siret Co")
    client.patch("/api/companies/me", headers=headers, json={"siret": "123456789"})
    res = client.patch("/api/companies/me", headers=headers, json={"siret": None})
    assert res.status_code == 200
    assert res.get_json()["siret"] is None
