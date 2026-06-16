"""Tests de l'API Booking (/api/bookings/*)."""
from tests.conftest import auth_headers_for, create_training, create_room, create_booking


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup_training(client, shared_seats=5):
    """Provider avec une formation, booker distinct."""
    prov = auth_headers_for(client, "prov@x.com",
                            company_name="Prov", with_siret=True)
    book = auth_headers_for(client, "book@x.com", company_name="Book")
    t = create_training(client, prov, shared_seats=shared_seats)
    return prov, book, t["id"]


def _setup_room(client, shared_seats=4):
    """Provider avec une salle, booker distinct."""
    prov = auth_headers_for(client, "room_prov@x.com",
                            company_name="RoomProv", with_siret=True)
    book = auth_headers_for(client, "room_book@x.com", company_name="RoomBook")
    r = create_room(client, prov, shared_seats=shared_seats)
    return prov, book, r["id"]


# ── Création de réservation sur une formation ─────────────────────────────────

def test_create_booking_success(client):
    _, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    assert b["status"] == "pending"
    assert b["seats"] == 2


def test_create_booking_requires_auth(client):
    _, _, tid = _setup_training(client)
    res = client.post(
        "/api/bookings",
        json={"training_id": tid, "seats": 1},
    )
    assert res.status_code == 401


def test_cannot_book_own_training(client):
    prov, _, tid = _setup_training(client)
    res = client.post(
        "/api/bookings", headers=prov,
        json={"training_id": tid, "seats": 1},
    )
    assert res.status_code == 400
    assert "propre" in res.get_json()["message"]


def test_cannot_book_more_seats_than_available(client):
    _, book, tid = _setup_training(client, shared_seats=5)
    res = client.post(
        "/api/bookings", headers=book,
        json={"training_id": tid, "seats": 99},
    )
    assert res.status_code == 400


def test_cannot_book_closed_training(client):
    prov = auth_headers_for(client, "p2@x.com",
                            company_name="P2", with_siret=True)
    book = auth_headers_for(client, "b2@x.com", company_name="B2")
    t = create_training(client, prov)
    client.patch(
        f"/api/trainings/{t['id']}", headers=prov, json={"status": "closed"}
    )
    res = client.post(
        "/api/bookings", headers=book,
        json={"training_id": t["id"], "seats": 1},
    )
    assert res.status_code == 400


def test_booking_404_unknown_training(client):
    book = auth_headers_for(client, "bx@x.com", company_name="BX")
    res = client.post(
        "/api/bookings", headers=book,
        json={"training_id": 9999, "seats": 1},
    )
    assert res.status_code == 404


def test_booking_with_note(client):
    _, book, tid = _setup_training(client)
    res = client.post(
        "/api/bookings", headers=book,
        json={"training_id": tid, "seats": 1, "note": "Merci de confirmer avant vendredi."},
    )
    assert res.status_code == 201
    assert res.get_json()["note"] == "Merci de confirmer avant vendredi."


# ── Réservation sur une salle ─────────────────────────────────────────────────

def test_create_room_booking_success(client):
    _, book, rid = _setup_room(client)
    b = create_booking(client, book, room_id=rid, seats=1)
    assert b["status"] == "pending"
    assert b["seats"] == 1


def test_cannot_book_own_room(client):
    prov, _, rid = _setup_room(client)
    res = client.post(
        "/api/bookings", headers=prov,
        json={"room_id": rid, "seats": 1},
    )
    assert res.status_code == 400


def test_booking_404_unknown_room(client):
    book = auth_headers_for(client, "broom@x.com", company_name="BRoom")
    res = client.post(
        "/api/bookings", headers=book,
        json={"room_id": 9999, "seats": 1},
    )
    assert res.status_code == 404


# ── Liste des réservations ────────────────────────────────────────────────────

def test_list_my_bookings(client):
    _, book, tid = _setup_training(client)
    create_booking(client, book, training_id=tid, seats=1)
    res = client.get("/api/bookings", headers=book)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_list_incoming_bookings(client):
    prov, book, tid = _setup_training(client)
    create_booking(client, book, training_id=tid, seats=2)
    res = client.get("/api/bookings/incoming", headers=prov)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_list_bookings_kind_training(client):
    prov = auth_headers_for(client, "kprov@x.com",
                            company_name="KProv", with_siret=True)
    book = auth_headers_for(client, "kbook@x.com", company_name="KBook")
    t = create_training(client, prov)
    r = create_room(client, prov, title="Salle K")
    create_booking(client, book, training_id=t["id"], seats=1)
    create_booking(client, book, room_id=r["id"], seats=1)

    tr = client.get("/api/bookings?kind=training", headers=book).get_json()
    rm = client.get("/api/bookings?kind=room", headers=book).get_json()
    assert len(tr) == 1
    assert len(rm) == 1


