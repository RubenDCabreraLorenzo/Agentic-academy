"""Account lifecycle (FR-045a, FR-046). Responses never reveal whether an email is registered."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from academy.auth import email as mail
from academy.auth.models import Account, OneTimeToken
from academy.auth.passwords import hash_password, verify_password
from academy.auth.sessions import create_session, hash_token, now, revoke_all, revoke_session
from academy.config import get_settings
from academy.shared.errors import ProblemError

VERIFY_TTL = timedelta(hours=24)
RESET_TTL = timedelta(hours=1)


def _normalize(email: str) -> str:
    return email.strip().lower()


def _issue_token(db: DbSession, account_id: uuid.UUID, purpose: str, ttl: timedelta) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        OneTimeToken(
            id=uuid.uuid4(),
            account_id=account_id,
            purpose=purpose,
            token_hash=hash_token(token),
            expires_at=now() + ttl,
        )
    )
    db.flush()
    return token


def _consume_token(db: DbSession, token: str, purpose: str) -> OneTimeToken:
    row = db.scalar(
        select(OneTimeToken)
        .where(OneTimeToken.token_hash == hash_token(token), OneTimeToken.purpose == purpose)
        .with_for_update()
    )
    if row is None or row.used_at is not None or row.expires_at <= now():
        raise ProblemError(400, "invalid_token", "This link is invalid or has expired")
    row.used_at = now()
    return row


def sign_up(db: DbSession, email: str, password: str) -> None:
    address = _normalize(email)
    password_hash = hash_password(password)
    existing = db.scalar(select(Account).where(Account.email == address))
    if existing is not None:
        if existing.status == "pending_verification":
            send_verification(db, existing)
        return
    account = Account(id=uuid.uuid4(), email=address, password_hash=password_hash)
    db.add(account)
    db.flush()
    send_verification(db, account)


def send_verification(db: DbSession, account: Account) -> None:
    token = _issue_token(db, account.id, "verify_email", VERIFY_TTL)
    link = f"{get_settings().public_base_url}/verify-email?token={token}"
    mail.send_safely(mail.verification_email(account.email, link))


def verify_email(db: DbSession, token: str) -> None:
    row = _consume_token(db, token, "verify_email")
    account = db.get(Account, row.account_id)
    if account is None:
        raise ProblemError(400, "invalid_token", "This link is invalid or has expired")
    if account.status == "pending_verification":
        account.status = "active"
        account.email_verified_at = now()


def sign_in(db: DbSession, email: str, password: str) -> tuple[Account, str]:
    account = db.scalar(select(Account).where(Account.email == _normalize(email)))
    if not verify_password(account.password_hash if account else None, password) or account is None:
        raise ProblemError(401, "invalid_credentials", "Email or password is incorrect")
    if account.status == "pending_verification":
        raise ProblemError(403, "email_not_verified", "Verify your email address before signing in")
    if account.status != "active":
        raise ProblemError(401, "invalid_credentials", "Email or password is incorrect")
    return account, create_session(db, account.id)


def sign_out(db: DbSession, session_id: uuid.UUID) -> None:
    revoke_session(db, session_id)


def request_password_reset(db: DbSession, email: str) -> None:
    account = db.scalar(select(Account).where(Account.email == _normalize(email)))
    if account is None or account.status == "deleted":
        return
    token = _issue_token(db, account.id, "reset_password", RESET_TTL)
    link = f"{get_settings().public_base_url}/reset-password?token={token}"
    mail.send_safely(mail.reset_email(account.email, link))


def confirm_password_reset(db: DbSession, token: str, new_password: str) -> None:
    password_hash = hash_password(new_password)
    row = _consume_token(db, token, "reset_password")
    account = db.get(Account, row.account_id)
    if account is None:
        raise ProblemError(400, "invalid_token", "This link is invalid or has expired")
    account.password_hash = password_hash
    if account.status == "pending_verification":
        # Receiving the reset email proves ownership of the address.
        account.status = "active"
        account.email_verified_at = now()
    revoke_all(db, account.id)


def delete_account(db: DbSession, account_id: uuid.UUID) -> None:
    """Hard-delete the account; all learner rows cascade in the same transaction (FR-046)."""
    from academy.shared.hooks import run_before_account_delete

    run_before_account_delete(db, account_id)
    db.execute(delete(Account).where(Account.id == account_id))
