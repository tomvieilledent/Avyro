"""Tests de l'API Training (/api/trainings/*)."""
from tests.conftest import (
    auth_headers_for,
    create_training,
    register_and_login,
)


# ── Création ──────────────────────────────────────────────────────────────────

def test_create_training_success(client, auth_headers):
    t = create_training(client, auth_headers)
    assert t["available_seats"] == 5
    assert t["booked_seats"] == 0
    assert t["status"] == "open"
    assert t["kind"] == "training"  # Par défaut


def test_create_room(client, auth_headers):
    t = create_training(client, auth_headers, kind="room", title="Salle A")
    assert t["kind"] == "room"


def test_create_training_missing_title_returns_422(client, auth_headers):
    res = client.post(
        "/api/trainings",
        headers=auth_headers,
        json={
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
        },
    )
    assert res.status_code == 422
    assert "title" in res.get_json()["messages"]


def test_create_training_ends_before_starts_returns_422(client, auth_headers):
    res = client.post(
        "/api/trainings",
        headers=auth_headers,
        json={
            "title": "T",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T17:00:00",
            "ends_at": "2026-09-01T09:00:00",
            "shared_seats": 5,
        },
    )
    assert res.status_code == 422


def test_create_training_requires_auth(client):
    res = client.post("/api/trainings", json={"title": "T"})
    assert res.status_code == 401


# ── Listing ───────────────────────────────────────────────────────────────────

def test_list_catalog(client, auth_headers):
    create_training(client, auth_headers)
    res = client.get("/api/trainings", headers=auth_headers)
    assert res.status_code == 200
    # La formation du provider n'apparaît pas dans son propre catalogue
    # (le frontend filtre sur provider_id ≠ user.company_id)
    assert isinstance(res.get_json(), list)


def test_list_mine(client, auth_headers):
    create_training(client, auth_headers, title="Ma formation 1")
    create_training(client, auth_headers, title="Ma formation 2")
    res = client.get("/api/trainings?mine=true", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_list_mine_kind_filter(client, auth_headers):
    create_training(client, auth_headers, kind="training", title="Formation")
    create_training(client, auth_headers, kind="room", title="Salle")
    trainings = client.get(
        "/api/trainings?mine=true&kind=training", headers=auth_headers
    ).get_json()
    rooms = client.get(
        "/api/trainings?mine=true&kind=room", headers=auth_headers
    ).get_json()
    assert len(trainings) == 1
    assert len(rooms) == 1


def test_list_search(client, auth_headers):
    create_training(client, auth_headers, title="Python avancé")
    create_training(client, auth_headers, title="Sécurité incendie")
    # mine=true pour voir ses propres formations
    res = client.get(
        "/api/trainings?mine=true&q=python", headers=auth_headers
    )
    results = res.get_json()
    assert len(results) == 1
    assert "Python" in results[0]["title"]


# ── Détail ────────────────────────────────────────────────────────────────────

def test_get_training_by_id(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.get(f"/api/trainings/{t['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["id"] == t["id"]


def test_get_unknown_training_returns_404(client, auth_headers):
    res = client.get("/api/trainings/9999", headers=auth_headers)
    assert res.status_code == 404


# ── Mise à jour ───────────────────────────────────────────────────────────────

def test_update_training_title(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.patch(
        f"/api/trainings/{t['id']}",
        headers=auth_headers,
        json={"title": "Nouveau titre"},
    )
    assert res.status_code == 200
    assert res.get_json()["title"] == "Nouveau titre"


def test_update_training_forbidden_for_other_user(client, auth_headers):
    t = create_training(client, auth_headers)
    other_headers = auth_headers_for(client, "other@x.com", company_name="Other Co")
    res = client.patch(
        f"/api/trainings/{t['id']}",
        headers=other_headers,
        json={"title": "Hack"},
    )
    assert res.status_code == 403


# ── Suppression ───────────────────────────────────────────────────────────────

def test_delete_training(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.delete(f"/api/trainings/{t['id']}", headers=auth_headers)
    assert res.status_code == 200
    # Vérifie que la formation n'existe plus
    assert client.get(f"/api/trainings/{t['id']}", headers=auth_headers).status_code == 404


def test_delete_training_forbidden_for_other_user(client, auth_headers):
    t = create_training(client, auth_headers)
    other_headers = auth_headers_for(client, "del@x.com", company_name="Del Co")
    res = client.delete(f"/api/trainings/{t['id']}", headers=other_headers)
    assert res.status_code == 403


# ── Rapports ──────────────────────────────────────────────────────────────────

def test_reports_empty(client, auth_headers):
    res = client.get("/api/trainings/reports", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json() == []


def test_reports_with_training(client, auth_headers):
    create_training(client, auth_headers)
    res = client.get("/api/trainings/reports", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["total_seats"] == 0  # Aucun inscrit confirmé


def test_reports_kind_filter(client, auth_headers):
    create_training(client, auth_headers, kind="training")
    create_training(client, auth_headers, kind="room", title="Salle")
    rooms = client.get(
        "/api/trainings/reports?kind=room", headers=auth_headers
    ).get_json()
    assert len(rooms) == 1
    assert rooms[0]["training_title"] == "Salle"
