"""Laboratory visits (data-model §2.11): exploration only, never evidence.

Revision ID: 0005_lab_visit
Revises: 0004_challenges
"""

from alembic import op

revision = "0005_lab_visit"
down_revision = "0004_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE lab_visit (
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            scenario_id text NOT NULL,
            variant_id text NOT NULL,
            first_viewed_at timestamptz NOT NULL DEFAULT now(),
            last_viewed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (account_id, scenario_id, variant_id)
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE lab_visit;")
