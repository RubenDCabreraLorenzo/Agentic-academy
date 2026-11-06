"""Validation rules 1–8 and 10 (contracts/content-schema.md). Each test breaks one rule."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from academy.content.solutions import check_solutions
from academy.content.validate import validate

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"
MODULE = Path("en/paths/mini-path/modules/01-intro")


@pytest.fixture
def tree_dir(tmp_path: Path) -> Path:
    target = tmp_path / "content"
    shutil.copytree(FIXTURE, target)
    return target


def edit_yaml(path: Path, change: Callable[[dict], None]) -> None:
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def rules(root: Path) -> set[str]:
    _tree, issues = validate(root)
    return {i.rule for i in issues}


def messages(root: Path) -> str:
    _tree, issues = validate(root)
    return "\n".join(f"{i.rule}: {i.message}" for i in issues)


def test_valid_fixture_has_no_issues(tree_dir: Path) -> None:
    assert messages(tree_dir) == ""


def test_rule1_schema_bad_semver(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "module.yaml", lambda d: d.update(version="1.0"))
    assert "1-schema" in rules(tree_dir)


def test_rule1_lang_mismatch(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "module.yaml", lambda d: d.update(lang="es"))
    assert "does not match folder" in messages(tree_dir)


def test_rule2_unknown_competency(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "module.yaml", lambda d: d["competencies"].append("nope"))
    assert "unknown competency 'nope'" in messages(tree_dir)


def test_rule2_lesson_anchor_must_resolve(tree_dir: Path) -> None:
    def change(d: dict) -> None:
        d["questions"][0]["lesson_anchor"] = "basics#missing"

    edit_yaml(tree_dir / MODULE / "knowledge-check.yaml", change)
    assert "lesson anchor 'basics#missing' not found" in messages(tree_dir)


def test_rule3_prerequisite_must_come_earlier(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "module.yaml", lambda d: d["prerequisites"].append("intro") if "prerequisites" in d else d.update(prerequisites=["intro"]))
    assert "3-prerequisites" in rules(tree_dir)


def test_rule3_path_cycle(tree_dir: Path) -> None:
    edit_yaml(tree_dir / "en/paths/mini-path/path.yaml", lambda d: d.update(prerequisite_paths=["mini-path"]))
    assert "path prerequisite cycle" in messages(tree_dir)


def test_rule4_single_agent_after_multi_agent(tree_dir: Path) -> None:
    second = tree_dir / "en/paths/mini-path/modules/02-second"
    shutil.copytree(tree_dir / MODULE, second)
    edit_yaml(tree_dir / MODULE / "module.yaml", lambda d: d.update(multi_agent=True))

    def change(d: dict) -> None:
        d.update(id="second", order=2, lab_scenarios=[])

    edit_yaml(second / "module.yaml", change)
    for f in (second / "lessons").glob("*.md"):
        f.write_text(f.read_text().replace("id: basics", "id: basics-two"))
    edit_yaml(second / "knowledge-check.yaml", lambda d: [d.update(id="second-check"), [q.update(lesson_anchor=q["lesson_anchor"].replace("basics", "basics-two")) for q in d["questions"]]])
    shutil.move(second / "challenges/hello-tool", second / "challenges/hello-two")
    edit_yaml(second / "challenges/hello-two/challenge.yaml", lambda d: d.update(id="hello-two", difficulty_rank=2))
    edit_yaml(tree_dir / "en/paths/mini-path/path.yaml", lambda d: d.update(modules=["intro", "second"]))
    assert "4-multi-agent" in rules(tree_dir)


def test_rule5_diagram_needs_alt(tree_dir: Path) -> None:
    lesson = tree_dir / MODULE / "lessons/01-basics.md"
    lesson.write_text(lesson.read_text().replace('alt="A loop from model to tool and back"', ""))
    assert "every diagram needs alt text" in messages(tree_dir)


def test_rule5_module_needs_challenge(tree_dir: Path) -> None:
    shutil.rmtree(tree_dir / MODULE / "challenges")
    assert "module needs at least one challenge" in messages(tree_dir)


def test_rule5_bad_maturity_level(tree_dir: Path) -> None:
    lesson = tree_dir / MODULE / "lessons/01-basics.md"
    lesson.write_text(lesson.read_text().replace('level="established"', 'level="hype"'))
    assert "maturity directive" in messages(tree_dir)


def test_rule5_knowledge_check_needs_five_questions(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "knowledge-check.yaml", lambda d: d.update(questions=d["questions"][:4]))
    assert "1-schema" in rules(tree_dir)


def test_rule6_objective_outside_module(tree_dir: Path) -> None:
    def change(d: dict) -> None:
        d["competencies"] = ["explain-agents"]

    edit_yaml(tree_dir / MODULE / "module.yaml", change)
    assert "6-traceability" in rules(tree_dir)


def test_rule7_unmapped_test(tree_dir: Path) -> None:
    tests = tree_dir / MODULE / "challenges/hello-tool/tests/test_agent.py"
    tests.write_text(tests.read_text() + "\n\ndef test_extra():\n    assert True\n")
    assert "is not mapped to any criterion" in messages(tree_dir)


def test_rule7_hints_minimum(tree_dir: Path) -> None:
    edit_yaml(tree_dir / MODULE / "challenges/hello-tool/challenge.yaml", lambda d: d.update(hints=["only one"]))
    assert "1-schema" in rules(tree_dir)


def test_rule7_hidden_tests_rejected(tree_dir: Path) -> None:
    (tree_dir / MODULE / "challenges/hello-tool/hidden").mkdir()
    assert "hidden tests are not supported" in messages(tree_dir)


def test_rule7_solution_passes_and_starter_fails(tree_dir: Path) -> None:
    tree, issues = validate(tree_dir)
    assert not issues
    check_solutions(tree)
    assert tree.issues == []


def test_rule7_broken_solution_is_reported(tree_dir: Path) -> None:
    sol = tree_dir / MODULE / "challenges/hello-tool/solution/agent.py"
    sol.write_text("def greet(name):\n    return 'nope'\n")
    tree, _ = validate(tree_dir)
    check_solutions(tree)
    assert any("reference solution fails" in i.message for i in tree.issues)


def test_rule8_destructive_without_approval(tree_dir: Path) -> None:
    f = tree_dir / "en/lab/demo-scenario.json"
    doc = json.loads(f.read_text())
    doc["variants"][0]["elements"][1] = {
        "id": "e2", "seq": 1, "kind": "tool_call", "tool": "delete_file", "arguments": {},
        "permission": "destructive", "approval": "not_required",
    }
    f.write_text(json.dumps(doc))
    assert "without a preceding approval_request" in messages(tree_dir)


def test_rule8_schema_violation(tree_dir: Path) -> None:
    f = tree_dir / "en/lab/demo-scenario.json"
    doc = json.loads(f.read_text())
    del doc["variants"][0]["recorded_with"]
    f.write_text(json.dumps(doc))
    assert "8-lab" in rules(tree_dir)


def test_rule10_secret_in_content(tree_dir: Path) -> None:
    lesson = tree_dir / MODULE / "lessons/01-basics.md"
    lesson.write_text(lesson.read_text() + "\nkey = sk-abcdefghijklmnopqrstuvwxyz123456\n")
    assert "10-secrets" in rules(tree_dir)
