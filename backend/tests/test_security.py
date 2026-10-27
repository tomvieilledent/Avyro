"""Tests durcissement : en-têtes, docs, ProxyFix, limiteur, révocation JWT."""
import logging
from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token, decode_token

from app import create_app
from app.config import ProductionConfig, TestingConfig
from app.extensions import db, limiter
from app.models import TokenBlocklist
from app.services import maintenance
from app.utils.jwt_handlers import purge_expired_blocklist, revoke_token
from tests.conftest import register_and_login


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture
def prod_app(monkeypatch, tmp_path):
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "a" * 40)
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "b" * 40)
    monkeypatch.setattr(ProductionConfig, "PUBLIC_URL", "https://x.test")
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://x.test"])
    monkeypatch.setattr(ProductionConfig, "OPENAPI_URL_PREFIX", None)
    spa = tmp_path / "spa"
    spa.mkdir()
    (spa / "index.html").write_text("<html></html>")
    monkeypatch.setenv("SERVE_FRONTEND", str(spa))
    return create_app("production")


# ── S14 : en-têtes ───────────────────────────────────────────────────────────

def test_api_security_headers(client):
    h = client.get("/api/health").headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert "default-src 'none'" in h["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in h  # hors prod


def test_docs_csp_allows_swagger_cdn(client):
    res = client.get("/api/docs")
    assert res.status_code == 200
    assert "cdn.jsdelivr.net" in res.headers["Content-Security-Policy"]


def test_prod_spa_headers_hsts_and_no_docs(prod_app):
    c = prod_app.test_client()
    res = c.get("/some/client/route")
    assert res.status_code == 200
    h = res.headers
    assert "max-age=" in h["Strict-Transport-Security"]
    csp = h["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert "unsafe-inline" not in csp.split("style-src-attr")[0]
    for url in ("/api/docs", "/api/openapi.json"):
        assert c.get(url).status_code == 404
    assert c.get("/api/health").headers["Strict-Transport-Security"]


def test_prod_docs_can_be_enabled_by_env(monkeypatch):
    monkeypatch.setenv("API_DOCS_ENABLED", "1")
    import importlib
    import app.config as cfg
    try:
        importlib.reload(cfg)
        assert cfg.ProductionConfig.OPENAPI_URL_PREFIX == "/api"
    finally:
        monkeypatch.delenv("API_DOCS_ENABLED")
        importlib.reload(cfg)
    assert cfg.ProductionConfig.OPENAPI_URL_PREFIX is None


# ── S7 : ProxyFix, stockage du limiteur ──────────────────────────────────────

def test_proxyfix_applied_when_configured(monkeypatch):
    monkeypatch.setattr(TestingConfig, "TRUSTED_PROXY_COUNT", 1)
    app = create_app("testing")
    seen = {}

    @app.get("/_ip")
    def _ip():
        from flask import request
        seen["ip"], seen["scheme"] = request.remote_addr, request.scheme
        return "ok"

    app.test_client().get("/_ip", headers={
        "X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "https"})
    assert seen == {"ip": "203.0.113.9", "scheme": "https"}


def test_no_proxyfix_by_default(client, app):
    @app.get("/_ip")
    def _ip():
        from flask import request
        return request.remote_addr

    res = client.get("/_ip", headers={"X-Forwarded-For": "203.0.113.9"})
    assert res.get_data(as_text=True) != "203.0.113.9"


def test_prod_warns_on_memory_limiter_and_no_proxy(monkeypatch, caplog):
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "a" * 40)
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "b" * 40)
    monkeypatch.setattr(ProductionConfig, "PUBLIC_URL", "https://x.test")
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://x.test"])
    with caplog.at_level(logging.WARNING):
        create_app("production")
    assert "RATELIMIT_STORAGE_URI=memory://" in caplog.text
    assert "TRUSTED_PROXY_COUNT=0" in caplog.text


@pytest.fixture
def limited_client(monkeypatch):
    monkeypatch.setattr(TestingConfig, "RATELIMIT_ENABLED", True)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        limiter.reset()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
        limiter.reset()


def test_refresh_is_rate_limited(limited_client):
    data = register_and_login(limited_client, "r@x.com")
    codes = [limited_client.post("/api/auth/refresh",
                                 headers=_bearer(data["refresh_token"])).status_code
             for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429


def test_accept_invite_is_rate_limited(limited_client):
    codes = [limited_client.post("/api/auth/accept-invite", json={
        "token": "bad", "first_name": "A", "last_name": "B",
        "phone": "0600000000", "password": "password123"}).status_code
        for _ in range(11)]
    assert codes[:10] == [400] * 10 and codes[10] == 429


# ── S8 : révocation ──────────────────────────────────────────────────────────

def test_logout_revokes_access_and_refresh(client):
    d = register_and_login(client, "l@x.com")
    res = client.post("/api/auth/logout", headers=_bearer(d["access_token"]),
                      json={"refresh_token": d["refresh_token"]})
    assert res.status_code == 200
    assert client.get("/api/auth/me", headers=_bearer(d["access_token"])).status_code == 401
    r = client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"]))
    assert r.status_code == 401 and r.get_json()["error"] == "unauthorized"


def test_logout_without_refresh_token_invalidates_all_refresh(client):
    d = register_and_login(client, "l@x.com")
    assert client.post("/api/auth/logout", headers=_bearer(d["access_token"])).status_code == 200
    assert client.get("/api/auth/me", headers=_bearer(d["access_token"])).status_code == 401
    # sans refresh_token fourni : token_version incrémenté, refresh existants invalidés
    assert client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).status_code == 401


def test_logout_with_refresh_token_itself(client):
    d = register_and_login(client, "l@x.com")
    assert client.post("/api/auth/logout", headers=_bearer(d["refresh_token"]),
                       json={}).status_code == 200
    assert client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).status_code == 401


def test_logout_requires_auth_and_valid_refresh(client):
    assert client.post("/api/auth/logout").status_code == 401
    d = register_and_login(client, "l@x.com")
    other = register_and_login(client, "o@x.com")
    h = _bearer(d["access_token"])
    for bad in ("garbage", d["access_token"], other["refresh_token"]):
        assert client.post("/api/auth/logout", headers=h,
                           json={"refresh_token": bad}).status_code == 400
    # rien n'a été révoqué par les tentatives invalides
    assert client.get("/api/auth/me", headers=h).status_code == 200


def test_delete_account_revokes_token(client, app):
    d = register_and_login(client, "d@x.com")
    h = _bearer(d["access_token"])
    assert client.delete("/api/auth/me", headers=h).status_code == 200
    assert client.get("/api/auth/me", headers=h).status_code == 401
    with app.app_context():
        assert TokenBlocklist.query.count() == 1


def test_password_change_revokes_old_refresh_tokens(client):
    d = register_and_login(client, "p@x.com", password="password123")
    h = _bearer(d["access_token"])
    assert client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).status_code == 200
    res = client.patch("/api/auth/me", headers=h, json={"password": "newpassword456"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["email"] == "p@x.com" and "password_hash" not in body
    # anciens tokens (refresh ET access) refusés ; la paire neuve fonctionne
    assert client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).status_code == 401
    assert client.get("/api/auth/me", headers=h).status_code == 401
    assert client.get("/api/auth/me", headers=_bearer(body["access_token"])).status_code == 200
    assert client.post("/api/auth/refresh",
                       headers=_bearer(body["refresh_token"])).status_code == 200
    # nouvelle connexion : nouveau refresh valide
    login = client.post("/api/auth/login",
                        json={"email": "p@x.com", "password": "newpassword456"}).get_json()
    assert client.post("/api/auth/refresh",
                       headers=_bearer(login["refresh_token"])).status_code == 200


def test_profile_update_without_password_keeps_refresh_valid(client):
    d = register_and_login(client, "p@x.com")
    res = client.patch("/api/auth/me", headers=_bearer(d["access_token"]), json={"first_name": "Z"})
    assert "access_token" not in res.get_json() and "refresh_token" not in res.get_json()
    assert client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).status_code == 200


