"""Result validation and mapping (runner protocol §5).

Everything read from the sandbox is untrusted input: the result file is written by a process that
also runs learner code. Validation rejects malformed or inconsistent results but cannot detect a
forged result that reports the exact expected test ids as passed (accepted residual risk, D1).
"""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from academy_runner.config import RESULT_LIMIT_BYTES

OUTCOMES = {"passed", "failed", "error", "skipped"}
MAX_MESSAGE = 2000

_SECRETS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[email]"),
    (
        re.compile(
            r"(?i)(password|passwd|secret|token|api[_-]?key|authorization)(\"?\s*[:=]\s*\"?)([^\s\",;]+)"
        ),
        r"\1\2[redacted]",
    ),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [redacted]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[redacted-key]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[redacted-key]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[redacted-key]"),
    (re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^\s]+"), "[redacted-dsn]"),
]


def scrub(text: str) -> str:
    for pattern, repl in _SECRETS:
        text = pattern.sub(repl, text)
    return text


class IntegrityError(ValueError):
    """The sandbox result is missing, malformed or inconsistent."""


def read_result_file(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "result.json"
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError as exc:
        raise IntegrityError("no result file") from exc
    except OSError as exc:  # ELOOP for symlinks
        raise IntegrityError("result file is not a regular file") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise IntegrityError("result file is not a regular file")
        if info.st_size > RESULT_LIMIT_BYTES:
            raise IntegrityError("result file larger than 1 MB")
        raw = os.read(fd, RESULT_LIMIT_BYTES + 1)
    finally:
        os.close(fd)
    if len(raw) > RESULT_LIMIT_BYTES:
        raise IntegrityError("result file larger than 1 MB")
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise IntegrityError("result file is not valid JSON") from exc
    if not isinstance(data, dict):
        raise IntegrityError("result must be a JSON object")
    return data


def validate_result(
    data: dict[str, Any], expected_ids: list[str], exit_code: int
) -> dict[str, dict[str, str]]:
    tests = data.get("tests")
    if not isinstance(tests, list):
        raise IntegrityError("result has no test list")
    seen: dict[str, dict[str, str]] = {}
    for t in tests:
        if (
            not isinstance(t, dict)
            or not isinstance(t.get("id"), str)
            or t.get("outcome") not in OUTCOMES
        ):
            raise IntegrityError("malformed test entry")
        if t["id"] in seen:
            raise IntegrityError(f"duplicated test id {t['id']}")
        msg = t.get("message", "")
        seen[t["id"]] = {
            "id": t["id"],
            "outcome": t["outcome"],
            "message": msg if isinstance(msg, str) else "",
        }
    if set(seen) != set(expected_ids):
        raise IntegrityError("test ids do not match the expected set")
    audit = data.get("audit_events", [])
    if not isinstance(audit, list):
        raise IntegrityError("malformed audit events")
    if exit_code != 0 and all(t["outcome"] == "passed" for t in seen.values()):
        raise IntegrityError("exit status inconsistent with reported outcomes")
    return seen


def forbidden_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        e
        for e in data.get("audit_events", [])
        if isinstance(e, dict) and e.get("kind") == "forbidden_operation"
    ]


def out_access_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        e
        for e in data.get("audit_events", [])
        if isinstance(e, dict) and e.get("kind") == "out_access"
    ]


def map_criteria(
    challenge: dict[str, Any], tests: dict[str, dict[str, str]]
) -> tuple[list[dict[str, Any]], bool]:
    """Returns (criteria_results, passed). ``met`` ⇔ all its tests passed."""
    results = []
    passed = True
    for c in challenge["criteria"]:
        entries = [
            {
                "id": tid,
                "title": tid.split("::", 1)[-1],
                "outcome": tests[tid]["outcome"],
                "message": scrub(tests[tid]["message"])[:MAX_MESSAGE] or None,
            }
            for tid in c["tests"]
        ]
        met = all(e["outcome"] == "passed" for e in entries)
        if c["mandatory"] and not met:
            passed = False
        results.append(
            {
                "criterion_id": c["id"],
                "description": c["description"],
                "mandatory": c["mandatory"],
                "met": met,
                "feedback_markdown": None if met else c["feedback"],
                "tests": entries,
            }
        )
    return results, passed


def integrity_failure(challenge: dict[str, Any], reason: str) -> dict[str, Any]:
    criteria = [
        {
            "criterion_id": c["id"],
            "description": c["description"],
            "mandatory": c["mandatory"],
            "met": False,
            "feedback_markdown": f"Test harness integrity check failed: {reason}.",
            "tests": [],
        }
        for c in challenge["criteria"]
    ]
    return {
        "status": "failed",
        "stop_reason": None,
        "criteria_results": criteria,
        "output_excerpt": f"Test harness integrity check failed: {reason}.",
    }
