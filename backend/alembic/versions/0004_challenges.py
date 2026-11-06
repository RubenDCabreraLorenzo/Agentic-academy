"""Challenges, submissions, job queue and hardened runner functions (data-model §2.7–2.10,
runner protocol §1).

Security model of this migration:

- ``academy_runner`` is the login role used by the runner host. It has NO table, sequence or schema
  ``CREATE`` privileges; it may only execute the three functions below.
- The functions are ``SECURITY DEFINER`` and owned by ``academy_runner_owner``, a NOLOGIN,
  non-superuser role holding only the table privileges the functions need.
- Every function pins ``search_path = pg_catalog, pg_temp`` and schema-qualifies every object, so a
  caller cannot shadow tables, types or operators.
- ``EXECUTE`` is revoked from ``PUBLIC`` (also for future functions in the schema) and granted only
  to ``academy_runner``.
- Worker ids are self-asserted by the shared runner role. That is acceptable because the runner host
  is trusted-but-exposed (runner protocol §0): a compromised host can already act as any worker.
  Fencing by ``lease_id`` still prevents stale results from overwriting newer ones.

Revision ID: 0004_challenges
Revises: 0003_assessment_attempt
"""

import os

from alembic import op

revision = "0004_challenges"
down_revision = "0003_assessment_attempt"
branch_labels = None
depends_on = None


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE challenge_workspace (
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            challenge_id text NOT NULL,
            files jsonb NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (account_id, challenge_id),
            CONSTRAINT ck_challenge_workspace_size CHECK (octet_length(files::text) <= 262144)
        );

        CREATE TABLE hint_usage (
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            challenge_id text NOT NULL,
            hints_revealed integer NOT NULL DEFAULT 0 CHECK (hints_revealed >= 0),
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (account_id, challenge_id)
        );

        CREATE TYPE submission_kind AS ENUM ('visible_run', 'submission');
        CREATE TYPE submission_status AS ENUM
            ('queued', 'running', 'passed', 'failed', 'stopped', 'error', 'cancelled');
        CREATE TYPE stop_reason AS ENUM ('timeout', 'memory', 'output_limit', 'forbidden_operation');

        CREATE TABLE challenge_submission (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
            challenge_id text NOT NULL,
            module_id text NOT NULL,
            content_version text NOT NULL,
            bundle_version text NOT NULL,
            kind submission_kind NOT NULL,
            attempt_number integer,
            files jsonb NOT NULL,
            status submission_status NOT NULL DEFAULT 'queued',
            stop_reason stop_reason,
            criteria_results jsonb,
            output_excerpt text,
            hints_used integer NOT NULL DEFAULT 0,
            queued_at timestamptz NOT NULL DEFAULT now(),
            started_at timestamptz,
            finished_at timestamptz,
            CONSTRAINT ck_challenge_submission_files CHECK (octet_length(files::text) <= 262144),
            CONSTRAINT ck_challenge_submission_output CHECK (output_excerpt IS NULL OR length(output_excerpt) <= 65536),
            CONSTRAINT ck_challenge_submission_stop CHECK ((stop_reason IS NULL) OR (status = 'stopped'))
        );
        CREATE INDEX ix_submission_account_challenge ON challenge_submission(account_id, challenge_id);

        CREATE TABLE submission_job (
            submission_id uuid PRIMARY KEY REFERENCES challenge_submission(id) ON DELETE CASCADE,
            available_at timestamptz NOT NULL DEFAULT now(),
            worker_id text,
            lease_id uuid,
            lease_expires_at timestamptz,
            infra_attempts integer NOT NULL DEFAULT 0,
            limits jsonb NOT NULL
        );
        CREATE INDEX ix_submission_job_available ON submission_job(available_at);

        CREATE TABLE runner_worker (
            worker_id text PRIMARY KEY,
            capacity integer NOT NULL,
            started_at timestamptz NOT NULL DEFAULT now(),
            last_heartbeat_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )

    # Roles (cluster-wide; created only if missing).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'academy_runner_owner') THEN
                CREATE ROLE academy_runner_owner NOLOGIN NOINHERIT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'academy_runner') THEN
                CREATE ROLE academy_runner NOLOGIN NOINHERIT;
            END IF;
        END $$;
        """
    )
    password = os.environ.get("RUNNER_DB_PASSWORD")
    if password:
        op.execute(f"ALTER ROLE academy_runner LOGIN PASSWORD {_quote_literal(password)}")

    op.execute(
        """
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM academy_runner;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM academy_runner;
        REVOKE CREATE ON SCHEMA public FROM PUBLIC;
        GRANT USAGE ON SCHEMA public TO academy_runner, academy_runner_owner;
        GRANT SELECT, UPDATE, DELETE ON public.submission_job TO academy_runner_owner;
        GRANT SELECT, UPDATE ON public.challenge_submission TO academy_runner_owner;
        GRANT SELECT, INSERT, UPDATE ON public.runner_worker TO academy_runner_owner;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
        """
    )

    op.execute(
        r"""
        CREATE FUNCTION public.runner_claim_job(p_worker_id text)
        RETURNS TABLE (
            submission_id uuid, lease_id uuid, challenge_id text, content_version text,
            bundle_version text, kind text, files jsonb, limits jsonb
        )
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $fn$
        DECLARE
            v_job public.submission_job%ROWTYPE;
            v_lease uuid := pg_catalog.gen_random_uuid();
        BEGIN
            IF p_worker_id IS NULL OR p_worker_id !~ '^[A-Za-z0-9_-]{1,64}$' THEN
                RAISE EXCEPTION 'invalid worker_id' USING ERRCODE = '22023';
            END IF;

            -- Jobs whose lease expired after 3 infrastructure attempts end as error (not counted).
            UPDATE public.challenge_submission s
               SET status = 'error', finished_at = pg_catalog.now()
              FROM public.submission_job j
             WHERE j.submission_id = s.id
               AND s.status = 'running'
               AND j.lease_expires_at < pg_catalog.now()
               AND j.infra_attempts >= 3;
            DELETE FROM public.submission_job j
             USING public.challenge_submission s
             WHERE j.submission_id = s.id AND s.status = 'error';

            SELECT j.* INTO v_job
              FROM public.submission_job j
              JOIN public.challenge_submission s ON s.id = j.submission_id
             WHERE j.available_at <= pg_catalog.now()
               AND j.infra_attempts < 3
               AND (s.status = 'queued'
                    OR (s.status = 'running' AND j.lease_expires_at < pg_catalog.now()))
             ORDER BY j.available_at, j.submission_id
             LIMIT 1
             FOR UPDATE OF j SKIP LOCKED;

            IF NOT FOUND THEN
                RETURN;
            END IF;

            UPDATE public.submission_job
               SET worker_id = p_worker_id,
                   lease_id = v_lease,
                   lease_expires_at = pg_catalog.now() + interval '60 seconds',
                   infra_attempts = public.submission_job.infra_attempts + 1
             WHERE public.submission_job.submission_id = v_job.submission_id;

            UPDATE public.challenge_submission
               SET status = 'running', started_at = pg_catalog.now()
             WHERE id = v_job.submission_id;

            RETURN QUERY
                SELECT s.id, v_lease, s.challenge_id, s.content_version, s.bundle_version,
                       s.kind::text, s.files, v_job.limits
                  FROM public.challenge_submission s
                 WHERE s.id = v_job.submission_id;
        END
        $fn$;

        CREATE FUNCTION public.runner_complete_job(p_submission_id uuid, p_lease_id uuid, p_result jsonb)
        RETURNS boolean
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $fn$
        DECLARE
            v_job public.submission_job%ROWTYPE;
            v_sub public.challenge_submission%ROWTYPE;
            v_status text;
            v_reason text;
            v_output text;
            v_attempt integer;
        BEGIN
            IF p_submission_id IS NULL OR p_lease_id IS NULL OR p_result IS NULL THEN
                RAISE EXCEPTION 'submission_id, lease_id and result are required' USING ERRCODE = '22023';
            END IF;
            IF pg_catalog.jsonb_typeof(p_result) <> 'object'
               OR pg_catalog.octet_length(p_result::text) > 1048576 THEN
                RAISE EXCEPTION 'result must be a JSON object of at most 1 MB' USING ERRCODE = '22023';
            END IF;
            v_status := p_result->>'status';
            v_reason := p_result->>'stop_reason';
            IF v_status IS NULL OR v_status NOT IN ('passed', 'failed', 'stopped', 'error') THEN
                RAISE EXCEPTION 'invalid status' USING ERRCODE = '22023';
            END IF;
            IF v_reason IS NOT NULL AND (v_status <> 'stopped'
               OR v_reason NOT IN ('timeout', 'memory', 'output_limit', 'forbidden_operation')) THEN
                RAISE EXCEPTION 'invalid stop_reason' USING ERRCODE = '22023';
            END IF;
            IF v_status = 'stopped' AND v_reason IS NULL THEN
                RAISE EXCEPTION 'stopped requires a stop_reason' USING ERRCODE = '22023';
            END IF;
            IF p_result ? 'criteria_results'
               AND pg_catalog.jsonb_typeof(p_result->'criteria_results') <> 'array' THEN
                RAISE EXCEPTION 'criteria_results must be an array' USING ERRCODE = '22023';
            END IF;
            v_output := p_result->>'output_excerpt';
            IF v_output IS NOT NULL AND pg_catalog.length(v_output) > 65536 THEN
                RAISE EXCEPTION 'output_excerpt longer than 64 KB' USING ERRCODE = '22023';
            END IF;

            -- Lease fencing: only the current lease holder may complete the job.
            SELECT * INTO v_job FROM public.submission_job
             WHERE submission_id = p_submission_id AND lease_id = p_lease_id
             FOR UPDATE;
            IF NOT FOUND THEN
                RETURN false;
            END IF;
            SELECT * INTO v_sub FROM public.challenge_submission WHERE id = p_submission_id FOR UPDATE;
            IF v_sub.status <> 'running' THEN
                RETURN false;
            END IF;

            IF v_status = 'error' THEN
                IF v_job.infra_attempts < 3 THEN
                    -- Infrastructure failure: re-queue without counting an attempt.
                    UPDATE public.submission_job
                       SET worker_id = NULL, lease_id = NULL, lease_expires_at = NULL,
                           available_at = pg_catalog.now() + interval '5 seconds'
                     WHERE submission_id = p_submission_id;
                    UPDATE public.challenge_submission SET status = 'queued', started_at = NULL
                     WHERE id = p_submission_id;
                    RETURN true;
                END IF;
                UPDATE public.challenge_submission
                   SET status = 'error', finished_at = pg_catalog.now()
                 WHERE id = p_submission_id;
                DELETE FROM public.submission_job WHERE submission_id = p_submission_id;
                RETURN true;
            END IF;

            IF v_sub.kind = 'submission' THEN
                SELECT COALESCE(MAX(attempt_number), 0) + 1 INTO v_attempt
                  FROM public.challenge_submission
                 WHERE account_id = v_sub.account_id AND challenge_id = v_sub.challenge_id
                   AND kind = 'submission' AND attempt_number IS NOT NULL;
            END IF;

            UPDATE public.challenge_submission
               SET status = v_status::public.submission_status,
                   stop_reason = v_reason::public.stop_reason,
                   criteria_results = COALESCE(p_result->'criteria_results', '[]'::jsonb),
                   output_excerpt = v_output,
                   attempt_number = v_attempt,
                   finished_at = pg_catalog.now()
             WHERE id = p_submission_id;
            DELETE FROM public.submission_job WHERE submission_id = p_submission_id;
            RETURN true;
        END
        $fn$;

        CREATE FUNCTION public.runner_heartbeat(p_worker_id text, p_capacity integer)
        RETURNS void
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $fn$
        BEGIN
            IF p_worker_id IS NULL OR p_worker_id !~ '^[A-Za-z0-9_-]{1,64}$' THEN
                RAISE EXCEPTION 'invalid worker_id' USING ERRCODE = '22023';
            END IF;
            IF p_capacity IS NULL OR p_capacity < 1 OR p_capacity > 16 THEN
                RAISE EXCEPTION 'capacity must be between 1 and 16' USING ERRCODE = '22023';
            END IF;
            INSERT INTO public.runner_worker (worker_id, capacity, last_heartbeat_at)
            VALUES (p_worker_id, p_capacity, pg_catalog.now())
            ON CONFLICT (worker_id)
            DO UPDATE SET capacity = EXCLUDED.capacity, last_heartbeat_at = pg_catalog.now();
            -- Extend only live leases held by this worker.
            UPDATE public.submission_job
               SET lease_expires_at = pg_catalog.now() + interval '60 seconds'
             WHERE worker_id = p_worker_id AND lease_expires_at > pg_catalog.now();
        END
        $fn$;

        ALTER FUNCTION public.runner_claim_job(text) OWNER TO academy_runner_owner;
        ALTER FUNCTION public.runner_complete_job(uuid, uuid, jsonb) OWNER TO academy_runner_owner;
        ALTER FUNCTION public.runner_heartbeat(text, integer) OWNER TO academy_runner_owner;
        REVOKE ALL ON FUNCTION public.runner_claim_job(text) FROM PUBLIC;
        REVOKE ALL ON FUNCTION public.runner_complete_job(uuid, uuid, jsonb) FROM PUBLIC;
        REVOKE ALL ON FUNCTION public.runner_heartbeat(text, integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.runner_claim_job(text) TO academy_runner;
        GRANT EXECUTE ON FUNCTION public.runner_complete_job(uuid, uuid, jsonb) TO academy_runner;
        GRANT EXECUTE ON FUNCTION public.runner_heartbeat(text, integer) TO academy_runner;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS public.runner_heartbeat(text, integer);
        DROP FUNCTION IF EXISTS public.runner_complete_job(uuid, uuid, jsonb);
        DROP FUNCTION IF EXISTS public.runner_claim_job(text);
        DROP TABLE runner_worker; DROP TABLE submission_job; DROP TABLE challenge_submission;
        DROP TYPE stop_reason; DROP TYPE submission_status; DROP TYPE submission_kind;
        DROP TABLE hint_usage; DROP TABLE challenge_workspace;
        """
    )