def test_revoke_token_idempotent_and_purge(app):
    with app.app_context():
        tok = create_access_token(identity="1")
        payload = decode_token(tok)
        revoke_token(payload)
        revoke_token(payload)
        db.session.commit()
        assert TokenBlocklist.query.count() == 1
        row = TokenBlocklist.query.first()
        assert row.user_id == 1 and row.token_type == "access"
        # non expiré : conservé
        assert purge_expired_blocklist() == 0
        # expiré : purgé
        assert purge_expired_blocklist(datetime.utcnow() + timedelta(days=2)) == 1


def test_revoke_token_non_numeric_sub(app):
    with app.app_context():
        revoke_token(decode_token(create_access_token(identity="invite:x")))
        db.session.commit()
        assert TokenBlocklist.query.first().user_id is None


def test_maintenance_purges_expired_blocklist(app):
    with app.app_context():
        db.session.add(TokenBlocklist(jti="old", token_type="access",
                                      expires_at=datetime.utcnow() - timedelta(days=1)))
        db.session.commit()
        maintenance.run_maintenance(app)
        assert TokenBlocklist.query.count() == 0


def test_tokens_carry_tv_and_legacy_token_without_tv_is_rejected(client, app):
    d = register_and_login(client, "tv@x.com")
    assert decode_token(d["access_token"])["tv"] == 0
    r = client.post("/api/auth/refresh", headers=_bearer(d["refresh_token"])).get_json()
    assert decode_token(r["access_token"])["tv"] == 0
    uid = decode_token(d["access_token"])["sub"]
    with app.app_context():
        legacy = create_access_token(identity=uid)  # sans claim tv
    assert client.get("/api/auth/me", headers=_bearer(legacy)).status_code == 401
