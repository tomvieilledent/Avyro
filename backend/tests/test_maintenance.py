"""Tests des tâches de maintenance (rappels email et purge)."""
from datetime import datetime, timedelta, timezone

_now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

from app.extensions import db
from app.models import Company, User, Training, Room, Booking
from app.services import maintenance


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_training(starts_in_hours: int = 20, confirmed_seats: int = 2) -> Training:
    """Crée une Training avec un inscrit confirmé."""
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
        shared_seats=10,
        provider_id=provider.id,
    )
    db.session.add(t)
    db.session.flush()

    if confirmed_seats > 0:
        db.session.add(
            Booking(
                training_id=t.id,
                company_id=booker.id,
                requested_by_id=buser.id,
                seats=confirmed_seats,
                status="confirmed",
            )
        )
    db.session.commit()
    return t


def _seed_room(starts_in_hours: int = 20) -> Room:
    """Crée une Room avec un inscrit confirmé."""
    provider = Company(name="RoomProvider", kind="pro")
    booker = Company(name="RoomBooker", kind="pro")
    db.session.add_all([provider, booker])
    db.session.flush()

    admin = User(
        email="admin@roomprov.com",
        first_name="R",
        last_name="Adm",
        phone="0600000002",
        role="admin",
        company_id=provider.id,
    )
    admin.set_password("x")
    buser = User(
        email="b@roombooker.com",
        first_name="RB",
        last_name="Ok",
        phone="0611111112",
        role="member",
        company_id=booker.id,
    )
    buser.set_password("x")
    db.session.add_all([admin, buser])
    db.session.flush()

    now = _now()
    r = Room(
        title="Salle test",
        contact_phone="0600000000",
        starts_at=now + timedelta(hours=starts_in_hours),
        ends_at=now + timedelta(hours=starts_in_hours + 4),
        shared_seats=4,
        provider_id=provider.id,
    )
    db.session.add(r)
    db.session.flush()

    db.session.add(
        Booking(
            room_id=r.id,
            company_id=booker.id,
            requested_by_id=buser.id,
            seats=2,
            status="confirmed",
        )
    )
    db.session.commit()
    return r


# ── Rappels : formations ──────────────────────────────────────────────────────

def test_reminder_sent_once(app, monkeypatch):
    """Le rappel est envoyé exactement une fois quand la date est atteinte."""
    sent = []
    monkeypatch.setattr(
        maintenance, "send_email",
        lambda to, subj, body: sent.append((to, subj, body)),
    )

    with app.app_context():
        _seed_training(starts_in_hours=20)
        count = maintenance.send_due_reminders()
        assert count == 1
        assert len(sent) == 1

        to, subj, body = sent[0]
        assert "admin@prov.com" in to
        assert "Booker" in body
        assert "2 place(s)" in body

        # Idempotent : pas de second envoi
        assert maintenance.send_due_reminders() == 0
        assert len(sent) == 1


def test_reminder_not_sent_too_early(app, monkeypatch):
    sent = []
    monkeypatch.setattr(maintenance, "send_email", lambda *a: sent.append(a))

    with app.app_context():
        _seed_training(starts_in_hours=24 * 10)
        assert maintenance.send_due_reminders() == 0
        assert sent == []


def test_reminder_body_includes_attendee_details(app, monkeypatch):
    bodies = []
    monkeypatch.setattr(
        maintenance, "send_email",
        lambda to, subj, body: bodies.append(body),
    )

    with app.app_context():
        _seed_training(starts_in_hours=10)
        maintenance.send_due_reminders()

    assert len(bodies) == 1
    assert "Booker" in bodies[0]
    assert "2 place" in bodies[0]


def test_reminder_sent_with_no_confirmed_bookings_mentions_zero(app, monkeypatch):
    """Le rappel est envoyé même sans inscrit — le corps mentionne 'Aucun inscrit'."""
    bodies = []
    monkeypatch.setattr(
        maintenance, "send_email",
        lambda to, subj, body: bodies.append(body),
    )

    with app.app_context():
        _seed_training(starts_in_hours=10, confirmed_seats=0)
        count = maintenance.send_due_reminders()
        assert count == 1
        assert "Aucun inscrit" in bodies[0]


# ── Purge : formations ────────────────────────────────────────────────────────

def test_purge_finished_training(app):
    with app.app_context():
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
        assert db.session.get(Training, tid) is None


def test_purge_does_not_remove_future_training(app):
    with app.app_context():
        _seed_training(starts_in_hours=48)
        assert maintenance.purge_finished_trainings() == 0


def test_purge_does_not_remove_ongoing_training(app):
    """Formation en cours (starts passé mais ends futur) : non purgée."""
    with app.app_context():
        provider = Company(name="POngoing", kind="pro")
        db.session.add(provider)
        db.session.flush()
        t = Training(
            title="En cours",
            contact_phone="0600000000",
            starts_at=_now() - timedelta(hours=2),
            ends_at=_now() + timedelta(hours=6),
            shared_seats=5,
            provider_id=provider.id,
        )
        db.session.add(t)
        db.session.commit()

        assert maintenance.purge_finished_trainings() == 0


# ── Purge : salles ────────────────────────────────────────────────────────────

def test_purge_finished_room(app):
    """Les salles terminées sont supprimées par purge_finished_trainings."""
    with app.app_context():
        provider = Company(name="RoomP", kind="pro")
        db.session.add(provider)
        db.session.flush()
        r = Room(
            title="Salle terminée",
            contact_phone="0600000000",
            starts_at=_now() - timedelta(hours=8),
            ends_at=_now() - timedelta(hours=1),
            shared_seats=4,
            provider_id=provider.id,
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

        purged = maintenance.purge_finished_trainings()
        assert purged == 1
        assert db.session.get(Room, rid) is None


def test_purge_does_not_remove_future_room(app):
    with app.app_context():
        _seed_room(starts_in_hours=48)
        assert maintenance.purge_finished_trainings() == 0


# ── run_maintenance ───────────────────────────────────────────────────────────

def test_run_maintenance_returns_summary(app, monkeypatch):
    monkeypatch.setattr(maintenance, "send_email", lambda *a: None)
    with app.app_context():
        _seed_training(starts_in_hours=10)

    result = maintenance.run_maintenance(app)
    assert "reminders" in result
    assert "purged" in result
    assert result["reminders"] == 1


def test_run_maintenance_purges_training_and_room(app, monkeypatch):
    """run_maintenance purge formations ET salles terminées en un seul appel."""
    monkeypatch.setattr(maintenance, "send_email", lambda *a: None)
    with app.app_context():
        provider = Company(name="PurgeProv", kind="pro")
        db.session.add(provider)
        db.session.flush()
        db.session.add(Training(
            title="Old T",
            contact_phone="0600000000",
            starts_at=_now() - timedelta(hours=8),
            ends_at=_now() - timedelta(hours=1),
            shared_seats=5,
            provider_id=provider.id,
        ))
        db.session.add(Room(
            title="Old R",
            contact_phone="0600000000",
            starts_at=_now() - timedelta(hours=8),
            ends_at=_now() - timedelta(hours=1),
            shared_seats=4,
            provider_id=provider.id,
        ))
        db.session.commit()

    result = maintenance.run_maintenance(app)
    assert result["purged"] >= 2
