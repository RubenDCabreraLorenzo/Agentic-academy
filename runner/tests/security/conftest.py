"""Sandbox security suite fixtures.

The suite is only meaningful under gVisor (``RUNNER_RUNTIME=runsc``). For local development on
machines without gVisor it can be exercised under ``runc`` with ``ALLOW_RUNC_SECURITY_TESTS=1``;
results obtained that way are NOT valid security evidence (runner protocol §8.6).
"""

from __future__ import annotations

import os
import textwrap
import uuid
from pathlib import Path
from typing import Any

import pytest

from academy_runner.config import Settings
from academy_runner.sandbox import Job, Sandbox

RUNTIME = os.environ.get("RUNNER_RUNTIME", "runsc")
IMAGE = os.environ.get("RUNNER_SANDBOX_IMAGE", "academy-sandbox:dev")


def _docker_ready() -> str | None:
    try:
        import docker

        client = docker.from_env()
        client.ping()
        client.images.get(IMAGE)
        if RUNTIME not in client.info().get("Runtimes", {}):
            return f"Docker runtime {RUNTIME} is not installed"
    except Exception as exc:
        return f"Docker or image {IMAGE} unavailable: {type(exc).__name__}"
    return None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    reason = _docker_ready()
    if reason is None and RUNTIME != "runsc" and os.environ.get("ALLOW_RUNC_SECURITY_TESTS") != "1":
        reason = "security suite requires RUNNER_RUNTIME=runsc (set ALLOW_RUNC_SECURITY_TESTS=1 to exercise it under runc; not valid evidence)"
    if reason:
        for item in items:
            item.add_marker(pytest.mark.skip(reason=reason))


def pytest_report_header(config: pytest.Config) -> str:
    note = "" if RUNTIME == "runsc" else "  (NOT valid security evidence: development exception)"
    return f"sandbox runtime: {RUNTIME}{note}"


DEFAULT_TEST = textwrap.dedent(
    """
    import solution

    def test_runs():
        assert solution.answer() == 42
    """
)


def challenge(tests: dict[str, str] | None = None, wall: int = 5) -> dict[str, Any]:
    tests = tests or {"test_solution.py": DEFAULT_TEST}
    from tests.security.academy_runner_test_ids import ids_for

    ids = ids_for(tests)
    return {
        "id": "security-probe",
        "tests": tests,
        "test_ids": ids,
        "limits": {"wall_seconds": wall},
        "criteria": [{"id": "all", "description": "All tests", "mandatory": True, "tests": ids, "feedback": "f"}],
    }


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    settings = Settings(
        runner_runtime=RUNTIME,  # type: ignore[arg-type]
        runner_sandbox_image=IMAGE,
        runner_out_dir=Path(os.environ.get("RUNNER_OUT_DIR", str(tmp_path / "out"))),
        runner_worker_id="security-suite",
    )
    return Sandbox(settings)


def run(sandbox: Sandbox, files: dict[str, str], ch: dict[str, Any] | None = None) -> dict[str, Any]:
    ch = ch or challenge()
    job = Job(uuid.uuid4(), uuid.uuid4(), ch["id"], "1.0.0", "b", "submission", files, ch["limits"])
    return sandbox.run(job, ch)


GOOD = "def answer():\n    return 42\n"
