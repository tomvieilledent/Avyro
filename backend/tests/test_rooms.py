"""Tests de l'API Room (/api/rooms/*)."""
from tests.conftest import auth_headers_for, create_room


# ── Création ──────────────────────────────────────────────────────────────────

def test_create_room_success(client, auth_headers):
    r = create_room(client, auth_headers)
    assert r["available_seats"] == 4
    assert r["booked_seats"] == 0
    assert r["status"] == "open"
    assert r["kind"] == "room"


def test_create_room_with_tags(client, auth_headers):
    r = create_room(client, auth_headers, tags=["réunion", "formation"])
    assert "réunion" in r["tags"]


def test_create_room_with_location(client, auth_headers):
    r = create_room(client, auth_headers, location="Paris 8e")
    assert r["location"] == "Paris 8e"


def test_create_room_remote(client, auth_headers):
    r = create_room(client, auth_headers, is_remote=True)
    assert r["is_remote"] is True


def test_create_room_with_coords(client, auth_headers):
    r = create_room(client, auth_headers, latitude=45.7640, longitude=4.8357)
    assert r["latitude"] == 45.7640
    assert r["longitude"] == 4.8357


def test_create_room_missing_title_returns_422(client, auth_headers):
    res = client.post(
        "/api/rooms",
        headers=auth_headers,
        json={
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 4,
        },
    )
    assert res.status_code == 422


def test_create_room_ends_before_starts_returns_422(client, auth_headers):
    res = client.post(
        "/api/rooms",
        headers=auth_headers,
        json={
            "title": "Salle",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T17:00:00",
            "ends_at": "2026-09-01T09:00:00",
            "shared_seats": 4,
        },
    )
    assert res.status_code == 422


def test_create_room_requires_siret(client):
    headers = auth_headers_for(client, "nosiret_room@x.com",
                               company_name="NoSiretRoom")
    res = client.post(
        "/api/rooms",
        headers=headers,
        json={
            "title": "Salle",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 4,
        },
    )
    assert res.status_code == 403


def test_create_room_requires_auth(client):
    res = client.post(
        "/api/rooms",
        json={
            "title": "Salle",
            "contact_phone": "0600000000",
            "starts_at": "2026-09-01T09:00:00",
            "ends_at": "2026-09-01T17:00:00",
            "shared_seats": 4,
        },
    )
    assert res.status_code == 401


# ── Listing et catalogue ──────────────────────────────────────────────────────

