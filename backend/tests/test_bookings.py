"""Tests de l'API Booking (/api/bookings/*)."""
from tests.conftest import (
    auth_headers_for,
    create_training,
    create_booking,
    register_and_login,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup(client):
    """
    Crée un provider avec une formation (5 places) et un booker distinct.
    Retourne (provider_headers, booker_headers, training_id).
    """
    prov = auth_headers_for(client, "prov@x.com", company_name="Prov")
    book = auth_headers_for(client, "book@x.com", company_name="Book")
    training = create_training(client, prov, shared_seats=5)
    return prov, book, training["id"]


# ── Création de réservation ───────────────────────────────────────────────────

def test_create_booking_success(client):
    _, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=2)
    assert b["status"] == "pending"
    assert b["seats"] == 2


def test_create_booking_requires_auth(client):
    _, _, tid = _setup(client)
    res = client.post(
        "/api/bookings", json={"training_id": tid, "seats": 1}
    )
    assert res.status_code == 401


def test_cannot_book_own_training(client):
    prov, _, tid = _setup(client)
    res = client.post(
        "/api/bookings",
        headers=prov,
        json={"training_id": tid, "seats": 1},
    )
    assert res.status_code == 400
    assert "propre" in res.get_json()["message"]


def test_cannot_book_more_seats_than_available(client):
    _, book, tid = _setup(client)
    res = client.post(
        "/api/bookings",
        headers=book,
        json={"training_id": tid, "seats": 99},
    )
    assert res.status_code == 400


def test_cannot_book_closed_training(client):
    prov = auth_headers_for(client, "p2@x.com", company_name="P2")
    book = auth_headers_for(client, "b2@x.com", company_name="B2")
    t = create_training(client, prov, shared_seats=5, status="closed")
    # status n'est pas filtré à la création — on force via PATCH
    client.patch(
        f"/api/trainings/{t['id']}",
        headers=prov,
        json={"status": "closed"},
    )
    res = client.post(
        "/api/bookings",
        headers=book,
        json={"training_id": t["id"], "seats": 1},
    )
    assert res.status_code == 400


def test_booking_404_unknown_training(client):
    book = auth_headers_for(client, "bx@x.com", company_name="BX")
    res = client.post(
        "/api/bookings",
        headers=book,
        json={"training_id": 9999, "seats": 1},
    )
    assert res.status_code == 404


# ── Liste des réservations ────────────────────────────────────────────────────

def test_list_my_bookings(client):
    prov, book, tid = _setup(client)
    create_booking(client, book, tid, seats=1)
    res = client.get("/api/bookings", headers=book)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_list_incoming_bookings(client):
    prov, book, tid = _setup(client)
    create_booking(client, book, tid, seats=2)
    res = client.get("/api/bookings/incoming", headers=prov)
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_list_bookings_kind_isolation(client):
    """Les bookings training et room sont isolés par kind."""
    prov_tr = auth_headers_for(client, "ptraining@x.com", company_name="PTraining")
    prov_rm = auth_headers_for(client, "proom@x.com", company_name="PRoom")
    book = auth_headers_for(client, "bkr@x.com", company_name="Booker")

    t = create_training(client, prov_tr, kind="training")
    r = create_training(client, prov_rm, kind="room", title="Salle")

    create_booking(client, book, t["id"], seats=1)
    create_booking(client, book, r["id"], seats=1)

    trainings_res = client.get("/api/bookings?kind=training", headers=book).get_json()
    rooms_res = client.get("/api/bookings?kind=room", headers=book).get_json()

    assert len(trainings_res) == 1
    assert len(rooms_res) == 1


# ── Confirmation / refus par le provider ─────────────────────────────────────

def test_provider_confirms_booking(client):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=2)

    res = client.patch(
        f"/api/bookings/{b['id']}",
        headers=prov,
        json={"status": "confirmed"},
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "confirmed"


def test_provider_cancels_booking(client):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=2)

    res = client.patch(
        f"/api/bookings/{b['id']}",
        headers=prov,
        json={"status": "cancelled"},
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "cancelled"


def test_booker_cannot_confirm_booking(client):
    """Seul le provider peut changer le statut."""
    prov, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=1)

    res = client.patch(
        f"/api/bookings/{b['id']}",
        headers=book,  # booker tente de confirmer
        json={"status": "confirmed"},
    )
    assert res.status_code == 403


def test_confirm_overbooking_blocked(client):
    """Impossible de confirmer si les places sont déjà prises."""
    prov = auth_headers_for(client, "pov@x.com", company_name="Pov")
    b1 = auth_headers_for(client, "bk1@x.com", company_name="Bk1")
    b2 = auth_headers_for(client, "bk2@x.com", company_name="Bk2")

    t = create_training(client, prov, shared_seats=3)

    bk1 = create_booking(client, b1, t["id"], seats=3)
    bk2 = create_booking(client, b2, t["id"], seats=2)

    # Confirme la première (prend les 3 places)
    client.patch(
        f"/api/bookings/{bk1['id']}", headers=prov, json={"status": "confirmed"}
    )

    # La seconde ne peut plus être confirmée : 0 place restante
    res = client.patch(
        f"/api/bookings/{bk2['id']}", headers=prov, json={"status": "confirmed"}
    )
    assert res.status_code == 400


# ── Annulation par le booker ──────────────────────────────────────────────────

def test_booker_cancels_pending_booking(client):
    _, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=1)

    res = client.delete(f"/api/bookings/{b['id']}", headers=book)
    assert res.status_code == 200


def test_booker_cannot_cancel_confirmed_booking(client):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=1)
    # Provider confirme
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    # Booker tente d'annuler
    res = client.delete(f"/api/bookings/{b['id']}", headers=book)
    assert res.status_code == 400


def test_other_company_cannot_cancel_booking(client):
    _, book, tid = _setup(client)
    b = create_booking(client, book, tid, seats=1)
    intruder = auth_headers_for(client, "i@x.com", company_name="Intruder")

    res = client.delete(f"/api/bookings/{b['id']}", headers=intruder)
    assert res.status_code == 403


# ── available_seats cohérence ─────────────────────────────────────────────────

def test_available_seats_decreases_after_confirmation(client):
    prov, book, tid = _setup(client)
    t_before = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t_before["available_seats"] == 5

    b = create_booking(client, book, tid, seats=2)
    # pending ne diminue pas les places disponibles
    t_after_pending = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t_after_pending["available_seats"] == 5

    # Après confirmation, les places sont comptabilisées
    client.patch(
        f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"}
    )
    t_after_confirm = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t_after_confirm["available_seats"] == 3
    assert t_after_confirm["booked_seats"] == 2
