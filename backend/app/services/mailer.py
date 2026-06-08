"""
Service d'envoi d'emails.

En production : envoie via SMTP (variables MAIL_* dans .env).
En développement (MAIL_SERVER absent) : écrit les messages dans un fichier
log local (DEV_OUTBOX) pour inspection sans serveur SMTP.
"""
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import current_app

# Chemin de l'outbox de développement — relatif au répertoire courant d'exécution
# ou surchargeable via la variable d'env MAIL_DEV_OUTBOX
_DEFAULT_OUTBOX = os.path.join(os.path.dirname(__file__), "..", "..", "dev_outbox.log")
DEV_OUTBOX = os.getenv("MAIL_DEV_OUTBOX", os.path.abspath(_DEFAULT_OUTBOX))


def send_email(
    to: "str | list[str]",
    subject: str,
    body: str,
) -> None:
    """
    Envoie un email à un ou plusieurs destinataires.

    Args:
        to: Adresse email ou liste d'adresses.
        subject: Sujet du message.
        body: Corps en texte brut.
    """
    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r for r in recipients if r]  # Élimine les None / chaînes vides
    if not recipients:
        return

    server = os.getenv("MAIL_SERVER")
    sender = os.getenv("MAIL_FROM", "no-reply@avyro.app")

    if not server:
        _dev_outbox(sender, recipients, subject, body)
        return

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    port = int(os.getenv("MAIL_PORT", "587"))
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

    with smtplib.SMTP(server, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(msg)


def _dev_outbox(
    sender: str,
    recipients: list[str],
    subject: str,
    body: str,
) -> None:
    """Enregistre l'email dans un fichier local (mode développement)."""
    entry = (
        f"\n{'=' * 60}\n"
        f"EMAIL — {datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}\n"
        f"From   : {sender}\n"
        f"To     : {', '.join(recipients)}\n"
        f"Subject: {subject}\n"
        f"\n{body}\n"
    )
    try:
        with open(DEV_OUTBOX, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        pass  # Pas critique si le fichier n'est pas accessible

    try:
        current_app.logger.info(
            "EMAIL (dev outbox) → %s | %s", recipients, subject
        )
    except RuntimeError:
        pass  # Hors contexte app (ex. tests directs)
