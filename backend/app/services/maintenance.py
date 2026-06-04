"""Tâches planifiées Avyro.

1. Envoie un email de rappel au fournisseur 1 jour ouvré avant le début,
   avec la liste live des inscrits, pour valider et préparer la formation.
2. Supprime de la DB les formations terminées (date de fin atteinte).
"""
import os
from datetime import datetime, timedelta

from app.extensions import db
from app.models import Training
from app.services.mailer import send_email


def minus_one_business_day(dt):
    """Renvoie le jour ouvré précédent (saute samedi/dimanche)."""
    d = dt - timedelta(days=1)
    while d.weekday() >= 5:  # 5 = samedi, 6 = dimanche
        d -= timedelta(days=1)
    return d


def _reminder_body(t):
    attendees = t.attendees()
    lines = [
        f"Bonjour,",
        "",
        f"La formation « {t.title} » débute le "
        f"{t.starts_at.strftime('%d/%m/%Y à %H:%M')}.",
        f"Lieu : {'À distance' if t.is_remote else (t.location or '—')}",
        "",
        f"Inscrits confirmés ({sum(a['seats'] for a in attendees)} place(s)) :",
    ]
    if attendees:
        for a in attendees:
            lines.append(
                f"  - {a['company_name']} : {a['seats']} place(s) "
                f"— {a['contact_name']} ({a['contact_email']})"
            )
    else:
        lines.append("  Aucun inscrit confirmé pour le moment.")
    lines += [
        "",
        "Merci de valider et de préparer la session.",
        "— Avyro",
    ]
    return "\n".join(lines)


def send_due_reminders(now=None):
    now = now or datetime.utcnow()
    sent = 0
    pending = Training.query.filter_by(reminder_sent=False).all()
    for t in pending:
        if now < minus_one_business_day(t.starts_at):
            continue
        # Claim atomique : un seul process gagne (sûr même avec plusieurs
        # workers/schedulers concurrents).
        claimed = (
            Training.query.filter_by(id=t.id, reminder_sent=False).update(
                {"reminder_sent": True}, synchronize_session=False
            )
        )
        db.session.commit()
        if not claimed:
            continue
        recipients = [u.email for u in t.provider.users]
        send_email(
            recipients,
            f"[Avyro] Préparez « {t.title} » — récap des inscrits",
            _reminder_body(t),
        )
        sent += 1
    return sent


def purge_finished_trainings(now=None):
    now = now or datetime.utcnow()
    finished = Training.query.filter(Training.ends_at <= now).all()
    for t in finished:
        db.session.delete(t)  # cascade ORM -> supprime les bookings liés
    db.session.commit()
    return len(finished)


def run_maintenance(app):
    with app.app_context():
        reminders = send_due_reminders()
        purged = purge_finished_trainings()
        if reminders or purged:
            app.logger.info(
                "Maintenance: %s rappel(s) envoyé(s), %s formation(s) purgée(s)",
                reminders,
                purged,
            )


def start_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler

    interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        lambda: run_maintenance(app),
        "interval",
        minutes=interval,
        next_run_time=datetime.utcnow(),
    )
    scheduler.start()
    app.logger.info("Scheduler démarré (intervalle %s min)", interval)
    return scheduler
