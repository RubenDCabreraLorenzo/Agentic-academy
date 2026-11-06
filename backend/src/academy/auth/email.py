"""``EmailSender`` port with SMTP, console and in-memory adapters (research R5)."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from academy.config import Settings, get_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, email: Email) -> None: ...


class SmtpSender:
    def __init__(self, settings: Settings) -> None:
        self.s = settings

    def send(self, email: Email) -> None:
        msg = EmailMessage()
        msg["From"] = self.s.smtp_from
        msg["To"] = email.to
        msg["Subject"] = email.subject
        msg.set_content(email.body)
        with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=10) as smtp:
            if self.s.smtp_user:
                smtp.starttls()
                smtp.login(self.s.smtp_user, self.s.smtp_password)
            smtp.send_message(msg)


class ConsoleSender:
    """Development only: prints the email (including links) to stdout, not to the log stream."""

    def send(self, email: Email) -> None:
        print(f"--- email to {email.to}: {email.subject}\n{email.body}\n---", flush=True)


class MemorySender:
    """Tests: keeps sent emails in memory."""

    def __init__(self) -> None:
        self.outbox: list[Email] = []

    def send(self, email: Email) -> None:
        self.outbox.append(email)


_sender: EmailSender | None = None


def get_sender() -> EmailSender:
    global _sender
    if _sender is None:
        s = get_settings()
        sender: EmailSender
        if s.email_backend == "smtp":
            sender = SmtpSender(s)
        elif s.email_backend == "console":
            sender = ConsoleSender()
        else:
            sender = MemorySender()
        _sender = sender
    return _sender


def set_sender(sender: EmailSender | None) -> None:
    global _sender
    _sender = sender


def send_safely(email: Email) -> None:
    """Email failures must not break the request (SC-008); the failure is logged without content."""
    try:
        get_sender().send(email)
    except Exception as exc:
        log.error("email delivery failed: %s", type(exc).__name__)


def verification_email(to: str, link: str) -> Email:
    return Email(
        to,
        "Verify your Agentic Academy account",
        f"Welcome to Agentic Academy.\n\nVerify your email address within 24 hours:\n{link}\n\n"
        "If you did not create an account, you can ignore this email.",
    )


def reset_email(to: str, link: str) -> Email:
    return Email(
        to,
        "Reset your Agentic Academy password",
        f"Reset your password within 1 hour:\n{link}\n\n"
        "If you did not request this, you can ignore this email; your password is unchanged.",
    )
