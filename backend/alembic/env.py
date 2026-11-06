"""Alembic environment: migrations run against DATABASE_URL (or -x url=...)."""

from alembic import context
from sqlalchemy import create_engine

from academy.config import get_settings

config = context.config


def run_migrations_online() -> None:
    url = context.get_x_argument(as_dictionary=True).get("url") or get_settings().database_url
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
