"""Tests de l'API Training (/api/trainings/*)."""
from tests.conftest import auth_headers_for, create_training


# ── Création ──────────────────────────────────────────────────────────────────

def test_create_training_success(client, auth_headers):
    t = create_training(client, auth_headers)
    assert t["available_seats"] == 5
    assert t["booked_seats"] == 0
    assert t["status"] == "open"
    assert t["kind"] == "training"


def test_create_training_with_tags(client, auth_headers):
    t = create_training(client, auth_headers, tags=["IT", "management"])
    assert "IT" in t["tags"]
    assert "management" in t["tags"]


def test_create_training_with_location(client, auth_headers):
    t = create_training(client, auth_headers, location="Paris 75001")
    assert t["location"] == "Paris 75001"


def test_create_training_remote(client, auth_headers):
    t = create_training(client, auth_headers, is_remote=True)
    assert t["is_remote"] is True


def test_create_training_with_coords(client, auth_headers):
    t = create_training(client, auth_headers, latitude=48.8566, longitude=2.3522)
    assert t["latitude"] == 48.8566
    assert t["longitude"] == 2.3522


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


def test_create_training_ends_equal_starts_returns_422(client, auth_headers):
    res = client.post(
        "/api/trainings",
        headers=auth_headers,
        json={
            "title": "T",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T09:00:00",
            "shared_seats": 5,
        },
    )
    assert res.status_code == 422


def test_create_training_requires_siret(client):
    """Un compte sans SIRET ne peut pas publier."""
    headers = auth_headers_for(client, "nosiret@x.com",
                               company_name="No SIRET Corp")
    res = client.post(
        "/api/trainings",
        headers=headers,
        json={
            "title": "T",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
        },
    )
    assert res.status_code == 403


def test_create_training_requires_auth(client):
    res = client.post(
        "/api/trainings",
        json={
            "title": "T",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 5,
        },
    )
    assert res.status_code == 401


# ── Listing et catalogue ──────────────────────────────────────────────────────

