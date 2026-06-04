"""Envoi d'emails.

Utilise un serveur SMTP si `MAIL_SERVER` est configuré, sinon écrit les
messages dans un « outbox » de développement (fichier + log).
"""
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from flask import current_app

DEV_OUTBOX = os.getenv(
    "MAIL_DEV_OUTBOX", "/root/Holberton/Avyro/backend/dev_outbox.log"
)


def send_email(to, subject, body):
    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r for r in recipients if r]
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


def _dev_outbox(sender, recipients, subject, body):
    entry = (
        f"\n===== EMAIL {datetime.utcnow().isoformat()} =====\n"
        f"From: {sender}\nTo: {', '.join(recipients)}\nSubject: {subject}\n\n"
        f"{body}\n"
    )
    try:
        with open(DEV_OUTBOX, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        pass
    try:
        current_app.logger.info("EMAIL (dev outbox) -> %s | %s", recipients, subject)
    except RuntimeError:
        pass
