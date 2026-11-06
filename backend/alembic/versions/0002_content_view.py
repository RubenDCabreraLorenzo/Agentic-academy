"""Content views (data-model §2.4). LastPosition is derived from the latest view (§2.5).

Revision ID: 0002_content_view
Revises: 0001_accounts
"""

from alembic import op

revision = "0002_content_view"
down_revision = "0001_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE content_type AS ENUM ('module', 'lesson');
        CREATE TABLE content_view (
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            content_type content_type NOT NULL,
            content_id text NOT NULL,
            content_version text NOT NULL,
            path_id text NOT NULL,
            module_id text NOT NULL,
            first_viewed_at timestamptz NOT NULL DEFAULT now(),
            last_viewed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (account_id, content_type, content_id)
        );
        CREATE INDEX ix_content_view_recent ON content_view(account_id, last_viewed_at DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE content_view; DROP TYPE content_type;")
