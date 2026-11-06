"""Malicious submissions must be contained (FR-022a, SC-011, runner protocol §2–§4)."""

from __future__ import annotations

import hashlib
import json
import textwrap

from tests.security.conftest import DEFAULT_TEST, GOOD, challenge, run


def code(body: str) -> dict[str, str]:
    return {"solution.py": textwrap.dedent(body) + "\n" + GOOD}


def test_correct_submission_passes(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, {"solution.py": GOOD})
    assert result["status"] == "passed", result


def test_network_access_is_stopped(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import socket
        try:
            socket.create_connection(("1.1.1.1", 80), timeout=2)
        except Exception:
            pass
    """))
    assert result["status"] == "stopped" and result["stop_reason"] == "forbidden_operation", result


def test_process_spawning_is_stopped(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import subprocess
        try:
            subprocess.run(["id"])
        except Exception:
            pass
    """))
    assert result["stop_reason"] == "forbidden_operation", result


def test_fork_bomb_is_contained(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import os
        for _ in range(1000):
            try:
                os.fork()
            except Exception:
                break
    """))
    assert result["status"] == "stopped", result


def test_infinite_loop_times_out(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("while True:\n    pass"), challenge(wall=3))
    assert result["status"] == "stopped" and result["stop_reason"] == "timeout", result


def test_memory_exhaustion_is_stopped(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("blob = bytearray(1024 * 1024 * 1024)"))
    assert result["status"] in {"stopped", "failed"}, result
    assert result["status"] != "passed"
    if result["status"] == "stopped":
        assert result["stop_reason"] == "memory"


def test_huge_output_is_stopped(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import sys
        for _ in range(20000):
            sys.stdout.write("x" * 512 + "\\n")
        sys.stdout.flush()
    """))
    assert result["status"] == "stopped" and result["stop_reason"] == "output_limit", result
    assert len(result["output_excerpt"]) <= 64 * 1024 + 200


def test_writing_to_work_fails(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        try:
            with open("/work/tests/test_solution.py", "w") as fh:
                fh.write("def test_runs():\\n    pass\\n")
        except OSError:
            pass
    """))
    assert result["status"] != "passed" or result["criteria_results"][0]["met"], result
    assert result["status"] in {"stopped", "passed"}


def test_environment_has_no_secrets(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import os
        print("ENV-DUMP", sorted(os.environ))
    """))
    out = result["output_excerpt"]
    for leaked in ("RUNNER_DATABASE_URL", "DATABASE_URL", "SESSION_SECRET", "SMTP", "academy_runner:"):
        assert leaked not in out, out


def test_filesystem_contains_no_solution_or_other_jobs(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, code("""
        import os
        found = []
        for root, dirs, files in os.walk("/"):
            if root.startswith(("/proc", "/sys", "/usr", "/dev")):
                dirs[:] = []
                continue
            for f in files:
                found.append(os.path.join(root, f))
        print("WORK", sorted(p for p in found if p.startswith("/work")))
        print("SOLUTIONS", [p for p in found if "solution/" in p or "reference" in p])
    """))
    out = result["output_excerpt"]
    work_line = next(line for line in out.splitlines() if line.startswith("WORK"))
    assert work_line == "WORK ['/work/manifest.json', '/work/submission/solution.py', '/work/tests/test_solution.py']", work_line
    assert "SOLUTIONS []" in out


def test_forged_stdout_result_is_ignored(sandbox) -> None:  # type: ignore[no-untyped-def]
    fake = json.dumps({"tests": [{"id": "test_solution.py::test_runs", "outcome": "passed", "message": ""}]})
    result = run(sandbox, {"solution.py": f"print({fake!r})\ndef answer():\n    return 0\n"})
    assert result["status"] == "failed", result


def test_replacing_tests_in_submission_is_rejected(sandbox) -> None:  # type: ignore[no-untyped-def]
    for name in ("tests/test_solution.py", "manifest.json", "conftest.py", "sitecustomize.py", "test_solution.py"):
        result = run(sandbox, {"solution.py": GOOD, name: "def test_runs():\n    pass\n"})
        assert result["status"] == "failed" and "Invalid submission files" in result["output_excerpt"], (name, result)


def test_learner_test_files_are_not_collected(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, {"solution.py": GOOD, "test_mine.py": "def test_x():\n    assert False\n"})
    assert result["status"] == "passed", result


def test_executed_tests_match_the_bundle(sandbox) -> None:  # type: ignore[no-untyped-def]
    expected = hashlib.sha256(DEFAULT_TEST.encode()).hexdigest()
    result = run(sandbox, code("""
        import hashlib
        print("TESTHASH", hashlib.sha256(open("/work/tests/test_solution.py", "rb").read()).hexdigest())
    """))
    assert f"TESTHASH {expected}" in result["output_excerpt"], result
