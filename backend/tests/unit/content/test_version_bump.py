"""Rule 9: content changed without a version bump relative to the latest bundle (FR-048–FR-050)."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import yaml

from academy.content.build import build
from academy.content.loader import load_tree
from academy.content.validate import validate_tree
from academy.content.versioning import check_version_bumps

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "content"
KC = Path("en/paths/mini-path/modules/01-intro/knowledge-check.yaml")


def setup(tmp_path: Path) -> tuple[Path, Path]:
    content = tmp_path / "content"
    shutil.copytree(FIXTURE, content)
    bundles = tmp_path / "bundles"
    build(load_tree(content), bundles, now=datetime(2026, 1, 1, tzinfo=UTC))
    return content, bundles


def change_question(content: Path, bump: bool) -> None:
    data = yaml.safe_load((content / KC).read_text())
    data["questions"][0]["prompt"] = "A reworded question?"
    if bump:
        data["version"] = "1.1.0"
    (content / KC).write_text(yaml.safe_dump(data))


def issues(content: Path, bundles: Path) -> list[str]:
    tree = load_tree(content)
    validate_tree(tree)
    check_version_bumps(tree, bundles)
    return [f"{i.rule}: {i.message}" for i in tree.issues]


def test_unchanged_content_passes(tmp_path: Path) -> None:
    content, bundles = setup(tmp_path)
    assert issues(content, bundles) == []


def test_change_without_bump_is_rejected(tmp_path: Path) -> None:
    content, bundles = setup(tmp_path)
    change_question(content, bump=False)
    found = issues(content, bundles)
    assert any(m.startswith("9-version") and "intro-check" in m for m in found), found


def test_change_with_bump_is_accepted(tmp_path: Path) -> None:
    content, bundles = setup(tmp_path)
    change_question(content, bump=True)
    assert issues(content, bundles) == []


def test_review_date_alone_needs_no_bump(tmp_path: Path) -> None:
    content, bundles = setup(tmp_path)
    data = yaml.safe_load((content / KC).read_text())
    data["last_reviewed"] = "2026-12-01"
    (content / KC).write_text(yaml.safe_dump(data))
    assert issues(content, bundles) == []
