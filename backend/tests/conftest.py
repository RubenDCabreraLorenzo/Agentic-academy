"""Shared test fixtures.

Integration tests need PostgreSQL. ``TEST_DATABASE_URL`` points to a server where the test user
may create databases; each test session creates a fresh database and runs all migrations.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("EMAIL_BACKEND", "memory")
os.environ.setdefault("SESSION_SECRET", "x" * 40)
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("RUNNER_DB_PASSWORD", "runner")

# Sample course content, including learner-facing test files that must not be collected. Declared
# here because a pytest ``--ignore`` option would be relative to the directory pytest is run from.
collect_ignore = ["fixtures"]

BACKEND = Path(__file__).resolve().parents[1]
ADMIN_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://academy:academy@localhost:5432/academy"
)


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    sa = pytest.importorskip("sqlalchemy")
    admin = sa.create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    name = f"academy_test_{uuid.uuid4().hex[:8]}"
    try:
        with admin.connect() as conn:
            conn.execute(sa.text(f'CREATE DATABASE "{name}"'))
    except sa.exc.OperationalError:
        pytest.skip("PostgreSQL not available (set TEST_DATABASE_URL)")
    url = ADMIN_URL.rsplit("/", 1)[0] + f"/{name}"
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.cmd_opts = None
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    os.environ["DATABASE_URL"] = url
    from academy.config import get_settings

    get_settings.cache_clear()
    command.upgrade(cfg, "head")
    yield url
    from academy.db import session as db_session

    db_session.get_engine.cache_clear()
    db_session._factory.cache_clear()
    with admin.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))


@pytest.fixture
def app(database_url: str, tmp_path: Path):  # type: ignore[no-untyped-def]
    from academy.auth import email as mail
    from academy.auth import rate_limit
    from academy.config import get_settings
    from academy.main import create_app

    get_settings.cache_clear()
    mail.set_sender(mail.MemorySender())
    rate_limit.by_ip.reset()
    rate_limit.by_email.reset()
    return create_app()


@pytest.fixture
def outbox(app):  # type: ignore[no-untyped-def]
    from academy.auth import email as mail

    return mail.get_sender().outbox  # type: ignore[attr-defined]


@pytest.fixture
def client(app):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="http://testserver") as c:
        yield c
