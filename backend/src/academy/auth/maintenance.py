"""``academy maintenance purge-unverified``: delete unverified accounts older than 30 days (D4)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete

from academy.auth.models import Account
from academy.auth.sessions import now
from academy.db.session import _factory

UNVERIFIED_RETENTION = timedelta(days=30)


def purge_unverified() -> int:
    with _factory()() as db, db.begin():
        result = db.execute(
            delete(Account).where(
                Account.status == "pending_verification",
                Account.created_at < now() - UNVERIFIED_RETENTION,
            )
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]