def test_list_mine_rooms(client, auth_headers):
    create_room(client, auth_headers, title="Salle A")
    create_room(client, auth_headers, title="Salle B")
    res = client.get("/api/rooms?mine=true", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_catalog_includes_all_open_rooms(client):
    """Le catalogue retourne toutes les salles ouvertes (filtre provider côté frontend)."""
    prov = auth_headers_for(client, "room_prov@x.com",
                            company_name="RoomProv", with_siret=True)
    other = auth_headers_for(client, "room_other@x.com",
                             company_name="RoomOther", with_siret=True)
    create_room(client, prov, title="Salle A")
    create_room(client, other, title="Salle B")

    catalog = client.get("/api/rooms", headers=prov).get_json()
    titles = [r["title"] for r in catalog]
    assert "Salle A" in titles
    assert "Salle B" in titles


def test_catalog_room_guest_access(client, auth_headers):
    create_room(client, auth_headers)
    res = client.get("/api/rooms")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


# ── Filtres ───────────────────────────────────────────────────────────────────

def test_filter_room_by_search_query(client, auth_headers):
    create_room(client, auth_headers, title="Salle Lumière")
    create_room(client, auth_headers, title="Salle Obscure")
    res = client.get("/api/rooms?mine=true&q=lumière", headers=auth_headers)
    results = res.get_json()
    assert len(results) == 1
    assert "Lumière" in results[0]["title"]


def test_filter_room_by_tag(client):
    prov = auth_headers_for(client, "rtag_prov@x.com",
                            company_name="RTagCorp", with_siret=True)
    other = auth_headers_for(client, "rtag_other@x.com",
                             company_name="RTagOther")
    create_room(client, prov, title="Grande salle", tags=["réunion"])
    create_room(client, prov, title="Petite salle", tags=["formation"])

    res = client.get("/api/rooms?tag=réunion", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Grande salle"


def test_filter_room_by_date_range(client):
    prov = auth_headers_for(client, "rdate_prov@x.com",
                            company_name="RDateCorp", with_siret=True)
    other = auth_headers_for(client, "rdate_other@x.com",
                             company_name="RDateOther")
    create_room(client, prov,
                starts_at="2026-10-01T09:00:00",
                ends_at="2026-10-01T17:00:00",
                title="Octobre")
    create_room(client, prov,
                starts_at="2026-12-01T09:00:00",
                ends_at="2026-12-01T17:00:00",
                title="Décembre")

    res = client.get(
        "/api/rooms?date_from=2026-10-01&date_to=2026-11-30",
        headers=other,
    )
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Octobre"


def test_filter_room_by_price_max(client):
    prov = auth_headers_for(client, "rprice_prov@x.com",
                            company_name="RPriceCorp", with_siret=True)
    other = auth_headers_for(client, "rprice_other@x.com",
                             company_name="RPriceOther")
    create_room(client, prov, price_per_seat=30.0, title="Pas cher")
    create_room(client, prov, price_per_seat=300.0, title="Cher")

    res = client.get("/api/rooms?price_max=100", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Pas cher"


def test_filter_room_by_seats_min(client):
    prov = auth_headers_for(client, "rseats_prov@x.com",
                            company_name="RSeatsCorp", with_siret=True)
    other = auth_headers_for(client, "rseats_other@x.com",
                             company_name="RSeatsOther")
    create_room(client, prov, shared_seats=2, title="Petite")
    create_room(client, prov, shared_seats=20, title="Grande")

    res = client.get("/api/rooms?seats_min=10", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Grande"


def test_filter_room_remote_only(client):
    prov = auth_headers_for(client, "rrem_prov@x.com",
                            company_name="RRemCorp", with_siret=True)
    other = auth_headers_for(client, "rrem_other@x.com",
                             company_name="RRemOther")
    create_room(client, prov, is_remote=True, title="Remote")
    create_room(client, prov, is_remote=False,
                location="Lyon", title="Présentiel")

    res = client.get("/api/rooms?remote_only=true", headers=other)
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Remote"


# ── Détail ────────────────────────────────────────────────────────────────────

def test_get_room_by_id(client, auth_headers):
    r = create_room(client, auth_headers)
    res = client.get(f"/api/rooms/{r['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["id"] == r["id"]


def test_get_unknown_room_returns_404(client, auth_headers):
    res = client.get("/api/rooms/9999", headers=auth_headers)
    assert res.status_code == 404


# ── Mise à jour ───────────────────────────────────────────────────────────────

def test_update_room_title(client, auth_headers):
    r = create_room(client, auth_headers)
    res = client.patch(
        f"/api/rooms/{r['id']}",
        headers=auth_headers,
        json={"title": "Nouvelle salle"},
    )
    assert res.status_code == 200
    assert res.get_json()["title"] == "Nouvelle salle"


def test_update_room_tags(client, auth_headers):
    r = create_room(client, auth_headers)
    res = client.patch(
        f"/api/rooms/{r['id']}",
        headers=auth_headers,
        json={"tags": ["réunion", "coworking"]},
    )
    assert res.status_code == 200
    assert "réunion" in res.get_json()["tags"]


def test_update_room_status(client, auth_headers):
    r = create_room(client, auth_headers)
    res = client.patch(
        f"/api/rooms/{r['id']}",
        headers=auth_headers,
        json={"status": "closed"},
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "closed"


def test_update_room_forbidden_for_other(client, auth_headers):
    r = create_room(client, auth_headers)
    other = auth_headers_for(client, "rother@x.com", company_name="OtherCo")
    res = client.patch(
        f"/api/rooms/{r['id']}", headers=other, json={"title": "Hack"}
    )
    assert res.status_code == 403


# ── Suppression ───────────────────────────────────────────────────────────────

def test_delete_room(client, auth_headers):
    r = create_room(client, auth_headers)
    res = client.delete(f"/api/rooms/{r['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert (
        client.get(f"/api/rooms/{r['id']}", headers=auth_headers).status_code == 404
    )


def test_delete_room_forbidden_for_other(client, auth_headers):
    r = create_room(client, auth_headers)
    other = auth_headers_for(client, "rdel@x.com", company_name="DelCo")
    res = client.delete(f"/api/rooms/{r['id']}", headers=other)
    assert res.status_code == 403


# ── Rapports ──────────────────────────────────────────────────────────────────

def test_room_reports_empty(client, auth_headers):
    res = client.get("/api/rooms/reports", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json() == []


def test_room_reports_with_room(client, auth_headers):
    create_room(client, auth_headers)
    res = client.get("/api/rooms/reports", headers=auth_headers)
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["total_seats"] == 0


def test_room_reports_with_confirmed_booking(client):
    prov = auth_headers_for(client, "rrep_prov@x.com",
                            company_name="RRepCorp", with_siret=True)
    book = auth_headers_for(client, "rrep_book@x.com",
                            company_name="RRepBooker")
    r = create_room(client, prov, shared_seats=10)

    b = client.post(
        "/api/bookings", headers=book,
        json={"room_id": r["id"], "seats": 2}
    ).get_json()
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )

    reports = client.get("/api/rooms/reports", headers=prov).get_json()
    assert reports[0]["total_seats"] == 2
    assert reports[0]["attendees"][0]["seats"] == 2


def test_room_reports_requires_auth(client):
    res = client.get("/api/rooms/reports")
    assert res.status_code == 401
