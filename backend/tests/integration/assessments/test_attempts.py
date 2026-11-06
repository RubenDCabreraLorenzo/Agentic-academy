"""US2: knowledge-check attempts (FR-016–FR-019, FR-041, FR-051)."""

from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from tests.helpers import csrf, sign_up_and_in

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"
CORRECT = {
    "q1": {"selected": ["a"]},
    "q2": {"selected": ["a", "b"]},
    "q3": {"selected": ["model", "tool", "result"]},
    "q4": {"pairs": {"search": "read", "delete": "destructive"}},
    "q5": {"selected": ["approve"]},
}


@pytest.fixture
def bundles(tmp_path: Path) -> Path:
    out = tmp_path / "bundles"
    build(load_tree(FIXTURE), out, now=datetime(2026, 1, 1, tzinfo=UTC))
    set_registry(Registry.load(out))
    yield out
    set_registry(None)


def start(client: TestClient) -> dict:
    r = client.post("/api/v1/knowledge-checks/intro-check/attempts", json={"attempt_id": str(uuid.uuid4())}, headers=csrf(client))
    assert r.status_code == 201, r.text
    return r.json()


def answer(client: TestClient, attempt_id: str, qid: str, value: dict) -> dict:
    r = client.put(f"/api/v1/attempts/{attempt_id}/answers/{qid}", json=value, headers=csrf(client))
    assert r.status_code == 200, r.text
    return r.json()


def submit(client: TestClient, attempt_id: str, confirm: bool = False):
    return client.post(f"/api/v1/attempts/{attempt_id}/submit", json={"confirm_unanswered": confirm}, headers=csrf(client))


def test_attempt_shape_hides_answers(client: TestClient, outbox: list, bundles: Path) -> None:
    sign_up_and_in(client, outbox)
    attempt = start(client)
    assert attempt["pass_threshold"] == 0.7 and len(attempt["questions"]) == 5
    assert set(attempt["objectives"]) == {"Explain the agent loop", "Design a tool"}
    text = str(attempt["questions"])
    assert "correct" not in text and "explanation" not in text and "pairs" not in text
    again = start(client)
    assert again["attempt_id"] == attempt["attempt_id"], "an in-progress attempt is resumed"


def test_feedback_lock_and_pass(client: TestClient, outbox: list, bundles: Path) -> None:
    sign_up_and_in(client, outbox)
    attempt = start(client)
    fb = answer(client, attempt["attempt_id"], "q1", {"selected": ["b"]})
    assert fb["correct"] is False and fb["explanation_markdown"]
    assert fb["lesson_link"] == {"module_id": "intro", "lesson_id": "basics", "anchor": "agent-loop"}
    locked = client.put(f"/api/v1/attempts/{attempt['attempt_id']}/answers/q1", json={"selected": ["a"]}, headers=csrf(client))
    assert locked.status_code == 409 and locked.json()["code"] == "already_answered"
    for qid in ("q2", "q3", "q4", "q5"):
        assert answer(client, attempt["attempt_id"], qid, CORRECT[qid])["correct"] is True
    result = submit(client, attempt["attempt_id"]).json()
    assert result["score"] == 0.8 and result["passed"] is True and result["best_score"] == 0.8
    assert result["objectives_demonstrated"] == ["obj-loop", "obj-tools"]
    assert result["competencies_demonstrated"] == [], "competencies also need the module challenge (FR-036)"
    again = submit(client, attempt["attempt_id"])
    assert again.status_code == 200 and again.json()["score"] == 0.8, "submit is idempotent"


def test_unanswered_requires_confirmation_and_weak_objectives(client: TestClient, outbox: list, bundles: Path) -> None:
    sign_up_and_in(client, outbox)
    attempt = start(client)
    answer(client, attempt["attempt_id"], "q1", CORRECT["q1"])
    r = submit(client, attempt["attempt_id"])
    assert r.status_code == 422 and r.json()["code"] == "unanswered_questions"
    result = submit(client, attempt["attempt_id"], confirm=True).json()
    assert result["passed"] is False and result["score"] == 0.2
    assert {w["id"] for w in result["weak_objectives"]} == {"obj-loop", "obj-tools"}
    assert all(w["lesson_link"]["lesson_id"] == "basics" for w in result["weak_objectives"])
    # retry keeps the best result
    retry = start(client)
    assert retry["attempt_id"] != attempt["attempt_id"]
    for qid, value in CORRECT.items():
        answer(client, retry["attempt_id"], qid, value)
    best = submit(client, retry["attempt_id"]).json()
    assert best["score"] == 1.0 and best["best_score"] == 1.0
    history = client.get("/api/v1/knowledge-checks/intro-check/attempts/history").json()
    assert [h["score"] for h in history] == [1.0, 0.2]
    assert history[1]["questions"][0]["question_id"]


def test_attempt_scored_with_its_own_version(client: TestClient, outbox: list, bundles: Path, tmp_path: Path) -> None:
    sign_up_and_in(client, outbox)
    attempt = start(client)
    # Publish a new bundle where q1's correct answer changes; the running attempt keeps version 1.
    content = tmp_path / "content"
    shutil.copytree(FIXTURE, content)
    kc_file = content / "en/paths/mini-path/modules/01-intro/knowledge-check.yaml"
    kc = yaml.safe_load(kc_file.read_text())
    kc["version"] = "2.0.0"
    kc["questions"][0]["correct"] = ["b"]
    kc_file.write_text(yaml.safe_dump(kc))
    build(load_tree(content), bundles, now=datetime(2026, 2, 1, tzinfo=UTC))
    set_registry(Registry.load(bundles))
    assert answer(client, attempt["attempt_id"], "q1", {"selected": ["a"]})["correct"] is True
    for qid in ("q2", "q3", "q4", "q5"):
        answer(client, attempt["attempt_id"], qid, CORRECT[qid])
    assert submit(client, attempt["attempt_id"]).json()["score"] == 1.0


def test_other_learners_cannot_touch_attempt(client: TestClient, outbox: list, bundles: Path) -> None:
    sign_up_and_in(client, outbox)
    attempt = start(client)
    client.cookies.clear()
    sign_up_and_in(client, outbox)
    r = client.put(f"/api/v1/attempts/{attempt['attempt_id']}/answers/q1", json={"selected": ["a"]}, headers=csrf(client))
    assert r.status_code == 404
