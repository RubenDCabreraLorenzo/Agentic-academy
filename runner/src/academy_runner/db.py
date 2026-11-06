"""Database access through the three runner functions only (runner protocol §1).

The runner role has no table privileges; every call goes through a ``SECURITY DEFINER`` function.
Short-lived connections keep worker threads independent.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg

from academy_runner.sandbox import Job


class RunnerDb:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _conn(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self.dsn, autocommit=True, connect_timeout=5)

    def heartbeat(self, worker_id: str, capacity: int) -> None:
        with self._conn() as conn:
            conn.execute("SELECT runner_heartbeat(%s, %s)", (worker_id, capacity))

    def claim(self, worker_id: str) -> Job | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM runner_claim_job(%s)", (worker_id,)).fetchone()
        if row is None:
            return None
        sid, lease, challenge_id, content_version, bundle_version, kind, files, limits = row
        return Job(
            submission_id=sid if isinstance(sid, uuid.UUID) else uuid.UUID(str(sid)),
            lease_id=lease if isinstance(lease, uuid.UUID) else uuid.UUID(str(lease)),
            challenge_id=challenge_id,
            content_version=content_version,
            bundle_version=bundle_version,
            kind=kind,
            files=files or {},
            limits=limits or {},
        )

    def complete(self, job: Job, result: dict[str, Any]) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT runner_complete_job(%s, %s, %s::jsonb)",
                (job.submission_id, job.lease_id, json.dumps(result)),
            ).fetchone()
        return bool(row and row[0])
