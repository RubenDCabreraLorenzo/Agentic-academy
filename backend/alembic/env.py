"""Alembic environment: migrations run against DATABASE_URL (or -x url=...)."""

import os

from alembic import context
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine

from academy.config import get_settings

config = context.config


class _MigrationSecrets(BaseSettings):
    """Values only migrations need, kept out of the API's ``Settings``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runner_db_password: str = ""


# Migrations read this from the process environment, but in development it is defined in ``.env``,
# the same source as DATABASE_URL. A real environment variable still takes precedence.
_runner_db_password = _MigrationSecrets().runner_db_password
if _runner_db_password:
    os.environ["RUNNER_DB_PASSWORD"] = _runner_db_password


def run_migrations_online() -> None:
    url = context.get_x_argument(as_dictionary=True).get("url") or get_settings().database_url
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
