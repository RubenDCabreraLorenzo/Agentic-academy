"""Sandbox launcher (runner protocol §2–§4).

Each job runs in one fresh container with: gVisor ``runsc`` (``runc`` only as a development
exception), no network, read-only root filesystem, a 16 MB ``/tmp`` tmpfs, a per-job ``/out``
directory, an unprivileged user, all capabilities dropped, ``no-new-privileges``, and limits on
PIDs, memory, CPU, open files, wall-clock time and output size.

``/work`` is mounted read-only and holds separate trees, so learner files can never overwrite,
shadow or replace the trusted evaluation tests: ``/work/submission`` (learner files only),
``/work/tests`` (copied from the immutable bundle of the pinned version, never from the payload)
and ``/work/manifest.json`` (written by the runner).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound
from docker.types import Ulimit

from academy_runner.config import MAX_WALL_SECONDS, MEMORY, OUTPUT_LIMIT_BYTES, Settings
from academy_runner.files import InvalidFilesError, validate_files
from academy_runner.results import (
    IntegrityError,
    forbidden_events,
    integrity_failure,
    map_criteria,
    out_access_events,
    read_result_file,
    scrub,
    validate_result,
)

log = logging.getLogger(__name__)
LABEL = "academy.submission"


class InfraError(RuntimeError):
    """Docker/gVisor/host failure: the job is re-queued and does not count as an attempt."""


@dataclass
class Job:
    submission_id: uuid.UUID
    lease_id: uuid.UUID
    challenge_id: str
    content_version: str
    bundle_version: str
    kind: str
    files: dict[str, Any]
    limits: dict[str, Any]


def _safe_write(base: Path, rel: str, content: str) -> None:
    target = (base / rel).resolve()
    if not str(target).startswith(str(base.resolve()) + os.sep):
        raise InvalidFilesError(f"invalid path '{rel}'")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _make_world_readable(root: Path) -> None:
    for dirpath, _dirnames, filenames in os.walk(root):
        os.chmod(dirpath, 0o755)  # noqa: S103 - read-only mount for the unprivileged sandbox user
        for f in filenames:
            os.chmod(os.path.join(dirpath, f), 0o644)


class Sandbox:
    def __init__(self, settings: Settings, client: docker.DockerClient | None = None) -> None:
        self.s = settings
        self._client = client

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def prepare(self, job: Job, challenge: dict[str, Any], job_dir: Path) -> tuple[Path, Path]:
        work, out = job_dir / "work", job_dir / "out"
        (work / "submission").mkdir(parents=True)
        (work / "tests").mkdir()
        out.mkdir()
        for rel, content in job.files.items():
            _safe_write(work / "submission", rel, content)
        for rel, content in challenge["tests"].items():
            _safe_write(work / "tests", rel, content)
        test_files = sorted(
            n
            for n in challenge["tests"]
            if n.rsplit("/", 1)[-1].startswith("test_") and n.endswith(".py")
        )
        manifest = {
            "submission_id": str(job.submission_id),
            "challenge_id": job.challenge_id,
            "content_version": job.content_version,
            "kind": job.kind,
            "test_files": test_files,
            "expected_test_ids": challenge["test_ids"],
        }
        (work / "manifest.json").write_text(json.dumps(manifest))
        _make_world_readable(work)
        os.chmod(job_dir, 0o700)
        os.chmod(out, 0o777)  # noqa: S103 - only this container mounts it; the parent is 0700
        return work, out

    def run(self, job: Job, challenge: dict[str, Any]) -> dict[str, Any]:
        try:
            validate_files(job.files, challenge["tests"])
        except InvalidFilesError as exc:
            return integrity_failure(challenge, f"invalid submission files ({exc})") | {
                "output_excerpt": f"Invalid submission files: {exc}"
            }
        wall = min(
            int(challenge.get("limits", {}).get("wall_seconds", MAX_WALL_SECONDS)), MAX_WALL_SECONDS
        )
        self.s.runner_out_dir.mkdir(parents=True, exist_ok=True)
        job_dir = self.s.runner_out_dir.resolve() / str(job.submission_id)
        if job_dir.exists():
            shutil.rmtree(job_dir)
        job_dir.mkdir()
        container = None
        try:
            work, out = self.prepare(job, challenge, job_dir)
            deadline = int(time.time()) + wall
            try:
                container = self.client.containers.run(
                    self.s.runner_sandbox_image,
                    detach=True,
                    runtime=self.s.runner_runtime,
                    network_mode="none",
                    read_only=True,
                    tmpfs={"/tmp": "size=16m,mode=1777"},  # noqa: S108 - path inside the sandbox
                    volumes={
                        str(work): {"bind": "/work", "mode": "ro"},
                        str(out): {"bind": "/out", "mode": "rw"},
                    },
                    user="65534:65534",
                    cap_drop=["ALL"],
                    security_opt=["no-new-privileges"],
                    pids_limit=64,
                    mem_limit=MEMORY,
                    memswap_limit=MEMORY,
                    nano_cpus=1_000_000_000,
                    ulimits=[Ulimit(name="nofile", soft=64, hard=64)],
                    environment={"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"},
                    labels={
                        LABEL: str(job.submission_id),
                        "academy.worker": self.s.runner_worker_id,
                        "academy.deadline": str(deadline),
                    },
                    stdout=True,
                    stderr=True,
                )
            except ImageNotFound as exc:
                raise InfraError("sandbox image not found") from exc
            except (APIError, DockerException) as exc:
                raise InfraError(f"cannot start sandbox: {type(exc).__name__}") from exc
            return self._supervise(container, out, wall, challenge)
        finally:
            if container is not None:
                with contextlib.suppress(NotFound, APIError):
                    container.remove(force=True)
            shutil.rmtree(job_dir, ignore_errors=True)

    def _supervise(
        self, container: Any, out: Path, wall: int, challenge: dict[str, Any]
    ) -> dict[str, Any]:
        output = bytearray()
        exceeded = threading.Event()

        def pump() -> None:
            try:
                for chunk in container.logs(stream=True, follow=True):
                    if len(output) < OUTPUT_LIMIT_BYTES:
                        output.extend(chunk[: OUTPUT_LIMIT_BYTES - len(output)])
                    else:
                        exceeded.set()
                        container.kill()
                        return
            except (APIError, DockerException, NotFound):
                return

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        timed_out = False
        exit_code = -1
        try:
            status = container.wait(timeout=wall + 2)
            exit_code = int(status.get("StatusCode", -1))
        except Exception:
            timed_out = True
            with contextlib.suppress(APIError, NotFound):
                container.kill()
        reader.join(timeout=2)
        try:
            container.reload()
            oom = bool(container.attrs.get("State", {}).get("OOMKilled"))
            if exit_code == -1:
                exit_code = int(container.attrs.get("State", {}).get("ExitCode", -1))
        except (APIError, NotFound):
            oom = False
        excerpt = scrub(output.decode("utf-8", "replace"))[:OUTPUT_LIMIT_BYTES]

        def stopped(reason: str, note: str) -> dict[str, Any]:
            res = integrity_failure(challenge, note)
            for c in res["criteria_results"]:
                c["feedback_markdown"] = note
            return {
                **res,
                "status": "stopped",
                "stop_reason": reason,
                "output_excerpt": f"{note}\n\n{excerpt}"[:OUTPUT_LIMIT_BYTES],
            }

        if timed_out:
            return stopped("timeout", f"Stopped: your code ran longer than {wall} seconds.")
        if exceeded.is_set():
            return stopped("output_limit", "Stopped: your code printed more than 64 KB of output.")
        if oom or exit_code == 137:
            return stopped("memory", "Stopped: your code used more than 256 MB of memory.")
        try:
            data = read_result_file(out)
            tests = validate_result(data, challenge["test_ids"], exit_code)
        except IntegrityError as exc:
            res = integrity_failure(challenge, str(exc))
            res["output_excerpt"] = f"{res['output_excerpt']}\n\n{excerpt}"[:OUTPUT_LIMIT_BYTES]
            return res
        forbidden = forbidden_events(data)
        if out_access_events(data):
            log.info(
                "out_access observed for submission %s: %s",
                challenge.get("id"),
                out_access_events(data),
            )
        if forbidden:
            names = ", ".join(sorted({str(e.get("event")) for e in forbidden}))
            return stopped(
                "forbidden_operation",
                f"Stopped: a forbidden operation was attempted ({names}). "
                "Network access, starting processes and reading system files are not allowed.",
            )
        criteria, passed = map_criteria(challenge, tests)
        return {
            "status": "passed" if passed else "failed",
            "stop_reason": None,
            "criteria_results": criteria,
            "output_excerpt": excerpt,
        }

    def reap(self, grace_seconds: int = 30, only_own: bool = False) -> int:
        """Remove sandbox containers past their deadline (or all of this worker's on start-up)."""
        removed = 0
        try:
            containers = self.client.containers.list(all=True, filters={"label": LABEL})
        except (APIError, DockerException):
            return 0
        now = time.time()
        for c in containers:
            labels = c.labels or {}
            own = labels.get("academy.worker") == self.s.runner_worker_id
            try:
                deadline = int(labels.get("academy.deadline", "0"))
            except ValueError:
                deadline = 0
            if (only_own and own) or (not only_own and now > deadline + grace_seconds):
                try:
                    c.remove(force=True)
                    removed += 1
                except (APIError, NotFound):
                    pass
        return removed
