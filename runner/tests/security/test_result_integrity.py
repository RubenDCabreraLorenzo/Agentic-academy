"""Learner code manipulating ``/out/result.json`` (runner protocol §5, review D1).

Validation is an integrity check, not tamper-proof evaluation: case (e) documents the accepted
residual risk that a well-formed forged result for the learner's own submission is accepted.
"""

from __future__ import annotations

import textwrap

import pytest

from academy_runner.config import is_tmpfs
from tests.security.conftest import GOOD, run

FAIL = "def answer():\n    return 0\n"


def atexit_code(body: str, base: str = FAIL) -> dict[str, str]:
    return {"solution.py": "import atexit, json, os\n\n@atexit.register\ndef _tamper():\n" + textwrap.indent(textwrap.dedent(body), "    ") + "\n\n" + base}


def test_a_wrong_test_id_set_is_rejected(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, atexit_code("""
        with open("/out/result.json", "w") as fh:
            json.dump({"tests": [{"id": "test_solution.py::other", "outcome": "passed"}], "audit_events": []}, fh)
    """))
    assert result["status"] == "failed" and "integrity check failed" in result["output_excerpt"], result


def test_b_symlink_result_is_rejected(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, atexit_code("""
        os.remove("/out/result.json")
        os.symlink("/etc/passwd", "/out/result.json")
    """))
    assert result["status"] == "failed" and "regular file" in result["output_excerpt"], result


def test_c_oversized_result_is_rejected(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, atexit_code("""
        with open("/out/result.json", "w") as fh:
            fh.write(" " * (1024 * 1024 + 10))
    """))
    assert result["status"] == "failed" and "1 MB" in result["output_excerpt"], result


def test_d_filling_out_is_contained(sandbox) -> None:  # type: ignore[no-untyped-def]
    if not is_tmpfs(sandbox.s.runner_out_dir):
        pytest.skip("RUNNER_OUT_DIR is not a fixed-size tmpfs here; containment of /out size cannot be verified")
    result = run(sandbox, {"solution.py": textwrap.dedent("""
        try:
            with open("/out/fill.bin", "wb") as fh:
                for _ in range(1024):
                    fh.write(b"x" * 1024 * 1024)
        except OSError:
            pass
    """) + GOOD})
    assert result["status"] in {"passed", "failed", "stopped"}
    other = run(sandbox, {"solution.py": GOOD})
    assert other["status"] == "passed", "other jobs are unaffected"


def test_d2_out_access_is_reported_not_forbidden(sandbox) -> None:  # type: ignore[no-untyped-def]
    result = run(sandbox, {"solution.py": 'open("/out/note.txt", "w").write("hi")\n' + GOOD})
    assert result["status"] == "passed", result
    assert result.get("stop_reason") is None


def test_d1_accepted_residual_risk(sandbox) -> None:  # type: ignore[no-untyped-def]
    """(e) A well-formed forged result with the exact expected ids is ACCEPTED (review D1).

    This is not a security guarantee: it documents the accepted residual risk. The test only checks
    that the forgery affects the learner's own job: a different job evaluated afterwards gets its
    own, correct result. Database isolation between jobs is enforced by the lease-fenced runner
    functions (backend tests/integration/challenges/test_runner_functions.py).
    """
    forged = run(sandbox, atexit_code("""
        with open("/out/result.json", "w") as fh:
            json.dump({"tests": [{"id": "test_solution.py::test_runs", "outcome": "passed", "message": ""}],
                       "audit_events": []}, fh)
    """))
    assert forged["status"] == "passed", "D1: forgery of one's own result is not detectable"
    honest_failure = run(sandbox, {"solution.py": FAIL})
    assert honest_failure["status"] == "failed", "another job is not affected by the forgery"
