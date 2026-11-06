"""``academy dev seed``: a verified demo learner for local development and end-to-end tests."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from academy.auth.models import Account
from academy.auth.passwords import hash_password
from academy.auth.sessions import now
from academy.config import get_settings
from academy.db.session import _factory

DEMO_EMAIL = "demo@academy.local"
DEMO_PASSWORD = "demo-password-123"  # noqa: S105 - development seed only


def seed() -> int:
    if get_settings().app_env == "production":
        print("refusing to seed demo data in production")
        return 1
    with _factory()() as db, db.begin():
        if db.scalar(select(Account).where(Account.email == DEMO_EMAIL)) is None:
            db.add(
                Account(
                    id=uuid.uuid4(),
                    email=DEMO_EMAIL,
                    password_hash=hash_password(DEMO_PASSWORD),
                    status="active",
                    email_verified_at=now(),
                )
            )
    print(f"demo learner: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    return 0
