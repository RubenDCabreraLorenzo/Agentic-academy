"""US1: path overview and module content (FR-001, FR-006, FR-007, FR-015, FR-045)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.helpers import sign_up_and_in

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.registry import Registry, set_registry

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"


@pytest.fixture(autouse=True)
def fixture_content(tmp_path: Path):  # type: ignore[no-untyped-def]
    build(load_tree(FIXTURE), tmp_path)
    set_registry(Registry.load(tmp_path))
    yield
    set_registry(None)


def test_path_is_public_without_learner_status(client: TestClient) -> None:
    r = client.get("/api/v1/paths/mini-path")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Mini path" and body["level"] == "foundational"
    assert body["objectives"] and body["entry_prerequisites"]
    assert body["modules"][0]["id"] == "intro" and "status" not in body["modules"][0]


def test_unknown_path_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/paths/nope").json()["code"] == "not_found"


def test_module_requires_account(client: TestClient) -> None:
    r = client.get("/api/v1/modules/intro")
    assert r.status_code == 401 and r.json()["code"] == "unauthenticated"


def test_module_content_and_view_recorded(client: TestClient, outbox: list) -> None:
    sign_up_and_in(client, outbox)
    r = client.get("/api/v1/modules/intro", params={"lesson": "basics"})
    assert r.status_code == 200
    m = r.json()
    assert m["objectives"][0]["statement"]
    assert m["lessons"][0]["body_markdown"].lstrip().startswith("## The agent loop")
    assert m["references"][0]["url"].startswith("https://")
    assert m["knowledge_check_id"] == "intro-check" and m["challenge_ids"] == ["hello-tool"]
    assert m["previous_module_id"] is None and m["next_module_id"] is None
    assert m["missing_prerequisites"] == []
    assert m["status"] == "in_progress"  # viewed, nothing demonstrated
    path = client.get("/api/v1/paths/mini-path").json()
    assert path["modules"][0]["status"] == "in_progress"


def test_missing_prerequisites_are_reported_not_blocking(client: TestClient, outbox: list, tmp_path: Path) -> None:
    import shutil

    import yaml

    content = tmp_path / "content"
    shutil.copytree(FIXTURE, content)
    second = content / "en/paths/mini-path/modules/02-second"
    shutil.copytree(content / "en/paths/mini-path/modules/01-intro", second)
    data = yaml.safe_load((second / "module.yaml").read_text())
    data.update(id="second", order=2, prerequisites=["intro"], lab_scenarios=[])
    (second / "module.yaml").write_text(yaml.safe_dump(data))
    for f in (second / "lessons").glob("*.md"):
        f.write_text(f.read_text().replace("id: basics", "id: basics-two"))
    kc = yaml.safe_load((second / "knowledge-check.yaml").read_text())
    kc["id"] = "second-check"
    for q in kc["questions"]:
        q["lesson_anchor"] = q["lesson_anchor"].replace("basics", "basics-two")
    (second / "knowledge-check.yaml").write_text(yaml.safe_dump(kc))
    shutil.move(second / "challenges/hello-tool", second / "challenges/hello-two")
    ch = yaml.safe_load((second / "challenges/hello-two/challenge.yaml").read_text())
    ch.update(id="hello-two", difficulty_rank=2)
    (second / "challenges/hello-two/challenge.yaml").write_text(yaml.safe_dump(ch))
    pdata = yaml.safe_load((content / "en/paths/mini-path/path.yaml").read_text())
    pdata["modules"] = ["intro", "second"]
    (content / "en/paths/mini-path/path.yaml").write_text(yaml.safe_dump(pdata))
    out = tmp_path / "bundles"
    tree = load_tree(content)
    build(tree, out)
    set_registry(Registry.load(out))

    sign_up_and_in(client, outbox)
    r = client.get("/api/v1/modules/second")
    assert r.status_code == 200
    m = r.json()
    assert m["missing_prerequisites"] == [{"id": "intro", "title": "Intro", "taught_in_module": "intro"}]
    assert m["previous_module_id"] == "intro"
