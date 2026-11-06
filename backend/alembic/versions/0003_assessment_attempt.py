"""Knowledge-check attempts (data-model §2.6).

Revision ID: 0003_assessment_attempt
Revises: 0002_content_view
"""

from alembic import op

revision = "0003_assessment_attempt"
down_revision = "0002_content_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE attempt_status AS ENUM ('in_progress', 'submitted');
        CREATE TABLE assessment_attempt (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            knowledge_check_id text NOT NULL,
            module_id text NOT NULL,
            content_version text NOT NULL,
            bundle_version text NOT NULL,
            status attempt_status NOT NULL DEFAULT 'in_progress',
            answers jsonb NOT NULL DEFAULT '{}'::jsonb,
            question_order jsonb NOT NULL,
            score numeric(4,3),
            passed boolean,
            per_objective jsonb,
            started_at timestamptz NOT NULL DEFAULT now(),
            submitted_at timestamptz,
            CONSTRAINT ck_assessment_attempt_score CHECK (score IS NULL OR (score >= 0 AND score <= 1))
        );
        CREATE INDEX ix_attempt_account_check ON assessment_attempt(account_id, knowledge_check_id);
        CREATE UNIQUE INDEX ux_attempt_one_in_progress
            ON assessment_attempt(account_id, knowledge_check_id) WHERE status = 'in_progress';
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE assessment_attempt; DROP TYPE attempt_status;")