def test_incoming_room_kind_filter(client):
    prov, book, rid = _setup_room(client)
    create_booking(client, book, room_id=rid, seats=1)
    res = client.get("/api/bookings/incoming?kind=room", headers=prov)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


# ── Compteurs de réservations en attente ──────────────────────────────────────

def test_booking_counts_empty(client, provider_headers):
    res = client.get("/api/bookings/counts", headers=provider_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["pending_incoming_training"] == 0
    assert data["pending_incoming_room"] == 0


def test_booking_counts_with_pending_training(client):
    prov = auth_headers_for(client, "cnt_prov@x.com",
                            company_name="CntCorp", with_siret=True)
    book = auth_headers_for(client, "cnt_book@x.com", company_name="CntBook")
    t = create_training(client, prov)
    create_booking(client, book, training_id=t["id"], seats=1)

    res = client.get("/api/bookings/counts", headers=prov)
    assert res.get_json()["pending_incoming_training"] == 1


def test_booking_counts_with_pending_room(client):
    prov = auth_headers_for(client, "cntroom_prov@x.com",
                            company_name="CntRoomCorp", with_siret=True)
    book = auth_headers_for(client, "cntroom_book@x.com",
                            company_name="CntRoomBook")
    r = create_room(client, prov)
    create_booking(client, book, room_id=r["id"], seats=1)

    res = client.get("/api/bookings/counts", headers=prov)
    assert res.get_json()["pending_incoming_room"] == 1


def test_booking_counts_decreases_after_confirmation(client):
    prov = auth_headers_for(client, "cntdec_prov@x.com",
                            company_name="CntDecCorp", with_siret=True)
    book = auth_headers_for(client, "cntdec_book@x.com",
                            company_name="CntDecBook")
    t = create_training(client, prov)
    b = create_booking(client, book, training_id=t["id"], seats=1)

    assert client.get("/api/bookings/counts",
                      headers=prov).get_json()["pending_incoming_training"] == 1

    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    assert client.get("/api/bookings/counts",
                      headers=prov).get_json()["pending_incoming_training"] == 0


# ── Confirmation / refus par le provider ─────────────────────────────────────

def test_provider_confirms_booking(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    res = client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "confirmed"


def test_provider_cancels_booking(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    res = client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "cancelled"}
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "cancelled"


def test_booker_cannot_confirm_booking(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    res = client.patch(
        f"/api/bookings/{b['id']}", headers=book, json={"status": "confirmed"}
    )
    assert res.status_code == 403


def test_confirm_overbooking_blocked(client):
    prov = auth_headers_for(client, "pov@x.com",
                            company_name="Pov", with_siret=True)
    b1 = auth_headers_for(client, "bk1@x.com", company_name="Bk1")
    b2 = auth_headers_for(client, "bk2@x.com", company_name="Bk2")
    t = create_training(client, prov, shared_seats=3)

    bk1 = create_booking(client, b1, training_id=t["id"], seats=3)
    bk2 = create_booking(client, b2, training_id=t["id"], seats=2)

    client.patch(
        f"/api/bookings/{bk1['id']}", headers=prov, json={"status": "confirmed"}
    )
    res = client.patch(
        f"/api/bookings/{bk2['id']}", headers=prov, json={"status": "confirmed"}
    )
    assert res.status_code == 400


def test_confirm_room_booking(client):
    prov, book, rid = _setup_room(client)
    b = create_booking(client, book, room_id=rid, seats=2)
    res = client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "confirmed"


# ── Annulation par le booker ──────────────────────────────────────────────────

def test_booker_cancels_pending_booking(client):
    _, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    res = client.delete(f"/api/bookings/{b['id']}", headers=book)
    assert res.status_code == 200


def test_booker_cannot_cancel_confirmed_booking(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    res = client.delete(f"/api/bookings/{b['id']}", headers=book)
    assert res.status_code == 400


def test_other_company_cannot_cancel_booking(client):
    _, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    intruder = auth_headers_for(client, "i@x.com", company_name="Intruder")
    res = client.delete(f"/api/bookings/{b['id']}", headers=intruder)
    assert res.status_code == 403


# ── Cohérence des places disponibles ─────────────────────────────────────────

def test_available_seats_unchanged_while_pending(client):
    prov, book, tid = _setup_training(client)
    create_booking(client, book, training_id=tid, seats=2)
    t = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t["available_seats"] == 5  # pending ne bloque pas


def test_available_seats_decreases_after_confirmation(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    t = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t["available_seats"] == 3
    assert t["booked_seats"] == 2


def test_available_seats_restored_after_cancel(client):
    prov, book, tid = _setup_training(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "cancelled"}
    )
    t = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t["available_seats"] == 5
