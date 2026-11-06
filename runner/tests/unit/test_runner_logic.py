"""Runner logic without Docker: files, results, criteria mapping, scrubbing, fencing (T074)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest

from academy_runner.config import Settings
from academy_runner.files import InvalidFilesError, validate_files
from academy_runner.results import (
    IntegrityError,
    map_criteria,
    read_result_file,
    scrub,
    validate_result,
)
from academy_runner.sandbox import Job
from academy_runner.worker import Worker

TESTS = {"test_triage.py": "def test_a(): pass\n"}
CHALLENGE = {
    "id": "c",
    "test_ids": ["test_triage.py::test_a", "test_triage.py::test_b"],
    "tests": TESTS,
    "criteria": [
        {"id": "one", "description": "A", "mandatory": True, "tests": ["test_triage.py::test_a"], "feedback": "fix a"},
        {"id": "two", "description": "B", "mandatory": False, "tests": ["test_triage.py::test_b"], "feedback": "fix b"},
    ],
}


@pytest.mark.parametrize(
    "name",
    ["/abs.py", "../up.py", "a/../b.py", "tests/x.py", "manifest.json", "conftest.py", "pkg/conftest.py",
     "sitecustomize.py", "usercustomize.py", "pytest.py", "pytest/__init__.py", "_pytest/x.py",
     "academy_sim.py", "academy_sim/core.py", "evil.pth", "test_triage.py", "a\\b.py", "./x.py"],
)
def test_reserved_or_unsafe_files_rejected(name: str) -> None:
    with pytest.raises(InvalidFilesError):
        validate_files({name: "x = 1"}, TESTS)


def test_valid_files_and_learner_tests_allowed() -> None:
    files = {"triage.py": "x = 1", "pkg/util.py": "y = 2", "test_mine.py": "def test_x(): pass"}
    assert validate_files(files, TESTS) == files


def test_size_limit() -> None:
    with pytest.raises(InvalidFilesError):
        validate_files({"big.py": "x" * 300_000}, TESTS)


def write(out: Path, data: object) -> None:
    (out / "result.json").write_text(json.dumps(data))


def good_result() -> dict:
    return {"tests": [{"id": i, "outcome": "passed", "message": ""} for i in CHALLENGE["test_ids"]], "audit_events": []}


def test_read_result_rejects_missing_symlink_large_and_malformed(tmp_path: Path) -> None:
    with pytest.raises(IntegrityError, match="no result"):
        read_result_file(tmp_path)
    target = tmp_path / "elsewhere.json"
    target.write_text("{}")
    os.symlink(target, tmp_path / "result.json")
    with pytest.raises(IntegrityError, match="regular file"):
        read_result_file(tmp_path)
    (tmp_path / "result.json").unlink()
    (tmp_path / "result.json").mkdir()
    with pytest.raises(IntegrityError):
        read_result_file(tmp_path)
    (tmp_path / "result.json").rmdir()
    (tmp_path / "result.json").write_text("x" * (1024 * 1024 + 1))
    with pytest.raises(IntegrityError, match="1 MB"):
        read_result_file(tmp_path)
    (tmp_path / "result.json").write_text("{not json")
    with pytest.raises(IntegrityError, match="JSON"):
        read_result_file(tmp_path)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["tests"].pop(),
        lambda d: d["tests"].append({"id": "test_triage.py::extra", "outcome": "passed"}),
        lambda d: d["tests"].append(dict(d["tests"][0])),
        lambda d: d["tests"][0].update(outcome="great"),
        lambda d: d.update(tests="all good"),
    ],
)
def test_validate_result_integrity(mutate) -> None:  # type: ignore[no-untyped-def]
    data = good_result()
    mutate(data)
    with pytest.raises(IntegrityError):
        validate_result(data, CHALLENGE["test_ids"], 0)


def test_exit_status_must_be_consistent() -> None:
    with pytest.raises(IntegrityError, match="exit status"):
        validate_result(good_result(), CHALLENGE["test_ids"], 1)


def test_forged_exact_result_is_accepted_d1() -> None:
    """Documents D1: a well-formed result with the exact expected ids cannot be told apart."""
    tests = validate_result(good_result(), CHALLENGE["test_ids"], 0)
    assert all(t["outcome"] == "passed" for t in tests.values())


def test_map_criteria_mandatory_and_optional() -> None:
    tests = {
        "test_triage.py::test_a": {"id": "test_triage.py::test_a", "outcome": "passed", "message": ""},
        "test_triage.py::test_b": {"id": "test_triage.py::test_b", "outcome": "failed", "message": "E assert 1 == 2"},
    }
    criteria, passed = map_criteria(CHALLENGE, tests)
    assert passed is True, "only mandatory criteria decide"
    assert criteria[0]["met"] and criteria[0]["feedback_markdown"] is None
    assert not criteria[1]["met"] and criteria[1]["feedback_markdown"] == "fix b"
    tests["test_triage.py::test_a"]["outcome"] = "error"
    assert map_criteria(CHALLENGE, tests)[1] is False


def test_scrub_secrets_and_dsn() -> None:
    text = "key=sk-abcdefghijklmnopqrstuvwxyz token: abc postgresql://u:p@h/db mail me@example.com"
    out = scrub(text)
    for secret in ("sk-abcdefghijklmnopqrstuvwxyz", "postgresql://u:p@h/db", "me@example.com", "token: abc"):
        assert secret not in out


class FakeDb:
    def __init__(self, accept: bool) -> None:
        self.accept = accept
        self.completed: list[dict] = []

    def complete(self, job, result):  # type: ignore[no-untyped-def]
        self.completed.append(result)
        return self.accept


class FakeSandbox:
    def __init__(self, result=None, exc=None) -> None:  # type: ignore[no-untyped-def]
        self.result, self.exc = result, exc

    def run(self, job, challenge):  # type: ignore[no-untyped-def]
        if self.exc:
            raise self.exc
        return self.result


def make_worker(tmp_path: Path, db: FakeDb, sandbox: FakeSandbox) -> Worker:
    bundle = {"bundle_version": "b1", "challenges": {"c": CHALLENGE}}
    (tmp_path / "en").mkdir()
    (tmp_path / "en" / "bundle-b1.json").write_text(json.dumps(bundle))
    settings = Settings(content_dir=tmp_path, runner_out_dir=tmp_path / "out")
    return Worker(settings, db=db, sandbox=sandbox)  # type: ignore[arg-type]


def job(bundle: str = "b1") -> Job:
    return Job(uuid.uuid4(), uuid.uuid4(), "c", "1.0.0", bundle, "submission", {"triage.py": "x"}, {})


def test_late_result_is_discarded_without_crash(tmp_path: Path) -> None:
    db = FakeDb(accept=False)
    worker = make_worker(tmp_path, db, FakeSandbox(result={"status": "passed"}))
    worker._slots.acquire()
    worker.process(job())
    assert db.completed == [{"status": "passed"}]


def test_infra_errors_are_reported_as_error(tmp_path: Path) -> None:
    from academy_runner.sandbox import InfraError

    db = FakeDb(accept=True)
    worker = make_worker(tmp_path, db, FakeSandbox(exc=InfraError("docker down")))
    worker._slots.acquire()
    worker.process(job())
    worker._slots.acquire()
    worker.process(job(bundle="missing"))
    assert db.completed == [{"status": "error"}, {"status": "error"}]


def test_settings_guards(tmp_path: Path) -> None:
    from academy_runner.config import ProductionGuardError

    with pytest.raises(ProductionGuardError):
        Settings(app_env="production", runner_runtime="runc", runner_out_dir=tmp_path).enforce_guards()
    with pytest.raises(ValueError):
        Settings(runner_worker_id="bad id!").enforce_guards()
    Settings(app_env="development", runner_runtime="runc", runner_out_dir=tmp_path).enforce_guards()
