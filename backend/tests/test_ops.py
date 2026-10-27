"""Tests exploitation : migrations, .env, seed, CLI, purge."""
import logging
import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest
from flask_migrate import downgrade, upgrade

from app import create_app
from app.config import TestingConfig, load_env_files
from app.extensions import db
from app.models import Company, Room, Training, User
from app.services import maintenance
from tests.conftest import auth_headers_for, future_dt


@pytest.fixture
def migrated(tmp_path, monkeypatch):
    """App de test branchée sur un fichier SQLite vierge (sans create_all)."""
    path = tmp_path / "mig.db"
    monkeypatch.setattr(TestingConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{path}")
    app = create_app("testing")
    with app.app_context():
        upgrade()
        yield app, path
        db.session.remove()


def test_upgrade_creates_schema_from_scratch(migrated):
    _, path = migrated
    con = sqlite3.connect(path)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    assert {"users", "companies", "trainings", "rooms", "bookings",
            "token_blocklist", "alembic_version"} <= tables
    cols = {r[1]: r for r in con.execute("pragma table_info(bookings)")}
    assert cols["requested_by_id"][3] == 0  # nullable
    idx = {r[1] for r in con.execute("pragma index_list(users)")}
    assert "uq_users_email_lower" in idx
    con.close()


def test_lower_email_unique_enforced_by_db(migrated):
    with db.engine.begin() as c:
        c.exec_driver_sql("insert into companies (name, kind, created_at, updated_at) "
                          "values ('c','pro','2026-01-01','2026-01-01')")
        ins = ("insert into users (email,password_hash,first_name,last_name,phone,role,"
               "company_id,created_at,updated_at) values (?, 'h','a','b','1','member',1,"
               "'2026-01-01','2026-01-01')")
        c.exec_driver_sql(ins, ("A@x.com",))
    with pytest.raises(Exception):
        with db.engine.begin() as c:
            c.exec_driver_sql(ins, ("a@X.com",))


def test_downgrade_to_base(migrated):
    _, path = migrated
    downgrade(revision="base")
    con = sqlite3.connect(path)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    assert "users" not in tables
    con.close()


def test_create_db_cli_refused_in_production(monkeypatch):
    from app.config import ProductionConfig
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "a" * 40)
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "b" * 40)
    monkeypatch.setattr(ProductionConfig, "PUBLIC_URL", "https://x.test")
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://x.test"])
    app = create_app("production")
    res = app.test_cli_runner().invoke(args=["create-db"])
    assert res.exit_code != 0 and "interdit en production" in res.output


def test_create_db_cli_ok_in_testing(app):
    res = app.test_cli_runner().invoke(args=["create-db"])
    assert res.exit_code == 0


def test_load_env_files(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("AVYRO_TEST_A=from_file\nAVYRO_TEST_B=from_file\n")
    monkeypatch.setenv("AVYRO_TEST_B", "from_env")
    monkeypatch.delenv("AVYRO_TEST_A", raising=False)
    load_env_files([env, tmp_path / "absent.env"])
    import os
    assert os.environ["AVYRO_TEST_A"] == "from_file"
    assert os.environ["AVYRO_TEST_B"] == "from_env"  # l'environnement prime
    monkeypatch.delenv("AVYRO_TEST_A")


def test_seed_demo(client, app, monkeypatch):
    import seed_demo
    with app.app_context():
        with pytest.raises(SystemExit):
            seed_demo.seed()  # aucune company
    auth_headers_for(client, "a@x.com", company_name="Old")
    with app.app_context():
        seed_demo.seed()
        assert Training.query.count() == len(seed_demo.TRAININGS)
        assert Room.query.count() == len(seed_demo.ROOMS)
        assert Company.query.first().name == seed_demo.COMPANY_NAMES[0]
    monkeypatch.setenv("FLASK_ENV", "production")
    with pytest.raises(SystemExit):
        seed_demo.main()


def test_seed_demo_main_dev(monkeypatch, tmp_path):
    import seed_demo
    monkeypatch.setenv("FLASK_ENV", "testing")
    called = []
    monkeypatch.setattr(seed_demo, "seed", lambda: called.append(1))
    seed_demo.main()
    assert called == [1]


def test_purge_removes_finished_rooms_and_trainings(app):
    from datetime import datetime
    now = datetime(2030, 1, 1)
    with app.app_context():
        c = Company(name="c")
        db.session.add(c)
        db.session.flush()
        common = dict(contact_phone="1", shared_seats=1, provider_id=c.id,
                      starts_at=now - timedelta(days=2), ends_at=now - timedelta(days=1))
        db.session.add_all([Room(title="r", **common), Training(title="t", **common)])
        db.session.commit()
        assert not hasattr(maintenance, "purge_finished_trainings")
        assert maintenance.purge_finished_offers(now) == 2
        assert Room.query.count() == 0 and Training.query.count() == 0


def test_dev_outbox_failure_is_logged(app, monkeypatch, caplog, tmp_path):
    from app.services import mailer
    monkeypatch.delenv("MAIL_SERVER", raising=False)
    monkeypatch.setattr(mailer, "DEV_OUTBOX", str(tmp_path / "no" / "dir" / "x.log"))
    with app.app_context(), caplog.at_level(logging.WARNING):
        assert mailer.send_email("a@x.com", "s", "b") is True
    assert "Dev outbox inaccessible" in caplog.text


def test_db_url_normalisation(monkeypatch):
    from app.config import _db_url
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/d")
    assert _db_url("x") == "postgresql+psycopg2://u:p@h/d"
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/d")
    assert _db_url("x") == "postgresql+psycopg2://u:p@h/d"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///a.db")
    assert _db_url("x") == "sqlite:///a.db"
