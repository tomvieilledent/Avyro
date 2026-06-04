import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "a@a.com",
            "password": "password123",
            "first_name": "Alice",
            "last_name": "Martin",
            "phone": "0600000000",
            "company_name": "Acme",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "a@a.com", "password": "password123"},
    )
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
