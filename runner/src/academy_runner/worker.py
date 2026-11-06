"""Worker loop: claim → run in sandbox → complete; heartbeat every 10 s; reap orphans."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from academy_runner.config import Settings
from academy_runner.content import BundleStore, ContentMissingError
from academy_runner.db import RunnerDb
from academy_runner.sandbox import InfraError, Job, Sandbox

log = logging.getLogger(__name__)
HEARTBEAT_SECONDS = 10
REAP_SECONDS = 30


class Worker:
    def __init__(
        self, settings: Settings, db: RunnerDb | None = None, sandbox: Sandbox | None = None
    ) -> None:
        self.s = settings
        self.db = db or RunnerDb(settings.dsn)
        self.sandbox = sandbox or Sandbox(settings)
        self.store = BundleStore(settings.content_dir)
        self.stop = threading.Event()
        self._slots = threading.Semaphore(settings.runner_concurrency)

    def process(self, job: Job) -> None:
        try:
            try:
                challenge = self.store.challenge(job.bundle_version, job.challenge_id)
                result = self.sandbox.run(job, challenge)
            except (InfraError, ContentMissingError) as exc:
                log.error("infrastructure error for %s: %s", job.submission_id, exc)
                result = {"status": "error"}
            except Exception:
                log.exception("unexpected runner error for %s", job.submission_id)
                result = {"status": "error"}
            if not self.db.complete(job, result):
                log.warning("result for %s discarded (lease superseded)", job.submission_id)
        finally:
            self._slots.release()

    def _heartbeat_loop(self) -> None:
        while not self.stop.is_set():
            try:
                self.db.heartbeat(self.s.runner_worker_id, self.s.runner_concurrency)
            except Exception as exc:
                log.error("heartbeat failed: %s", type(exc).__name__)
            self.stop.wait(HEARTBEAT_SECONDS)

    def _reap_loop(self) -> None:
        while not self.stop.wait(REAP_SECONDS):
            removed = self.sandbox.reap()
            if removed:
                log.info("reaped %d orphan sandbox container(s)", removed)

    def run_forever(self) -> None:
        removed = self.sandbox.reap(only_own=True)
        if removed:
            log.info("removed %d leftover container(s) of this worker", removed)
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._reap_loop, daemon=True).start()
        with ThreadPoolExecutor(self.s.runner_concurrency) as pool:
            while not self.stop.is_set():
                self._slots.acquire()
                try:
                    job = self.db.claim(self.s.runner_worker_id)
                except Exception as exc:
                    log.error("claim failed: %s", type(exc).__name__)
                    job = None
                if job is None:
                    self._slots.release()
                    self.stop.wait(self.s.poll_interval_seconds)
                    continue
                pool.submit(self.process, job)

    def run_once(self) -> bool:
        """Claim and process a single job synchronously (tests and load scripts)."""
        self._slots.acquire()
        job = self.db.claim(self.s.runner_worker_id)
        if job is None:
            self._slots.release()
            return False
        self.process(job)
        return True


def drain(worker: Worker, timeout: float = 60) -> int:
    done = 0
    end = time.monotonic() + timeout
    while time.monotonic() < end and worker.run_once():
        done += 1
    return done
