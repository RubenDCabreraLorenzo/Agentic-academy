"""In-sandbox test harness: ``python -m academy_sim.run /work /out`` (runner protocol §2–§5).

Trust note (review D1): learner code is imported by the tests and runs in this same process, as
the same user, so it can tamper with this harness and can write or overwrite ``/out/result.json``.
This harness therefore only enables *integrity checks* performed by the runner (exact test-id
set, regular file, size, exit status); it does NOT provide tamper-proof evaluation. Isolation from
the network, other learners and secrets is enforced by the sandbox, not by this file.

Audit hooks (``sys.addaudithook``, which cannot be removed) are installed before any learner code
is imported. They *report* attempts to open sockets, spawn processes or touch sensitive paths as
``forbidden_operation`` events, and record learner access to the permitted output location
``/out`` as separate ``out_access`` events. ``/out`` access is informational: it never fails a
submission by itself, and learner code can suppress or forge these events (D1).
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

MAX_MESSAGE = 2000

NETWORK_EVENTS = {
    "socket.connect",
    "socket.bind",
    "socket.sendto",
    "socket.sendmsg",
    "socket.getaddrinfo",
}
PROCESS_EVENTS = {
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.posix_spawn",
    "os.spawn",
    "os.fork",
    "os.forkpty",
}
SENSITIVE_ROOTS = (
    "/proc",
    "/sys",
    "/root",
    "/home",
    "/var",
    "/run",
    "/boot",
    "/srv",
    "/mnt",
    "/opt",
)
SENSITIVE_ETC_ALLOWED = ("/etc/localtime", "/etc/timezone", "/etc/mime.types")
WRITABLE_ROOTS = ("/tmp", "/out")
#: Standard devices used by Python and pytest themselves.
DEVICES = (
    "/dev/null",
    "/dev/zero",
    "/dev/urandom",
    "/dev/random",
    "/dev/stdout",
    "/dev/stderr",
    "/dev/tty",
)


class _State:
    harness_writing = False
    out_dir = "/out"
    forbidden: Counter[tuple[str, str]] = Counter()
    out_access: Counter[tuple[str, str]] = Counter()


def _under(path: str, roots: tuple[str, ...]) -> bool:
    return any(path == r or path.startswith(r + "/") for r in roots)


def _write_mode(mode: Any, flags: Any) -> bool:
    if isinstance(mode, str) and any(c in mode for c in "wax+"):
        return True
    if isinstance(flags, int):
        return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
    return False


def _classify_path(event: str, path: str, write: bool) -> None:
    path = os.path.abspath(path)
    if path in DEVICES:
        return
    if _under(path, (_State.out_dir,)):
        if not _State.harness_writing:
            _State.out_access[(event if not write else f"{event}:write", path)] += 1
        return
    if write and not _under(path, WRITABLE_ROOTS):
        _State.forbidden[(f"{event}:write-outside-tmp", path)] += 1
        return
    if _under(path, SENSITIVE_ROOTS) or (
        path.startswith("/etc/") and not _under(path, SENSITIVE_ETC_ALLOWED)
    ):
        _State.forbidden[(f"{event}:sensitive-path", path)] += 1


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if event in NETWORK_EVENTS or event in PROCESS_EVENTS:
        _State.forbidden[(event, "")] += 1
        raise PermissionError(f"{event} is not allowed in the sandbox")
    if event == "open" and args:
        target = args[0]
        if isinstance(target, bytes):
            target = os.fsdecode(target)
        if isinstance(target, str):
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else None
            _classify_path("open", target, _write_mode(mode, flags))
    elif (
        event in {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate"}
        and args
    ):
        target = args[0]
        if isinstance(target, bytes):
            target = os.fsdecode(target)
        if isinstance(target, str):
            _classify_path(event, target, True)


def _base_id(nodeid: str) -> str:
    return nodeid.split("[", 1)[0]


class _Collector:
    """pytest plugin recording one outcome per test id (parametrized cases aggregated)."""

    RANK = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}

    def __init__(self) -> None:
        self.results: dict[str, dict[str, str]] = {}

    def _record(self, nodeid: str, outcome: str, message: str) -> None:
        tid = _base_id(nodeid)
        prev = self.results.get(tid)
        if prev is None or self.RANK[outcome] > self.RANK[prev["outcome"]]:
            self.results[tid] = {"id": tid, "outcome": outcome, "message": message[:MAX_MESSAGE]}

    def pytest_runtest_logreport(self, report: Any) -> None:
        if report.passed:
            if report.when == "call":
                self._record(report.nodeid, "passed", "")
            return
        if report.skipped:
            self._record(report.nodeid, "skipped", "skipped")
            return
        outcome = "failed" if report.when == "call" else "error"
        message = getattr(report, "longreprtext", "") or str(report.longrepr)
        lines = [ln for ln in message.splitlines() if ln.startswith("E ")]
        self._record(report.nodeid, outcome, "\n".join(lines) or message[-MAX_MESSAGE:])

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            message = getattr(report, "longreprtext", "") or str(report.longrepr)
            self._record(f"{report.nodeid}::<collection>", "error", message[-MAX_MESSAGE:])


def run(work: Path, out: Path) -> int:
    started = time.monotonic()
    _State.out_dir = str(out)
    manifest = json.loads((work / "manifest.json").read_text())
    sys.addaudithook(_audit)  # before any learner code is imported; cannot be removed
    sys.path.insert(0, str(work / "submission"))
    os.chdir("/tmp" if Path("/tmp").is_dir() else str(work))
    import pytest

    collector = _Collector()
    test_files = [str(work / "tests" / name) for name in manifest["test_files"]]
    pytest.main(
        [
            *test_files,
            f"--rootdir={work / 'tests'}",
            "--import-mode=importlib",
            "-p",
            "no:cacheprovider",
            "-q",
            "--no-header",
            # Learner output goes to the container's stdout: it is shown to the learner (truncated,
            # scrubbed) and counts towards the 64 KB output limit.
            "--capture=no",
        ],
        plugins=[collector],
    )
    # Files that failed to import report collection errors for every expected test of that file.
    for tid in manifest["expected_test_ids"]:
        if tid not in collector.results:
            file = tid.split("::", 1)[0]
            coll = collector.results.get(f"{file}::<collection>")
            collector.results[tid] = {
                "id": tid,
                "outcome": "error",
                "message": coll["message"] if coll else "test was not executed",
            }
    tests = [collector.results[tid] for tid in manifest["expected_test_ids"]]
    audit = [
        {"event": e, "kind": "forbidden_operation", "path": p, "count": n}
        for (e, p), n in sorted(_State.forbidden.items())
    ]
    audit += [
        {"event": e, "kind": "out_access", "path": p, "count": n}
        for (e, p), n in sorted(_State.out_access.items())
    ]
    result = {
        "tests": tests,
        "audit_events": audit,
        "duration_ms": int((time.monotonic() - started) * 1000),
    }
    _State.harness_writing = True
    (out / "result.json").write_text(json.dumps(result))
    return 0


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m academy_sim.run /work /out", file=sys.stderr)
        sys.exit(2)
    sys.exit(run(Path(sys.argv[1]), Path(sys.argv[2])))


if __name__ == "__main__":
    main()
