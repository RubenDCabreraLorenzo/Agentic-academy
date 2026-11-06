from __future__ import annotations

import json
from pathlib import Path

from academy.content.build import build
from academy.content.loader import load_tree, parse_test_ids
from academy.content.registry import Registry

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"
CONTRACT = Path(__file__).resolve().parents[4] / "specs/001-agentic-academy-mvp/contracts/lab-trace.schema.json"
PACKAGED = Path(__file__).resolve().parents[3] / "src/academy/content/lab_trace.schema.json"


def test_loader_extracts_lesson_structure() -> None:
    tree = load_tree(FIXTURE)
    assert tree.issues == []
    (module,) = tree.modules
    (lesson,) = module.lessons
    assert lesson.anchors == {"agent-loop", "tools"}
    assert [b.language for b in lesson.code_blocks] == ["python"]
    assert lesson.diagrams == [{"kind": "mermaid", "alt": "A loop from model to tool and back"}]
    assert ("maturity", {"level": "established"}) in lesson.directives
    assert module.challenges[0].test_ids == ["test_agent.py::test_greets"]


def test_parse_test_ids_ignores_non_test_files() -> None:
    files = {"test_a.py": "def test_x():\n  pass\ndef helper():\n  pass\n", "util.py": "def test_y(): pass"}
    assert parse_test_ids(files) == ["test_a.py::test_x"]


def test_build_never_includes_solutions_and_is_immutable(tmp_path: Path) -> None:
    tree = load_tree(FIXTURE)
    path, created = build(tree, tmp_path)
    assert created
    data = json.loads(path.read_text())
    challenge = data["challenges"]["hello-tool"]
    assert "solution" not in json.dumps(challenge).lower().replace("reference_explanation", "")
    assert challenge["tests"] and challenge["starter_files"]
    again, created_again = build(tree, tmp_path)
    assert again == path and not created_again


def test_registry_resolves_versions(tmp_path: Path) -> None:
    tree = load_tree(FIXTURE)
    path, _ = build(tree, tmp_path)
    reg = Registry.load(tmp_path)
    current = reg.current("en")
    assert current.version == json.loads(path.read_text())["bundle_version"]
    assert reg.get(current.version).module("intro") is not None


def test_packaged_lab_schema_matches_contract() -> None:
    assert json.loads(PACKAGED.read_text()) == json.loads(CONTRACT.read_text())
