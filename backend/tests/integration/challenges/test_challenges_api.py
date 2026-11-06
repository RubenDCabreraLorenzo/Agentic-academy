"""US4: challenge API (FR-021–FR-024, FR-022c, FR-045b; runner protocol §1)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from tests.helpers import csrf, sign_up_and_in

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"
GOOD = {"agent.py": 'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n'}


@pytest.fixture
def challenges_on(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, database_url: str):  # type: ignore[no-untyped-def]
    from academy.config import get_settings

    monkeypatch.setenv("CHALLENGES_ENABLED", "true")
    get_settings.cache_clear()
    build(load_tree(FIXTURE), tmp_path)
    set_registry(Registry.load(tmp_path))
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM runner_worker"))
    yield engine
    set_registry(None)
    get_settings.cache_clear()


def heartbeat(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO runner_worker (worker_id, capacity) VALUES ('w1', 2) ON CONFLICT (worker_id) DO UPDATE SET last_heartbeat_at = now()"))


def post_submission(client: TestClient, files: dict, kind: str = "submission", sid: str | None = None):
    return client.post(
        "/api/v1/challenges/hello-tool/submissions",
        json={"submission_id": sid or str(uuid.uuid4()), "kind": kind, "files": files},
        headers=csrf(client),
    )


def test_detail_hides_reference_until_passed(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    d = client.get("/api/v1/challenges/hello-tool").json()
    assert d["title"] == "Hello tool" and d["criteria"][0]["mandatory"] is True
    assert d["files"] == d["starter_files"] and "test_agent.py" in d["tests"]
    assert d["reference_explanation_markdown"] is None and d["hints_revealed"] == [] and d["hints_total"] == 2
    assert "solution" not in str(d).lower().replace("reference_explanation", "")


def test_workspace_autosave_and_size_limit(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    r = client.put("/api/v1/challenges/hello-tool/workspace", json={"agent.py": "x = 1\n"}, headers=csrf(client))
    assert r.status_code == 204
    assert client.get("/api/v1/challenges/hello-tool").json()["files"] == {"agent.py": "x = 1\n"}
    big = client.put("/api/v1/challenges/hello-tool/workspace", json={"agent.py": "x" * 300_000}, headers=csrf(client))
    assert big.status_code == 413
    bad = client.put("/api/v1/challenges/hello-tool/workspace", json={"tests/test_agent.py": "x"}, headers=csrf(client))
    assert bad.status_code == 400 and bad.json()["code"] == "invalid_submission_files"


@pytest.mark.parametrize(
    "name", ["conftest.py", "sitecustomize.py", "pytest.py", "academy_sim.py", "x.pth", "test_agent.py", "../x.py", "/abs.py", "manifest.json"]
)
def test_reserved_files_rejected(client: TestClient, outbox: list, challenges_on, name: str) -> None:
    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    r = post_submission(client, {**GOOD, name: "x = 1\n"})
    assert r.status_code == 400 and r.json()["code"] == "invalid_submission_files"


def test_hints_progressive_then_exhausted(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    first = client.post("/api/v1/challenges/hello-tool/hints", headers=csrf(client)).json()
    assert first == {"index": 1, "total": 2, "markdown": "Look at the return value."}
    assert client.post("/api/v1/challenges/hello-tool/hints", headers=csrf(client)).json()["index"] == 2
    r = client.post("/api/v1/challenges/hello-tool/hints", headers=csrf(client))
    assert r.status_code == 409 and r.json()["code"] == "no_more_hints"
    assert len(client.get("/api/v1/challenges/hello-tool").json()["hints_revealed"]) == 2


def test_unavailable_without_heartbeat_keeps_code(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    r = post_submission(client, GOOD)
    assert r.status_code == 503 and r.json()["code"] == "evaluation_unavailable"
    assert client.get("/api/v1/challenges/hello-tool").json()["files"] == GOOD


def test_disabled_flag_refuses(client: TestClient, outbox: list, challenges_on, monkeypatch: pytest.MonkeyPatch) -> None:
    from academy.config import get_settings

    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    monkeypatch.setenv("CHALLENGES_ENABLED", "false")
    get_settings.cache_clear()
    assert post_submission(client, GOOD).status_code == 503


def test_queue_idempotency_concurrency_and_position(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    sid = str(uuid.uuid4())
    r = post_submission(client, GOOD, sid=sid)
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "queued" and body["queue_position"] >= 1 and body["delayed"] is False
    again = post_submission(client, GOOD, sid=sid)
    assert again.status_code == 202 and again.json()["submission_id"] == sid
    busy = post_submission(client, GOOD)
    assert busy.status_code == 429 and busy.json()["code"] == "run_in_progress"
    listed = client.get("/api/v1/challenges/hello-tool/submissions").json()
    assert [s["submission_id"] for s in listed] == [sid]
    got = client.get(f"/api/v1/submissions/{sid}").json()
    assert got["status"] == "queued" and got["attempt_number"] is None


def test_delayed_flag(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    sid = post_submission(client, GOOD).json()["submission_id"]
    with challenges_on.begin() as conn:
        conn.execute(text("UPDATE challenge_submission SET queued_at = now() - interval '6 minutes' WHERE id = :id"), {"id": sid})
    assert client.get(f"/api/v1/submissions/{sid}").json()["delayed"] is True


def test_account_deletion_cancels_jobs(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    sid = post_submission(client, GOOD).json()["submission_id"]
    assert client.request("DELETE", "/api/v1/me", json={"confirm": "DELETE"}, headers=csrf(client)).status_code == 204
    with challenges_on.begin() as conn:
        assert conn.execute(text("SELECT count(*) FROM challenge_submission WHERE id = :id"), {"id": sid}).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM submission_job WHERE submission_id = :id"), {"id": sid}).scalar() == 0


def test_other_learner_cannot_read_submission(client: TestClient, outbox: list, challenges_on) -> None:
    sign_up_and_in(client, outbox)
    heartbeat(challenges_on)
    sid = post_submission(client, GOOD).json()["submission_id"]
    client.cookies.clear()
    sign_up_and_in(client, outbox)
    assert client.get(f"/api/v1/submissions/{sid}").status_code == 404
