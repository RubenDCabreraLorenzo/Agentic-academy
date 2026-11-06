"""Hardened runner database functions, connected as ``academy_runner`` (T079, runner protocol §1)."""

from __future__ import annotations

import json
import uuid

import psycopg
import pytest
from sqlalchemy import create_engine, text


def _pg(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://")


@pytest.fixture
def admin(database_url: str):  # type: ignore[no-untyped-def]
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM submission_job; DELETE FROM challenge_submission; DELETE FROM runner_worker"))
    return engine


@pytest.fixture
def runner(database_url: str):  # type: ignore[no-untyped-def]
    host_part = _pg(database_url).split("@", 1)[1]
    conn = psycopg.connect(f"postgresql://academy_runner:runner@{host_part}", autocommit=True)
    yield conn
    conn.close()


def make_submission(admin, kind: str = "submission") -> uuid.UUID:  # type: ignore[no-untyped-def]
    sid = uuid.uuid4()
    with admin.begin() as conn:
        account = conn.execute(
            text("INSERT INTO account (id, email, password_hash, status) VALUES (:id, :e, 'x', 'active') RETURNING id"),
            {"id": uuid.uuid4(), "e": f"{uuid.uuid4().hex}@example.com"},
        ).scalar()
        conn.execute(
            text(
                "INSERT INTO challenge_submission (id, account_id, challenge_id, module_id, content_version, "
                "bundle_version, kind, files) VALUES (:id, :a, 'c', 'm', '1.0.0', 'b1', :k, '{\"a.py\": \"x\"}')"
            ),
            {"id": sid, "a": account, "k": kind},
        )
        conn.execute(text("INSERT INTO submission_job (submission_id, limits) VALUES (:id, '{\"wall_seconds\": 5}')"), {"id": sid})
    return sid


def claim(runner, worker: str = "w1"):  # type: ignore[no-untyped-def]
    return runner.execute("SELECT * FROM runner_claim_job(%s)", (worker,)).fetchone()


def complete(runner, sid, lease, result):  # type: ignore[no-untyped-def]
    return runner.execute("SELECT runner_complete_job(%s, %s, %s::jsonb)", (sid, lease, json.dumps(result))).fetchone()[0]


PASSED = {"status": "passed", "stop_reason": None, "criteria_results": [], "output_excerpt": "ok"}


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM challenge_submission",
        "SELECT * FROM account",
        "UPDATE challenge_submission SET status = 'passed'",
        "INSERT INTO runner_worker (worker_id, capacity) VALUES ('x', 1)",
        "DELETE FROM submission_job",
        "CREATE TABLE evil (id int)",
    ],
)
def test_no_direct_table_privileges(runner, sql: str) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        runner.execute(sql)


def test_public_and_api_role_cannot_execute(admin) -> None:  # type: ignore[no-untyped-def]
    with admin.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT p.proname, p.proacl::text, p.prosecdef, p.proconfig::text, pg_get_userbyid(p.proowner) "
                "FROM pg_proc p WHERE p.proname LIKE 'runner_%'"
            )
        ).all()
    assert {r[0] for r in rows} == {"runner_claim_job", "runner_complete_job", "runner_heartbeat"}
    for name, acl, secdef, config, owner in rows:
        assert secdef, name
        assert "search_path=pg_catalog, pg_temp" in config, name
        assert owner == "academy_runner_owner", name
        entries = acl.strip("{}").split(",")
        assert not any(e.startswith("=") for e in entries), f"{name} must not be executable by PUBLIC: {acl}"
        grantees = {e.split("=", 1)[0] for e in entries}
        assert grantees == {"academy_runner_owner", "academy_runner"}, f"{name}: unexpected grantees {grantees}"


@pytest.mark.parametrize(
    ("call", "args"),
    [
        ("SELECT * FROM runner_claim_job(%s)", ("bad worker!",)),
        ("SELECT * FROM runner_claim_job(%s)", (None,)),
        ("SELECT runner_heartbeat(%s, %s)", ("w1", 0)),
        ("SELECT runner_heartbeat(%s, %s)", ("w1", 99)),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), None, "{}")),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), str(uuid.uuid4()), '{"status": "hacked"}')),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), str(uuid.uuid4()), '{"status": "passed", "stop_reason": "timeout"}')),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), str(uuid.uuid4()), '{"status": "stopped"}')),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), str(uuid.uuid4()), '{"status": "passed", "criteria_results": {}}')),
        ("SELECT runner_complete_job(%s, %s, %s::jsonb)", (str(uuid.uuid4()), str(uuid.uuid4()), json.dumps({"status": "passed", "output_excerpt": "x" * 70000}))),
    ],
)
def test_invalid_parameters_rejected(runner, call: str, args: tuple) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(psycopg.errors.InvalidParameterValue):
        runner.execute(call, args)


