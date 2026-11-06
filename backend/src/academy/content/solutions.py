"""Rule 7 execution checks: reference solutions pass, starter code fails (``--run-solutions``).

Solutions and tests are trusted maintainer code, so they run in a local subprocess, not in the
sandbox. The test layout mirrors the sandbox (runner protocol §2): learner files on the import
path, tests collected only from ``tests/`` with ``--import-mode=importlib``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from academy.content.loader import ContentTree, LoadedChallenge


def _write(base: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def run_tests(code: dict[str, str], tests: dict[str, str], timeout: int = 60) -> dict[str, bool]:
    """Run ``tests`` against ``code`` and return ``{test_id: passed}``."""
    with tempfile.TemporaryDirectory(prefix="academy-solution-") as tmp:
        work = Path(tmp)
        _write(work / "submission", code)
        _write(work / "tests", tests)
        report = work / "report.xml"
        test_files = sorted(
            str(work / "tests" / name)
            for name in tests
            if name.rsplit("/", 1)[-1].startswith("test_") and name.endswith(".py")
        )
        env = {**os.environ, "PYTHONPATH": str(work / "submission"), "PYTHONDONTWRITEBYTECODE": "1"}
        subprocess.run(  # noqa: S603 - trusted maintainer content, fixed argv
            [
                sys.executable,
                "-m",
                "pytest",
                *test_files,
                f"--rootdir={work / 'tests'}",
                "--import-mode=importlib",
                "-p",
                "no:cacheprovider",
                "-q",
                f"--junitxml={report}",
            ],
            cwd=work / "tests",
            env=env,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        results: dict[str, bool] = {}
        if not report.exists():
            return results
        for case in ET.parse(report).getroot().iter("testcase"):  # noqa: S314 - local file
            classname = case.get("classname", "")
            name = case.get("name", "")
            file = classname.replace(".", "/") + ".py" if classname else ""
            passed = not any(child.tag in {"failure", "error", "skipped"} for child in case)
            results[f"{file}::{name}"] = passed
        return results


def check_challenge(tree: ContentTree, ch: LoadedChallenge) -> None:
    rule = "7-challenge"
    expected = set(ch.test_ids)
    solved = run_tests(ch.solution, ch.tests)
    missing = expected - set(solved)
    if missing:
        tree.issue(rule, ch.path, f"tests not executed: {sorted(missing)}")
    failing = sorted(t for t, ok in solved.items() if not ok)
    if failing:
        tree.issue(rule, ch.path, f"reference solution fails tests: {failing}")
    starter = run_tests(ch.starter, ch.tests)
    mandatory_fails = [
        c.id
        for c in ch.meta.criteria
        if c.mandatory and not all(starter.get(t, False) for t in c.tests)
    ]
    if not mandatory_fails:
        tree.issue(rule, ch.path, "starter code must fail at least one mandatory criterion")


def check_solutions(tree: ContentTree) -> None:
    for ch in tree.challenges:
        if ch.solution and ch.tests:
            check_challenge(tree, ch)
