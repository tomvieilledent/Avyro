def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_register_and_login(client):
    res = client.post(
        "/api/auth/register",
        json={
            "email": "b@b.com",
            "password": "password123",
            "first_name": "Bob",
            "last_name": "Durand",
            "phone": "0600000000",
            "company_name": "Globex",
        },
    )
    assert res.status_code == 201
    assert "access_token" in res.get_json()

    res = client.post(
        "/api/auth/login",
        json={"email": "b@b.com", "password": "password123"},
    )
    assert res.status_code == 200


def test_login_bad_credentials(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "x@x.com", "password": "nope"},
    )
    assert res.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_update_profile(client, auth_headers):
    res = client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"first_name": "Alice", "last_name": "Bernard", "email": "alice@new.com"},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["full_name"] == "Alice Bernard"
    assert body["email"] == "alice@new.com"
