"""Tests des tâches de maintenance (rappels email et purge)."""
from datetime import datetime, timedelta, timezone

_now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

from app.extensions import db
from app.models import Company, User, Training, Booking
from app.services import maintenance


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_training(starts_in_hours: int = 20) -> Training:
    """
    Crée en base une Training avec un inscrit confirmé.
    Retourne la Training pour inspection dans les tests.
    """
    provider = Company(name="Provider", kind="pro")
    booker = Company(name="Booker", kind="pro")
    db.session.add_all([provider, booker])
    db.session.flush()

    admin = User(
        email="admin@prov.com",
        first_name="Ad",
        last_name="Min",
        phone="0600000000",
        role="admin",
        company_id=provider.id,
    )
    admin.set_password("x")
    buser = User(
        email="b@booker.com",
        first_name="Bo",
        last_name="Ok",
        phone="0611111111",
        role="member",
        company_id=booker.id,
    )
    buser.set_password("x")
    db.session.add_all([admin, buser])
    db.session.flush()

    now = _now()
    t = Training(
        title="Formation test",
        contact_phone="0600000000",
        starts_at=now + timedelta(hours=starts_in_hours),
        ends_at=now + timedelta(hours=starts_in_hours + 4),
        shared_seats=5,
        provider_id=provider.id,
    )
    db.session.add(t)
    db.session.flush()

    db.session.add(
        Booking(
            training_id=t.id,
            company_id=booker.id,
            requested_by_id=buser.id,
            seats=2,
            status="confirmed",
        )
    )
    db.session.commit()
    return t


# ── Rappels ───────────────────────────────────────────────────────────────────

def test_reminder_sent_once(app, monkeypatch):
    """Le rappel est envoyé exactement une fois quand la date est atteinte."""
    sent = []
    monkeypatch.setattr(
        maintenance, "send_email",
        lambda to, subj, body: sent.append((to, subj, body)),
    )

    with app.app_context():
        _seed_training(starts_in_hours=20)  # < 1 jour ouvré → rappel dû

        count = maintenance.send_due_reminders()
        assert count == 1
        assert len(sent) == 1

        to, subj, body = sent[0]
        assert "admin@prov.com" in to
        assert "Booker" in body
        assert "2 place(s)" in body

        # Idempotent : pas de second envoi
        count2 = maintenance.send_due_reminders()
        assert count2 == 0
        assert len(sent) == 1  # Toujours 1


def test_reminder_not_sent_too_early(app, monkeypatch):
    """Pas de rappel si la formation commence dans plus d'1 jour ouvré."""
    sent = []
    monkeypatch.setattr(
        maintenance, "send_email", lambda *a: sent.append(a)
    )

    with app.app_context():
        _seed_training(starts_in_hours=24 * 10)  # ~10 jours plus tard
        assert maintenance.send_due_reminders() == 0
        assert sent == []


def test_reminder_body_includes_attendee_details(app, monkeypatch):
    """Le corps de l'email mentionne l'entreprise et le nombre de places."""
    bodies = []
    monkeypatch.setattr(
        maintenance, "send_email",
        lambda to, subj, body: bodies.append(body),
    )

    with app.app_context():
        _seed_training(starts_in_hours=10)
        maintenance.send_due_reminders()

    assert len(bodies) == 1
    body = bodies[0]
    assert "Booker" in body  # Nom de la Company
    assert "2 place" in body


# ── Purge ─────────────────────────────────────────────────────────────────────

def test_purge_finished_training(app):
    """Les formations terminées sont supprimées."""
    with app.app_context():
        # Crée une formation déjà terminée (starts_in_hours négatif)
        provider = Company(name="P", kind="pro")
        db.session.add(provider)
        db.session.flush()
        t = Training(
            title="Terminée",
            contact_phone="0600000000",
            starts_at=_now() - timedelta(hours=8),
            ends_at=_now() - timedelta(hours=1),
            shared_seats=5,
            provider_id=provider.id,
        )
        db.session.add(t)
        db.session.commit()
        tid = t.id

        purged = maintenance.purge_finished_trainings()
        assert purged == 1

        from app.extensions import db as _db
        assert _db.session.get(Training, tid) is None


def test_purge_does_not_remove_future_training(app):
    """Les formations futures ne sont pas purgées."""
    with app.app_context():
        _seed_training(starts_in_hours=48)
        purged = maintenance.purge_finished_trainings()
        assert purged == 0


# ── run_maintenance ───────────────────────────────────────────────────────────

def test_run_maintenance_returns_summary(app, monkeypatch):
    monkeypatch.setattr(maintenance, "send_email", lambda *a: None)
    with app.app_context():
        _seed_training(starts_in_hours=10)

    result = maintenance.run_maintenance(app)
    assert "reminders" in result
    assert "purged" in result
    assert result["reminders"] == 1
