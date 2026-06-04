from datetime import datetime, timedelta

from app.extensions import db
from app.models import Company, User, Training, Booking
from app.services import maintenance


def _seed_training_with_confirmed(starts_in_hours=20):
    provider = Company(name="Prov", kind="pro")
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
    buser = User(
        email="b@booker.com",
        first_name="Bo",
        last_name="Ok",
        phone="0611111111",
        company_id=booker.id,
    )
    admin.set_password("x")
    buser.set_password("x")
    db.session.add_all([admin, buser])
    db.session.flush()

    t = Training(
        title="T",
        contact_phone="0600000000",
        starts_at=datetime.utcnow() + timedelta(hours=starts_in_hours),
        ends_at=datetime.utcnow() + timedelta(hours=starts_in_hours + 4),
        shared_seats=5,
        total_seats=5,
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


def test_reminder_sent_once(app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        maintenance, "send_email", lambda to, subj, body: sent.append((to, subj, body))
    )
    _seed_training_with_confirmed()

    assert maintenance.send_due_reminders() == 1
    assert len(sent) == 1
    to, subj, body = sent[0]
    assert "admin@prov.com" in to
    assert "Booker" in body and "2 place(s)" in body

    # Idempotent : pas de second envoi.
    assert maintenance.send_due_reminders() == 0
    assert len(sent) == 1


def test_reminder_not_sent_too_early(app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        maintenance, "send_email", lambda *a: sent.append(a)
    )
    # Début dans ~10 jours : plus d'1 jour ouvré avant -> pas de rappel.
    _seed_training_with_confirmed(starts_in_hours=24 * 10)
    assert maintenance.send_due_reminders() == 0
    assert sent == []