def test_claim_returns_no_account_and_fences_completion(admin, runner) -> None:  # type: ignore[no-untyped-def]
    sid = make_submission(admin)
    job = claim(runner)
    cols = [d.name for d in runner.execute("SELECT * FROM runner_claim_job('w9')").description]
    assert "account_id" not in cols
    assert job[0] == sid and job[2] == "c" and job[5] == "submission"
    lease = job[1]
    assert claim(runner, "w2") is None, "a leased job is not claimable"
    assert complete(runner, sid, uuid.uuid4(), PASSED) is False, "wrong lease is rejected"
    with admin.begin() as conn:
        assert conn.execute(text("SELECT status FROM challenge_submission WHERE id = :id"), {"id": sid}).scalar() == "running"
    assert complete(runner, sid, lease, PASSED) is True
    with admin.begin() as conn:
        row = conn.execute(text("SELECT status, attempt_number FROM challenge_submission WHERE id = :id"), {"id": sid}).one()
    assert row == ("passed", 1)
    assert complete(runner, sid, lease, PASSED) is False, "completed jobs cannot be completed again"


def test_superseded_lease_is_fenced(admin, runner) -> None:  # type: ignore[no-untyped-def]
    sid = make_submission(admin)
    first = claim(runner, "w1")
    with admin.begin() as conn:
        conn.execute(text("UPDATE submission_job SET lease_expires_at = now() - interval '1 second'"))
    second = claim(runner, "w2")
    assert second is not None and second[1] != first[1]
    assert complete(runner, sid, first[1], PASSED) is False, "late result from the old lease is discarded"
    assert complete(runner, sid, second[1], {**PASSED, "status": "failed"}) is True


def test_error_requeues_then_final_without_attempt(admin, runner) -> None:  # type: ignore[no-untyped-def]
    sid = make_submission(admin)
    for attempt in range(1, 4):
        with admin.begin() as conn:
            conn.execute(text("UPDATE submission_job SET available_at = now() - interval '1 second'"))
        job = claim(runner)
        assert job is not None, f"attempt {attempt} should be claimable"
        assert complete(runner, sid, job[1], {"status": "error"}) is True
    with admin.begin() as conn:
        row = conn.execute(text("SELECT status, attempt_number FROM challenge_submission WHERE id = :id"), {"id": sid}).one()
        jobs = conn.execute(text("SELECT count(*) FROM submission_job")).scalar()
    assert row == ("error", None) and jobs == 0


def test_expired_lease_after_three_attempts_becomes_error(admin, runner) -> None:  # type: ignore[no-untyped-def]
    sid = make_submission(admin)
    claim(runner)
    with admin.begin() as conn:
        conn.execute(text("UPDATE submission_job SET infra_attempts = 3, lease_expires_at = now() - interval '1 second'"))
    assert claim(runner) is None
    with admin.begin() as conn:
        assert conn.execute(text("SELECT status FROM challenge_submission WHERE id = :id"), {"id": sid}).scalar() == "error"


def test_visible_runs_never_get_attempt_numbers(admin, runner) -> None:  # type: ignore[no-untyped-def]
    sid = make_submission(admin, kind="visible_run")
    job = claim(runner)
    assert complete(runner, sid, job[1], PASSED) is True
    with admin.begin() as conn:
        assert conn.execute(text("SELECT attempt_number FROM challenge_submission WHERE id = :id"), {"id": sid}).scalar() is None


def test_heartbeat_extends_only_own_leases(admin, runner) -> None:  # type: ignore[no-untyped-def]
    make_submission(admin)
    make_submission(admin)
    claim(runner, "w1")
    claim(runner, "w2")
    with admin.begin() as conn:
        conn.execute(text("UPDATE submission_job SET lease_expires_at = now() + interval '5 seconds'"))
    runner.execute("SELECT runner_heartbeat(%s, %s)", ("w1", 2))
    with admin.begin() as conn:
        rows = dict(conn.execute(text("SELECT worker_id, lease_expires_at > now() + interval '30 seconds' FROM submission_job")).all())
        workers = conn.execute(text("SELECT worker_id FROM runner_worker")).scalars().all()
    assert rows == {"w1": True, "w2": False}
    assert workers == ["w1"]
