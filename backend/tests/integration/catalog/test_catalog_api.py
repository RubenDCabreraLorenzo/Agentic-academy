"""US6: public catalog and roadmap built from the real curriculum (FR-001, FR-002)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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


def test_catalog_is_public_and_ordered(client: TestClient) -> None:
    r = client.get("/api/v1/catalog")
    assert r.status_code == 200
    paths = r.json()
    orders = [p["order"] for p in paths]
    assert orders == sorted(orders)
    first = paths[0]
    assert first["id"] == "foundations-of-agentic-ai-engineering" and first["status"] == "available"
    assert {p["status"] for p in paths[1:]} == {"planned"}
    titles = " ".join(p["title"] for p in paths)
    for topic in ("orchestration", "Multi-agent", "MCP", "RAG", "evaluation", "Security", "Production"):
        assert topic.lower() in titles.lower()
    for p in paths:
        assert p["level"] in {"foundational", "intermediate", "advanced"}
        assert p["competencies"], "every path lists its competencies"


def test_planned_path_detail_has_no_modules(client: TestClient) -> None:
    r = client.get("/api/v1/paths/multi-agent-architectures")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "planned" and body["modules"] == []
    assert body["prerequisite_paths"] == ["agent-orchestration-and-workflows"]
