"""US5: laboratory scenarios are served to signed-in learners and never count as evidence."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.helpers import sign_up_and_in

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry

CONTENT = Path(__file__).resolve().parents[4] / "content"


@pytest.fixture(autouse=True)
def real_content(tmp_path: Path):  # type: ignore[no-untyped-def]
    build(load_tree(CONTENT), tmp_path)
    set_registry(Registry.load(tmp_path))
    yield
    set_registry(None)


def test_scenario_requires_account_and_is_served(client: TestClient, outbox: list) -> None:
    assert client.get("/api/v1/lab/scenarios/workflow-vs-agent-loop").status_code == 401
    sign_up_and_in(client, outbox)
    doc = client.get("/api/v1/lab/scenarios/workflow-vs-agent-loop", params={"variant": "agent-loop"}).json()
    assert {v["id"] for v in doc["variants"]} == {"fixed-workflow", "agent-loop"}
    assert doc["comparisons"][0]["left_variant"] == "fixed-workflow"
    assert client.get("/api/v1/lab/scenarios/nope").status_code == 404


def test_lab_visits_are_not_evidence(client: TestClient, outbox: list) -> None:
    sign_up_and_in(client, outbox)
    client.get("/api/v1/lab/scenarios/research-agent-with-tools")
    comps = client.get("/api/v1/me/competencies").json()
    assert all(c["status"] == "not_started" for c in comps)
