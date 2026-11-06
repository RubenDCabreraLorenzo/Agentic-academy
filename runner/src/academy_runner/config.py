"""Runner settings (quickstart "Environment variables").

Development-only exceptions are refused when ``APP_ENV=production`` and logged otherwise:
``RUNNER_RUNTIME=runc``, an image reference without a digest, and a ``RUNNER_OUT_DIR`` that is
not a tmpfs mount.
"""

from __future__ import annotations

import logging
import re
import socket
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)

#: Platform maximums (runner protocol §4).
MAX_WALL_SECONDS = 10
MEMORY = "256m"
OUTPUT_LIMIT_BYTES = 64 * 1024
RESULT_LIMIT_BYTES = 1024 * 1024


class ProductionGuardError(RuntimeError):
    pass


def _default_worker_id() -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", socket.gethostname())[:48] or "runner"


def is_tmpfs(path: Path) -> bool:
    try:
        target = str(path.resolve())
        best = ("", "")
        with open("/proc/mounts") as fh:
            for line in fh:
                parts = line.split()
                matches = len(parts) >= 3 and (
                    target == parts[1] or target.startswith(parts[1].rstrip("/") + "/")
                )
                if matches and len(parts[1]) > len(best[0]):
                    best = (parts[1], parts[2])
        return best[1] == "tmpfs"
    except OSError:
        return False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    runner_database_url: str = "postgresql://academy_runner:runner@localhost:5432/academy"
    content_dir: Path = Path("./dist/content")
    runner_runtime: Literal["runsc", "runc"] = "runsc"
    runner_sandbox_image: str = "academy-sandbox:dev"
    runner_concurrency: int = 2
    runner_out_dir: Path = Path("./.runner-out")
    runner_worker_id: str = _default_worker_id()
    poll_interval_seconds: float = 1.0

    @property
    def dsn(self) -> str:
        return self.runner_database_url.replace("postgresql+psycopg://", "postgresql://")

    def dev_exceptions(self) -> list[str]:
        problems = []
        if self.runner_runtime != "runsc":
            problems.append(
                f"RUNNER_RUNTIME={self.runner_runtime} (sandbox security results are not valid)"
            )
        if "@sha256:" not in self.runner_sandbox_image:
            problems.append("RUNNER_SANDBOX_IMAGE is not pinned by digest")
        if not is_tmpfs(self.runner_out_dir):
            problems.append("RUNNER_OUT_DIR is not a tmpfs mount")
        return problems

    def enforce_guards(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.runner_worker_id):
            raise ValueError("RUNNER_WORKER_ID must match [A-Za-z0-9_-]{1,64}")
        if not 1 <= self.runner_concurrency <= 16:
            raise ValueError("RUNNER_CONCURRENCY must be between 1 and 16")
        problems = self.dev_exceptions()
        if self.app_env == "production" and problems:
            raise ProductionGuardError("refusing to start in production: " + "; ".join(problems))
        for p in problems:
            log.warning("development-only runner setting: %s", p)
