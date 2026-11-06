"""Accounts, sessions and one-time tokens (data-model §2.1–2.3).

Revision ID: 0001_accounts
Revises:
"""

from alembic import op

revision = "0001_accounts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute(
        """
        CREATE TYPE account_status AS ENUM ('pending_verification', 'active', 'deleted');
        CREATE TABLE account (
            id uuid PRIMARY KEY,
            email citext NOT NULL UNIQUE,
            password_hash text NOT NULL,
            status account_status NOT NULL DEFAULT 'pending_verification',
            email_verified_at timestamptz,
            locale text NOT NULL DEFAULT 'en',
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE session (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            token_hash text NOT NULL UNIQUE,
            created_at timestamptz NOT NULL DEFAULT now(),
            last_seen_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz
        );
        CREATE INDEX ix_session_account ON session(account_id);
        CREATE TYPE token_purpose AS ENUM ('verify_email', 'reset_password');
        CREATE TABLE one_time_token (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            purpose token_purpose NOT NULL,
            token_hash text NOT NULL UNIQUE,
            expires_at timestamptz NOT NULL,
            used_at timestamptz
        );
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TABLE one_time_token; DROP TYPE token_purpose; DROP TABLE session; "
        "DROP TABLE account; DROP TYPE account_status;"
    )
