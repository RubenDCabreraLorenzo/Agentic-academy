"""US3: dashboard, competency view and path reset (FR-038–FR-043)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry
from tests.helpers import csrf, sign_up_and_in
from tests.integration.assessments.test_attempts import CORRECT

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"


@pytest.fixture(autouse=True)
def content(tmp_path: Path):  # type: ignore[no-untyped-def]
    build(load_tree(FIXTURE), tmp_path)
    set_registry(Registry.load(tmp_path))
    yield
    set_registry(None)


def pass_check(client: TestClient) -> None:
    a = client.post("/api/v1/knowledge-checks/intro-check/attempts", json={"attempt_id": str(uuid.uuid4())}, headers=csrf(client)).json()
    for qid, value in CORRECT.items():
        client.put(f"/api/v1/attempts/{a['attempt_id']}/answers/{qid}", json=value, headers=csrf(client))
    assert client.post(f"/api/v1/attempts/{a['attempt_id']}/submit", json={}, headers=csrf(client)).json()["passed"]


def pass_challenge(database_url: str, email: str) -> None:
    """Simulates a runner result for the learner's submission (the runner path is tested separately)."""
    engine = create_engine(database_url)
    with engine.begin() as conn:
        account = conn.execute(text("SELECT id FROM account WHERE email = :e"), {"e": email}).scalar()
        conn.execute(
            text(
                "INSERT INTO challenge_submission (id, account_id, challenge_id, module_id, content_version, bundle_version, "
                "kind, files, status, attempt_number, finished_at, criteria_results) VALUES (:id, :a, 'hello-tool', 'intro', "
                "'1.0.0', 'b', 'submission', '{}', 'passed', 1, now(), :cr)"
            ),
            {"id": uuid.uuid4(), "a": account, "cr": json.dumps([])},
        )


def test_new_learner_welcome(client: TestClient, outbox: list) -> None:
    sign_up_and_in(client, outbox)
    d = client.get("/api/v1/me/dashboard").json()
    assert d["new_learner"] is True and d["active_path"]["id"] == "mini-path"
    assert d["competencies_demonstrated"] == 0 and d["competencies_total"] == 2
    assert d["next_step"]["kind"] == "lesson" and d["continue"] is None


def test_progress_flow_and_completion(client: TestClient, outbox: list, database_url: str) -> None:
    email = sign_up_and_in(client, outbox)
    client.get("/api/v1/modules/intro", params={"lesson": "basics"})
    d = client.get("/api/v1/me/dashboard").json()
    assert d["modules"] == [{"id": "intro", "title": "Intro", "status": "in_progress"}]
    assert d["continue"] == {"module_id": "intro", "lesson_id": "basics"}
    assert d["next_step"]["kind"] == "knowledge_check"
    assert {o["id"] for o in d["pending_objectives"]} == {"obj-loop", "obj-tools"}

    pass_check(client)
    d = client.get("/api/v1/me/dashboard").json()
    assert d["pending_objectives"] == [] and d["next_step"] == {"kind": "challenge", "target_id": "hello-tool", "label": "Hello tool", "module_id": "intro"}
    assert d["competencies_demonstrated"] == 0, "a passed check alone never demonstrates a competency"

    pass_challenge(database_url, email)
    d = client.get("/api/v1/me/dashboard").json()
    assert d["modules"][0]["status"] == "completed" and d["path_completed"] is True
    assert d["competencies_demonstrated"] == 2
    assert {c["id"] for c in d["completion_summary"]["competencies"]} == {"explain-agents", "design-tools"}

    comps = client.get("/api/v1/me/competencies", params={"pathId": "mini-path"}).json()
    assert all(c["status"] == "demonstrated" for c in comps)
    evidence_types = {e["type"] for c in comps for e in c["evidence"]}
    assert evidence_types == {"knowledge_check", "challenge"}
    assert all(e["version"] == "1.0.0" for c in comps for e in c["evidence"])


def test_reset_requires_confirmation_and_is_scoped(client: TestClient, outbox: list, database_url: str) -> None:
    email = sign_up_and_in(client, outbox)
    client.get("/api/v1/modules/intro")
    pass_check(client)
    pass_challenge(database_url, email)
    bad = client.request("DELETE", "/api/v1/me/paths/mini-path/progress", json={"confirm": "yes"}, headers=csrf(client))
    assert bad.status_code == 400
    ok = client.request("DELETE", "/api/v1/me/paths/mini-path/progress", json={"confirm": "RESET"}, headers=csrf(client))
    assert ok.status_code == 204
    d = client.get("/api/v1/me/dashboard").json()
    assert d["competencies_demonstrated"] == 0 and d["modules"][0]["status"] == "not_started" and d["continue"] is None
    assert client.get("/api/v1/me").status_code == 200, "the account itself is untouched"
