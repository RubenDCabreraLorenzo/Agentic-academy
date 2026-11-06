"""Opaque server-side sessions, cookies and double-submit CSRF protection (research R5).

Session tokens and CSRF tokens are random; only SHA-256 hashes of session tokens are stored.
Idle timeout 7 days, absolute lifetime 30 days (initial values, review D4).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from academy.auth.models import Account, Session
from academy.config import get_settings
from academy.shared.errors import problem_response

SESSION_COOKIE = "aa_session"
CSRF_COOKIE = "aa_csrf"
CSRF_HEADER = "x-csrf-token"
IDLE_TIMEOUT = timedelta(days=7)
ABSOLUTE_LIFETIME = timedelta(days=30)
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
#: Pre-session endpoints; they are protected by rate limiting and carry no ambient authority.
CSRF_EXEMPT = {
    "/api/v1/auth/sign-in",
    "/api/v1/auth/sign-up",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/password-reset/request",
    "/api/v1/auth/password-reset/confirm",
}


def now() -> datetime:
    return datetime.now(UTC)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: DbSession, account_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    t = now()
    db.add(
        Session(
            id=uuid.uuid4(),
            account_id=account_id,
            token_hash=hash_token(token),
            created_at=t,
            last_seen_at=t,
            expires_at=t + ABSOLUTE_LIFETIME,
        )
    )
    db.flush()
    return token


def resolve_session(db: DbSession, token: str | None) -> tuple[Session, Account] | None:
    if not token:
        return None
    row = db.execute(
        select(Session, Account)
        .join(Account, Account.id == Session.account_id)
        .where(Session.token_hash == hash_token(token))
    ).first()
    if row is None:
        return None
    session, account = row
    t = now()
    if (
        session.revoked_at is not None
        or session.expires_at <= t
        or session.last_seen_at + IDLE_TIMEOUT <= t
        or account.status != "active"
    ):
        return None
    if t - session.last_seen_at > timedelta(minutes=5):
        session.last_seen_at = t
    return session, account


def revoke_session(db: DbSession, session_id: uuid.UUID) -> None:
    db.execute(update(Session).where(Session.id == session_id).values(revoked_at=now()))


def revoke_all(db: DbSession, account_id: uuid.UUID) -> None:
    db.execute(
        update(Session)
        .where(Session.account_id == account_id, Session.revoked_at.is_(None))
        .values(revoked_at=now())
    )


def set_auth_cookies(response: Response, token: str) -> None:
    secure = get_settings().cookie_secure
    max_age = int(ABSOLUTE_LIFETIME.total_seconds())
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_urlsafe(24),
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


class CsrfMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests whose ``X-CSRF-Token`` does not match the ``aa_csrf`` cookie."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        if request.method not in SAFE_METHODS and request.url.path not in CSRF_EXEMPT:
            cookie = request.cookies.get(CSRF_COOKIE, "")
            header = request.headers.get(CSRF_HEADER, "")
            if not cookie or not hmac.compare_digest(cookie, header):
                return problem_response(403, "csrf_failed", "CSRF token missing or invalid")
        return await call_next(request)
