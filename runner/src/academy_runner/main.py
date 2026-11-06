"""``academy-runner`` entry point."""

from __future__ import annotations

import logging
import signal
import sys

from academy_runner.config import Settings
from academy_runner.worker import Worker


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    )
    settings = Settings()
    settings.enforce_guards()
    worker = Worker(settings)
    signal.signal(signal.SIGTERM, lambda *_: worker.stop.set())
    signal.signal(signal.SIGINT, lambda *_: worker.stop.set())
    logging.getLogger(__name__).info(
        "runner %s starting (runtime=%s, concurrency=%d)",
        settings.runner_worker_id,
        settings.runner_runtime,
        settings.runner_concurrency,
    )
    worker.run_forever()
    sys.exit(0)


if __name__ == "__main__":
    main()
