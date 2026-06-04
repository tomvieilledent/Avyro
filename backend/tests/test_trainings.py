def _create_training(client, headers):
    return client.post(
        "/api/trainings",
        headers=headers,
        json={
            "title": "Sécurité incendie",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 4,
            "price_per_seat": 150,
        },
    )


def test_create_and_list_training(client, auth_headers):
    res = _create_training(client, auth_headers)
    assert res.status_code == 201
    assert res.get_json()["available_seats"] == 4

    res = client.get("/api/trainings?mine=true", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_shared_seats_required(client, auth_headers):
    res = client.post(
        "/api/trainings",
        headers=auth_headers,
        json={
            "title": "x",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
        },
    )
    assert res.status_code == 422
