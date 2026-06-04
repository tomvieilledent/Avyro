def _register(client, email, company):
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Test",
            "last_name": email,
            "phone": "0600000000",
            "company_name": company,
        },
    )
    res = client.post(
        "/api/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {res.get_json()['access_token']}"}


def _setup_training_and_booking(client):
    provider = _register(client, "prov@a.com", "Acme")
    booker = _register(client, "book@b.com", "Globex")
    tid = client.post(
        "/api/trainings",
        headers=provider,
        json={
            "title": "T",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
        },
    ).get_json()["id"]
    bid = client.post(
        "/api/bookings",
        headers=booker,
        json={"training_id": tid, "seats": 2},
    ).get_json()["id"]
    return provider, booker, tid, bid


def test_unsubscribe_pending_ok(client):
    _, booker, _, bid = _setup_training_and_booking(client)
    res = client.delete(f"/api/bookings/{bid}", headers=booker)
    assert res.status_code == 200


def test_unsubscribe_confirmed_rejected(client):
    provider, booker, _, bid = _setup_training_and_booking(client)
    client.patch(
        f"/api/bookings/{bid}", headers=provider, json={"status": "confirmed"}
    )
    res = client.delete(f"/api/bookings/{bid}", headers=booker)
    assert res.status_code == 400