def test_list_mine(client, auth_headers):
    create_training(client, auth_headers, title="Formation 1")
    create_training(client, auth_headers, title="Formation 2")
    res = client.get("/api/trainings?mine=true", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_catalog_includes_all_open_trainings(client):
    """Le catalogue retourne toutes les formations ouvertes (filtre provider côté frontend)."""
    prov = auth_headers_for(client, "prov_cat@x.com",
                            company_name="Prov", with_siret=True)
    other = auth_headers_for(client, "other_cat@x.com",
                             company_name="Other", with_siret=True)
    create_training(client, prov, title="Formation A")
    create_training(client, other, title="Formation B")

    catalog = client.get("/api/trainings", headers=prov).get_json()
    titles = [t["title"] for t in catalog]
    assert "Formation A" in titles
    assert "Formation B" in titles


def test_catalog_guest_access(client, auth_headers):
    """Le catalogue est accessible sans JWT (status=open uniquement)."""
    create_training(client, auth_headers)
    res = client.get("/api/trainings")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_list_mine_requires_auth(client):
    res = client.get("/api/trainings?mine=true")
    assert res.status_code == 200
    assert res.get_json() == []


# ── Filtres ───────────────────────────────────────────────────────────────────

def test_filter_by_search_query(client, auth_headers):
    create_training(client, auth_headers, title="Python avancé")
    create_training(client, auth_headers, title="Sécurité incendie")
    res = client.get("/api/trainings?mine=true&q=python", headers=auth_headers)
    results = res.get_json()
    assert len(results) == 1
    assert "Python" in results[0]["title"]


def test_filter_by_tag(client):
    prov = auth_headers_for(client, "tag_prov@x.com",
                            company_name="TagCorp", with_siret=True)
    other = auth_headers_for(client, "tag_other@x.com",
                             company_name="TagOther")
    create_training(client, prov, title="IT Training", tags=["IT"])
    create_training(client, prov, title="RH Training", tags=["RH"])

    res = client.get("/api/trainings?tag=IT", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "IT Training"


def test_filter_by_date_range(client):
    prov = auth_headers_for(client, "date_prov@x.com",
                            company_name="DateCorp", with_siret=True)
    other = auth_headers_for(client, "date_other@x.com",
                             company_name="DateOther")
    create_training(client, prov,
                    starts_at="2026-10-01T09:00:00",
                    ends_at="2026-10-01T17:00:00",
                    title="Octobre")
    create_training(client, prov,
                    starts_at="2026-12-01T09:00:00",
                    ends_at="2026-12-01T17:00:00",
                    title="Décembre")

    res = client.get(
        "/api/trainings?date_from=2026-10-01&date_to=2026-11-30",
        headers=other,
    )
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Octobre"


def test_filter_by_price_max(client):
    prov = auth_headers_for(client, "price_prov@x.com",
                            company_name="PriceCorp", with_siret=True)
    other = auth_headers_for(client, "price_other@x.com",
                             company_name="PriceOther")
    create_training(client, prov, price_per_seat=50.0, title="Pas cher")
    create_training(client, prov, price_per_seat=500.0, title="Cher")

    res = client.get("/api/trainings?price_max=100", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Pas cher"


def test_filter_by_seats_min(client):
    prov = auth_headers_for(client, "seats_prov@x.com",
                            company_name="SeatsCorp", with_siret=True)
    other = auth_headers_for(client, "seats_other@x.com",
                             company_name="SeatsOther")
    create_training(client, prov, shared_seats=2, title="Petite session")
    create_training(client, prov, shared_seats=20, title="Grande session")

    res = client.get("/api/trainings?seats_min=10", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Grande session"


def test_filter_remote_only(client):
    prov = auth_headers_for(client, "rem_prov@x.com",
                            company_name="RemCorp", with_siret=True)
    other = auth_headers_for(client, "rem_other@x.com",
                             company_name="RemOther")
    create_training(client, prov, is_remote=True, title="Distanciel")
    create_training(client, prov, is_remote=False,
                    location="Lyon", title="Présentiel")

    res = client.get("/api/trainings?remote_only=true", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Distanciel"


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


def test_update_training_tags(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.patch(
        f"/api/trainings/{t['id']}",
        headers=auth_headers,
        json={"tags": ["IT", "sécurité"]},
    )
    assert res.status_code == 200
    assert "IT" in res.get_json()["tags"]


def test_update_training_status_to_closed(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.patch(
        f"/api/trainings/{t['id']}",
        headers=auth_headers,
        json={"status": "closed"},
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "closed"


def test_update_training_forbidden_for_other_user(client, auth_headers):
    t = create_training(client, auth_headers)
    other = auth_headers_for(client, "other@x.com", company_name="Other Co")
    res = client.patch(
        f"/api/trainings/{t['id']}",
        headers=other,
        json={"title": "Hack"},
    )
    assert res.status_code == 403


def test_update_training_requires_auth(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.patch(
        f"/api/trainings/{t['id']}", json={"title": "T"}
    )
    assert res.status_code == 401


# ── Suppression ───────────────────────────────────────────────────────────────

def test_delete_training(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.delete(f"/api/trainings/{t['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert (
        client.get(f"/api/trainings/{t['id']}", headers=auth_headers).status_code
        == 404
    )


def test_delete_training_forbidden_for_other_user(client, auth_headers):
    t = create_training(client, auth_headers)
    other = auth_headers_for(client, "del@x.com", company_name="Del Co")
    res = client.delete(f"/api/trainings/{t['id']}", headers=other)
    assert res.status_code == 403


def test_delete_training_requires_auth(client, auth_headers):
    t = create_training(client, auth_headers)
    res = client.delete(f"/api/trainings/{t['id']}")
    assert res.status_code == 401


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
    assert data[0]["total_seats"] == 0


def test_reports_with_confirmed_booking(client):
    prov = auth_headers_for(client, "rep_prov@x.com",
                            company_name="RepCorp", with_siret=True)
    book = auth_headers_for(client, "rep_book@x.com",
                            company_name="RepBooker")
    t = create_training(client, prov, shared_seats=10)

    b = client.post(
        "/api/bookings", headers=book,
        json={"training_id": t["id"], "seats": 3}
    ).get_json()
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )

    reports = client.get("/api/trainings/reports", headers=prov).get_json()
    assert reports[0]["total_seats"] == 3
    assert len(reports[0]["attendees"]) == 1
    assert reports[0]["attendees"][0]["seats"] == 3


def test_reports_requires_auth(client):
    res = client.get("/api/trainings/reports")
    assert res.status_code == 401
