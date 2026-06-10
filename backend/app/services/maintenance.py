"""
Tâches de maintenance planifiées.

1. send_due_reminders() — envoie un email de rappel au provider 1 jour ouvré
   avant le début de chaque formation/salle, avec la liste live des inscrits.
   Atomic via mise à jour conditionnelle (reminder_sent=False → True) pour
   supporter plusieurs workers/schedulers sans doublon.

2. purge_finished_trainings() — supprime les Training dont ends_at est dépassé.
   La cascade ORM supprime automatiquement les Booking associés.

Les deux fonctions sont idempotentes : les appeler plusieurs fois est sans
effet indésirable.
"""
import os
from datetime import datetime, timedelta, timezone

_now_utc = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

from app.extensions import db
from app.models import Training, Room
from app.services.mailer import send_email


def minus_one_business_day(dt: datetime) -> datetime:
    """
    Retourne le jour ouvré précédant `dt` (saute samedis et dimanches).

    Exemples :
        Lundi    → Vendredi précédent
        Mardi    → Lundi
        Samedi   → Jeudi (deux jours en arrière pour dépasser le we)
    """
    d = dt - timedelta(days=1)
    while d.weekday() >= 5:  # 5=samedi, 6=dimanche
        d -= timedelta(days=1)
    return d


def _build_reminder_body(training: Training) -> str:
    """Construit le corps de l'email de rappel pour un provider."""
    attendees = training.attendees()
    total = sum(a["seats"] for a in attendees)
    lieu = "À distance" if training.is_remote else (training.location or "—")

    lines = [
        "Bonjour,",
        "",
        f"Rappel : « {training.title} » commence le "
        f"{training.starts_at.strftime('%d/%m/%Y à %H:%M')}.",
        f"Lieu : {lieu}",
        "",
        f"Inscrits confirmés ({total} place(s)) :",
    ]

    if attendees:
        for a in attendees:
            lines.append(
                f"  • {a['company_name']} : {a['seats']} place(s)"
                f" — {a['contact_name']} ({a['contact_email']})"
            )
    else:
        lines.append("  Aucun inscrit confirmé pour le moment.")

    lines += ["", "Merci de préparer la session.", "— Avyro"]
    return "\n".join(lines)


def send_due_reminders(now: datetime | None = None) -> int:
    """
    Envoie les rappels dus et retourne le nombre d'emails envoyés.

    Un rappel est « dû » si now >= J-1 ouvré avant starts_at et que
    reminder_sent est encore False.

    Atomic : l'UPDATE conditionnel garantit qu'un seul process envoie
    le rappel même avec plusieurs workers.
    """
    now = now or _now_utc()
    sent = 0

    pending = (
        Training.query.filter_by(reminder_sent=False).all()
        + Room.query.filter_by(reminder_sent=False).all()
    )
    for t in pending:
        if now < minus_one_business_day(t.starts_at):
            continue  # Encore trop tôt

        # Claim atomique : met à jour uniquement si reminder_sent est toujours False
        model = Training if isinstance(t, Training) else Room
        claimed = (
            model.query
            .filter_by(id=t.id, reminder_sent=False)
            .update({"reminder_sent": True}, synchronize_session=False)
        )
        db.session.commit()

        if not claimed:
            continue  # Un autre worker a déjà envoyé le rappel

        recipients = [u.email for u in t.provider.users]
        send_email(
            recipients,
            f"[Avyro] Préparez « {t.title} » — récap des inscrits",
            _build_reminder_body(t),
        )
        sent += 1

    return sent


def purge_finished_trainings(now: datetime | None = None) -> int:
    """
    Supprime les Training dont ends_at est dépassé.

    Retourne le nombre de Training supprimées. La cascade SQLAlchemy
    supprime automatiquement les Booking associés.
    """
    now = now or _now_utc()
    finished = (
        Training.query.filter(Training.ends_at <= now).all()
        + Room.query.filter(Room.ends_at <= now).all()
    )
    for t in finished:
        db.session.delete(t)
    if finished:
        db.session.commit()
    return len(finished)


def run_maintenance(app) -> dict:
    """
    Lance les deux tâches de maintenance dans le contexte de l'app.

    Retourne un résumé {reminders: int, purged: int}.
    """
    with app.app_context():
        reminders = send_due_reminders()
        purged = purge_finished_trainings()
        if reminders or purged:
            app.logger.info(
                "Maintenance : %s rappel(s) envoyé(s), %s formation(s) purgée(s).",
                reminders,
                purged,
            )
        return {"reminders": reminders, "purged": purged}


def start_scheduler(app) -> object:
    """
    Démarre le scheduler APScheduler en arrière-plan.

    N'activer que sur UNE instance backend (pas compatible multi-workers
    sans stockage partagé comme Redis).
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        lambda: run_maintenance(app),
        "interval",
        minutes=interval,
        # Première exécution immédiate au démarrage
        next_run_time=_now_utc(),
    )
    scheduler.start()
    app.logger.info(
        "Scheduler démarré (intervalle=%s min, daemon=True).", interval
    )
    return scheduler
