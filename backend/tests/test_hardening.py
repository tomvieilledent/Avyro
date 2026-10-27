"""Tests durcissement : invitations, bookings, comptes, config prod, geocode."""
import io
import json
from datetime import timedelta
from urllib.error import URLError

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import ConfigError, ProductionConfig, validate_production_config
from app.extensions import db
from app.models import Booking, User
from app.utils.tokens import create_invite_token
from tests.conftest import (
    auth_headers_for, create_booking, create_room, create_training,
    future_dt, register_and_login,
)

GOOD = "x" * 40
ACCEPT = {"first_name": "N", "last_name": "M", "phone": "0600000000",
          "password": "password123"}


def _setup(client, seats=5):
    prov = auth_headers_for(client, "prov@x.com", company_name="Prov", with_siret=True)
    book = auth_headers_for(client, "book@x.com", company_name="Book")
    return prov, book, create_training(client, prov, shared_seats=seats)["id"]


# ── Invitations ──────────────────────────────────────────────────────────────

def test_invite_token_as_bearer_is_rejected_not_500(client, app):
    data = register_and_login(client, "adm@x.com", company_name="C")
    with app.app_context():
        token = create_invite_token("n@x.com", "member", data["user"]["company_id"])
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (401, 422)


def test_access_token_with_non_numeric_identity_is_401(client):
    tok = create_access_token(identity="invite:foo@x.com")
    for url in ("/api/auth/me", "/api/bookings"):
        res = client.get(url, headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 401
    # Route à JWT optionnel : pas de 500 non plus
    res = client.get("/api/trainings?mine=true",
                     headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 200 and res.get_json() == []


def test_accept_invite_rejects_jwt_and_tampered_tokens(client, app):
    data = register_and_login(client, "adm@x.com", company_name="C")
    jwt_tok = create_access_token(
        identity="invite:n@x.com",
        additional_claims={"invite": True, "invite_email": "n@x.com",
                           "company_id": data["user"]["company_id"]},
    )
    with app.app_context():
        good = create_invite_token("n@x.com", "member", data["user"]["company_id"])
    for tok in (jwt_tok, good[:-2] + "xx"):
        res = client.post("/api/auth/accept-invite", json={"token": tok, **ACCEPT})
        assert res.status_code == 400


def test_accept_invite_expired(client, app):
    data = register_and_login(client, "adm@x.com", company_name="C")
    with app.app_context():
        tok = create_invite_token("n@x.com", "member", data["user"]["company_id"])
        app.config["INVITE_MAX_AGE"] = -1
    res = client.post("/api/auth/accept-invite", json={"token": tok, **ACCEPT})
    assert res.status_code == 400


def test_accept_invite_single_use_and_role(client, app):
    data = register_and_login(client, "adm@x.com", company_name="C")
    with app.app_context():
        tok = create_invite_token("New@X.com", "admin", data["user"]["company_id"])
    res = client.post("/api/auth/accept-invite", json={"token": tok, **ACCEPT})
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "new@x.com"
    assert res.get_json()["user"]["role"] == "admin"
    again = client.post("/api/auth/accept-invite", json={"token": tok, **ACCEPT})
    assert again.status_code == 409


def test_invite_url_uses_public_url(client, app, monkeypatch):
    app.config["PUBLIC_URL"] = "https://app.avyro.test/"
    sent = []
    monkeypatch.setattr("app.api.companies.send_email",
                        lambda **kw: sent.append(kw))
    h = auth_headers_for(client, "adm@x.com", company_name="C")
    res = client.post("/api/companies/me/invite", headers=h,
                      json={"email": "Guest@X.com"})
    assert res.status_code == 200
    assert sent[0]["to"] == "guest@x.com"
    assert "https://app.avyro.test/invite?token=" in sent[0]["body"]
    assert "localhost" not in sent[0]["body"]


# ── Comptes : email, limites, conflits ───────────────────────────────────────

def _reg(client, email, **kw):
    return client.post("/api/auth/register", json={
        "email": email, "password": "password123", "first_name": "A",
        "last_name": "B", "phone": "0600000000", **kw})


def test_email_case_insensitive_register_login(client):
    res = _reg(client, "  Alice@Example.COM ")
    assert res.status_code == 201
    assert res.get_json()["user"]["email"] == "alice@example.com"
    assert _reg(client, "ALICE@example.com").status_code == 409
    login = client.post("/api/auth/login",
                        json={"email": "ALICE@Example.com", "password": "password123"})
    assert login.status_code == 200


def test_patch_me_email_case_conflict(client):
    _reg(client, "a@x.com")
    h = auth_headers_for(client, "b@x.com")
    res = client.patch("/api/auth/me", headers=h, json={"email": "A@X.com"})
    assert res.status_code == 409


def test_integrity_error_race_returns_409(client, monkeypatch):
    _reg(client, "a@x.com")
    monkeypatch.setattr("app.api.auth._email_taken", lambda *a, **k: False)
    assert _reg(client, "a@x.com").status_code == 409
    h = auth_headers_for(client, "b@x.com")
    assert client.patch("/api/auth/me", headers=h,
                        json={"email": "a@x.com"}).status_code == 409
    assert client.get("/api/auth/me", headers=h).status_code == 200  # session saine


def test_company_name_stripped_and_limits(client):
    res = _reg(client, "a@x.com", company_name="  Acme  ")
    assert res.status_code == 201
    h = {"Authorization": f"Bearer {res.get_json()['access_token']}"}
    comp = client.get("/api/companies/me", headers=h).get_json()
    assert comp["name"] == "Acme" and comp["kind"] == "pro"
    assert _reg(client, "b@x.com", company_name="   ").status_code == 201
    assert _reg(client, "c@x.com", company_name="x" * 256).status_code == 422
    assert _reg(client, "d@x.com", tags=["t"] * 21).status_code == 422
    assert _reg(client, "e@x.com", tags=["t" * 51]).status_code == 422
    r = client.post("/api/auth/register", json={
        "email": "f@x.com", "password": "p" * 129, "first_name": "A",
        "last_name": "B", "phone": "0600000000"})
    assert r.status_code == 422


def test_refresh_requires_existing_user(client):
    data = register_and_login(client, "gone@x.com")
    ref = {"Authorization": f"Bearer {data['refresh_token']}"}
    assert client.post("/api/auth/refresh", headers=ref).status_code == 200
    h = {"Authorization": f"Bearer {data['access_token']}"}
    assert client.delete("/api/auth/me", headers=h).status_code == 200
    assert client.post("/api/auth/refresh", headers=ref).status_code == 401


def test_delete_member_with_bookings_anonymizes(client, app):
    prov, book, tid = _setup(client)
    # Second membre de la company "Book" qui réserve
    adm = client.get("/api/auth/me", headers=book).get_json()
    with app.app_context():
        tok = create_invite_token("m@x.com", "member", adm["company_id"])
    m = client.post("/api/auth/accept-invite", json={"token": tok, **ACCEPT}).get_json()
    mh = {"Authorization": f"Bearer {m['access_token']}"}
    b = create_booking(client, mh, training_id=tid, seats=1)
    client.patch(f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"})

    assert client.delete("/api/auth/me", headers=mh).status_code == 200
    with app.app_context():
        bk = db.session.get(Booking, b["id"])
        assert bk is not None and bk.requested_by_id is None
    inc = client.get("/api/bookings/incoming", headers=prov)
    assert inc.status_code == 200
    assert inc.get_json()[0]["requested_by_id"] is None
    rep = client.get("/api/trainings/reports", headers=prov)
    assert rep.status_code == 200
    assert rep.get_json()[0]["attendees"][0]["contact_email"] is None


def test_delete_last_admin_with_bookings(client, app):
    prov, book, tid = _setup(client)
    create_booking(client, book, training_id=tid, seats=1)
    assert client.delete("/api/auth/me", headers=book).status_code == 200
    with app.app_context():
        assert Booking.query.count() == 0
        assert User.query.filter_by(email="book@x.com").first() is None


# ── Bookings ─────────────────────────────────────────────────────────────────

def test_transitions_only_from_pending(client):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, training_id=tid, seats=2)
    url = f"/api/bookings/{b['id']}"
    assert client.patch(url, headers=prov, json={"status": "confirmed"}).status_code == 200
    for st in ("cancelled", "confirmed"):
        assert client.patch(url, headers=prov, json={"status": st}).status_code == 400
    t = client.get(f"/api/trainings/{tid}", headers=prov).get_json()
    assert t["available_seats"] == 3

    other = auth_headers_for(client, "other@x.com", company_name="Other")
    b2 = create_booking(client, other, training_id=tid, seats=1)
    url2 = f"/api/bookings/{b2['id']}"
    assert client.patch(url2, headers=prov, json={"status": "cancelled"}).status_code == 200
    assert client.patch(url2, headers=prov, json={"status": "confirmed"}).status_code == 400


def test_cannot_book_past_offer(client):
    prov = auth_headers_for(client, "prov@x.com", company_name="P", with_siret=True)
    book = auth_headers_for(client, "book@x.com", company_name="B")
    t = create_training(client, prov, starts_at="2020-01-01T09:00:00",
                        ends_at="2020-01-01T17:00:00")
    res = client.post("/api/bookings", headers=book,
                      json={"training_id": t["id"], "seats": 1})
    assert res.status_code == 400


def test_duplicate_booking_rejected_until_cancelled(client):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    dup = client.post("/api/bookings", headers=book,
                      json={"training_id": tid, "seats": 1})
    assert dup.status_code == 409
    # Après annulation, une nouvelle demande est possible
    assert client.delete(f"/api/bookings/{b['id']}", headers=book).status_code == 200
    assert client.post("/api/bookings", headers=book,
                       json={"training_id": tid, "seats": 1}).status_code == 201


def test_duplicate_booking_rejected_when_confirmed_room(client):
    prov = auth_headers_for(client, "prov@x.com", company_name="P", with_siret=True)
    book = auth_headers_for(client, "book@x.com", company_name="B")
    r = create_room(client, prov)
    b = create_booking(client, book, room_id=r["id"], seats=1)
    client.patch(f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"})
    assert client.post("/api/bookings", headers=book,
                       json={"room_id": r["id"], "seats": 1}).status_code == 409


def test_booker_cancel_is_soft(client, app):
    prov, book, tid = _setup(client)
    b = create_booking(client, book, training_id=tid, seats=1)
    assert client.get("/api/bookings/counts", headers=prov).get_json()[
        "pending_incoming_training"] == 1
    assert client.delete(f"/api/bookings/{b['id']}", headers=book).status_code == 200
    with app.app_context():
        assert db.session.get(Booking, b["id"]).status == "cancelled"
    assert client.get("/api/bookings/counts", headers=prov).get_json()[
        "pending_incoming_training"] == 0
    # Deuxième annulation / confirmation tardive : 400
    assert client.delete(f"/api/bookings/{b['id']}", headers=book).status_code == 400
    assert client.patch(f"/api/bookings/{b['id']}", headers=prov,
                        json={"status": "confirmed"}).status_code == 400


def test_booking_survives_email_failure(client, monkeypatch):
    def boom(*a, **k):
        raise OSError("smtp down")
    monkeypatch.setenv("MAIL_SERVER", "smtp.invalid")
    monkeypatch.setattr("app.services.mailer.smtplib.SMTP", boom)
    prov, book, tid = _setup(client)
    b = client.post("/api/bookings", headers=book,
                    json={"training_id": tid, "seats": 1})
    assert b.status_code == 201
    r = client.patch(f"/api/bookings/{b.get_json()['id']}", headers=prov,
                     json={"status": "confirmed"})
    assert r.status_code == 200


def test_send_email_never_raises(app, monkeypatch):
    from app.services.mailer import send_email
    monkeypatch.setenv("MAIL_SERVER", "smtp.invalid")
    monkeypatch.setattr("app.services.mailer.smtplib.SMTP",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    with app.app_context():
        assert send_email("a@x.com", "s", "b") is False


# ── Offres : visibilité et PATCH ─────────────────────────────────────────────

def test_non_open_offer_hidden_except_owner(client):
    prov, book, tid = _setup(client)
    r = create_room(client, prov)
    client.patch(f"/api/trainings/{tid}", headers=prov, json={"status": "closed"})
    client.patch(f"/api/rooms/{r['id']}", headers=prov, json={"status": "cancelled"})
    assert client.get(f"/api/trainings/{tid}", headers=book).status_code == 404
    assert client.get(f"/api/rooms/{r['id']}", headers=book).status_code == 404
    assert client.get(f"/api/trainings/{tid}", headers=prov).status_code == 200
    assert client.get(f"/api/rooms/{r['id']}", headers=prov).status_code == 200


def test_shared_seats_cannot_drop_below_confirmed(client):
    prov, book, tid = _setup(client, seats=5)
    b = create_booking(client, book, training_id=tid, seats=3)
    client.patch(f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"})
    url = f"/api/trainings/{tid}"
    assert client.patch(url, headers=prov, json={"shared_seats": 2}).status_code == 400
    assert client.patch(url, headers=prov, json={"shared_seats": 3}).status_code == 200


def test_room_shared_seats_below_confirmed(client):
    prov = auth_headers_for(client, "prov@x.com", company_name="P", with_siret=True)
    book = auth_headers_for(client, "book@x.com", company_name="B")
    r = create_room(client, prov, shared_seats=4)
    b = create_booking(client, book, room_id=r["id"], seats=3)
    client.patch(f"/api/bookings/{b['id']}", headers=prov, json={"status": "confirmed"})
    assert client.patch(f"/api/rooms/{r['id']}", headers=prov,
                        json={"shared_seats": 1}).status_code == 400


def test_patch_dates_validated_against_existing(client):
    prov, _, tid = _setup(client)
    url = f"/api/trainings/{tid}"
    # ends_at avant le starts_at existant
    res = client.patch(url, headers=prov, json={"ends_at": future_dt(1)})
    assert res.status_code == 422
    res = client.patch(url, headers=prov, json={"starts_at": future_dt(90)})
    assert res.status_code == 422
    assert client.patch(url, headers=prov,
                        json={"starts_at": future_dt(30, 10)}).status_code == 200
    r = create_room(client, prov)
    assert client.patch(f"/api/rooms/{r['id']}", headers=prov,
                        json={"ends_at": future_dt(1)}).status_code == 422


def test_patch_single_aware_date_no_typeerror(client):
    prov, _, tid = _setup(client)
    url = f"/api/trainings/{tid}"
    cur = client.get(url, headers=prov).get_json()
    base = cur["ends_at"][:19]
    res = client.patch(url, headers=prov, json={"ends_at": base + "Z"})
    assert res.status_code == 200
    assert res.get_json()["ends_at"][:19] == base
    res = client.patch(url, headers=prov, json={"ends_at": cur["starts_at"][:19] + "Z"})
    assert res.status_code == 422
    r = create_room(client, prov)
    ru = f"/api/rooms/{r['id']}"
    assert client.patch(ru, headers=prov,
                        json={"starts_at": r["starts_at"][:19] + "+00:00"}).status_code == 200
    assert client.patch(ru, headers=prov,
                        json={"ends_at": r["starts_at"][:19] + "Z"}).status_code == 422


# ── Invite info ──────────────────────────────────────────────────────────────

def test_invite_info(client, app):
    data = register_and_login(client, "adm@x.com", company_name="Acme")
    with app.app_context():
        tok = create_invite_token("New@X.com", "admin", data["user"]["company_id"])
    res = client.get(f"/api/auth/invite-info?token={tok}")
    assert res.status_code == 200
    assert res.get_json() == {"email": "new@x.com", "company_name": "Acme", "role": "admin"}


def test_invite_info_invalid_expired_used(client, app):
    data = register_and_login(client, "adm@x.com", company_name="Acme")
    assert client.get("/api/auth/invite-info?token=garbage").status_code == 400
    assert client.get("/api/auth/invite-info").status_code == 422
    with app.app_context():
        tok = create_invite_token("n@x.com", "member", data["user"]["company_id"])
        used = create_invite_token("adm@x.com", "member", data["user"]["company_id"])
    assert client.get(f"/api/auth/invite-info?token={used}").status_code == 400
    app.config["INVITE_MAX_AGE"] = -1
    assert client.get(f"/api/auth/invite-info?token={tok}").status_code == 400


# ── Config production ────────────────────────────────────────────────────────

def _prod_cfg(**over):
    cfg = {"SECRET_KEY": "a" * 40, "JWT_SECRET_KEY": "b" * 40,
           "PUBLIC_URL": "https://avyro.example",
           "CORS_ORIGINS": ["https://avyro.example"]}
    cfg.update(over)
    return cfg


def test_prod_config_valid():
    validate_production_config(_prod_cfg())


@pytest.mark.parametrize("key", ["SECRET_KEY", "JWT_SECRET_KEY"])
@pytest.mark.parametrize("bad", [None, "", "dev-secret-change-me" + "x" * 20,
                                 "change-me" + "x" * 30, "short"])
def test_prod_config_rejects_bad_secrets(key, bad):
    with pytest.raises(ConfigError):
        validate_production_config(_prod_cfg(**{key: bad}))


def test_prod_config_requires_public_url_and_distinct_keys():
    with pytest.raises(ConfigError):
        validate_production_config(_prod_cfg(PUBLIC_URL=""))
    with pytest.raises(ConfigError):
        validate_production_config(_prod_cfg(JWT_SECRET_KEY="a" * 40))


@pytest.mark.parametrize("bad", [[], None])
def test_prod_config_requires_cors_origins(bad):
    with pytest.raises(ConfigError):
        validate_production_config(_prod_cfg(CORS_ORIGINS=bad))


def test_create_app_production_fails_with_default_secrets(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "")
    with pytest.raises(ConfigError):
        create_app("production")


def test_create_app_production_ok_and_health(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "a" * 40)
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "b" * 40)
    monkeypatch.setattr(ProductionConfig, "PUBLIC_URL", "https://avyro.example")
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://avyro.example"])
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    app = create_app("production")
    assert app.config["CORS_ORIGINS"] == ["https://avyro.example"]
    res = app.test_client().get("/api/health")
    assert res.get_json() == {"status": "ok", "env": "production"}


def test_dev_defaults(app):
    assert app.config["CORS_ORIGINS"] == "*"
    assert app.config["PUBLIC_URL"]


# ── Geocode ──────────────────────────────────────────────────────────────────

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_geocode_ok(client, monkeypatch):
    seen = {}

    def fake(req, timeout=None):
        seen["url"], seen["ua"], seen["timeout"] = (
            req.full_url, req.get_header("User-agent"), timeout)
        return _Resp(json.dumps([
            {"display_name": "10 Rue X, Paris", "lat": "48.85", "lon": "2.35",
             "address": {"house_number": "10", "road": "Rue X",
                         "postcode": "75001", "town": "Paris"}},
            {"display_name": "Y", "lat": "1", "lon": "2",
             "address": {"road": "Rue Y", "municipality": "Z"}},
            {"display_name": "Nowhere", "lat": "3", "lon": "4"},
        ]).encode())

    monkeypatch.setattr("app.api.geocode.urlopen", fake)
    res = client.get("/api/geocode?q=Paris")
    assert res.status_code == 200
    assert res.get_json() == [
        {"label": "10 Rue X, Paris", "lat": 48.85, "lng": 2.35,
         "line1": "10 Rue X", "postal_code": "75001", "city": "Paris"},
        {"label": "Y", "lat": 1.0, "lng": 2.0,
         "line1": "Rue Y", "postal_code": "", "city": "Z"},
        {"label": "Nowhere", "lat": 3.0, "lng": 4.0,
         "line1": "", "postal_code": "", "city": ""},
    ]
    assert "addressdetails=1" in seen["url"]
    assert seen["ua"] == "Avyro/1.0" and seen["timeout"]
    assert "nominatim.openstreetmap.org/search" in seen["url"]
    assert "format=json" in seen["url"] and "limit=5" in seen["url"]


@pytest.mark.parametrize("exc", [URLError("down"), TimeoutError()])
def test_geocode_upstream_errors_502(client, monkeypatch, exc):
    def fake(*a, **k):
        raise exc
    monkeypatch.setattr("app.api.geocode.urlopen", fake)
    assert client.get("/api/geocode?q=Paris").status_code == 502


def test_geocode_bad_payload_502(client, monkeypatch):
    monkeypatch.setattr("app.api.geocode.urlopen",
                        lambda *a, **k: _Resp(b"<html>"))
    assert client.get("/api/geocode?q=Paris").status_code == 502


def test_geocode_validation(client):
    assert client.get("/api/geocode").status_code == 422
    assert client.get("/api/geocode?q=ab").status_code == 422
