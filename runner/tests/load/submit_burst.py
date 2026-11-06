"""Submit N concurrent correct solutions through the API and report p95 time-to-result.

Target: 95% of results within 30 s (NFR-006a, SC-012). Requires the stack from quickstart "Run"
(API, runner, database) with CHALLENGES_ENABLED=true and RATE_LIMIT_ENABLED=false.

    uv run --project backend python runner/tests/load/submit_burst.py --n 10
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import http.cookiejar
import json
import statistics
import sys
import time
import urllib.request
import uuid
from typing import Any

PASSWORD = "load-test-password-123"


class Client:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/") + "/api/v1"
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def csrf(self) -> str:
        return next((c.value for c in self.jar if c.name == "aa_csrf"), "")

    def call(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("X-CSRF-Token", self.csrf())
        try:
            with self.opener.open(req, timeout=30) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            raw = err.read()
            return err.code, json.loads(raw) if raw else None


def run_one(base: str, challenge: str, files: dict[str, str], seed_cmd: Any) -> float:
    c = Client(base)
    email = seed_cmd()
    status, _ = c.call("POST", "/auth/sign-in", {"email": email, "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"sign-in failed: {status}")
    start = time.monotonic()
    status, sub = c.call(
        "POST", f"/challenges/{challenge}/submissions",
        {"submission_id": str(uuid.uuid4()), "kind": "submission", "files": files},
    )
    if status != 202:
        raise RuntimeError(f"submission refused: {status} {sub}")
    while True:
        _, sub = c.call("GET", f"/submissions/{sub['submission_id']}")
        if sub["status"] not in ("queued", "running"):
            if sub["status"] != "passed":
                raise RuntimeError(f"unexpected result {sub['status']}")
            return time.monotonic() - start
        time.sleep(0.5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--challenge", default="apply-temperature")
    parser.add_argument("--solution", default="content/en/paths/foundations-of-agentic-ai-engineering/modules/01-llm-foundations/challenges/apply-temperature/solution/sampling.py")
    parser.add_argument("--database-url", default="postgresql://academy:academy@localhost:5432/academy")
    args = parser.parse_args()
    with open(args.solution) as fh:
        files = {"sampling.py": fh.read()}

    import psycopg
    from argon2 import PasswordHasher

    pw_hash = PasswordHasher().hash(PASSWORD)

    def seed() -> str:
        email = f"load-{uuid.uuid4().hex[:10]}@example.com"
        with psycopg.connect(args.database_url, autocommit=True) as conn:
            conn.execute(
                "INSERT INTO account (id, email, password_hash, status, email_verified_at) "
                "VALUES (%s, %s, %s, 'active', now())",
                (uuid.uuid4(), email, pw_hash),
            )
        return email

    with cf.ThreadPoolExecutor(args.n) as pool:
        durations = list(pool.map(lambda _: run_one(args.base, args.challenge, files, seed), range(args.n)))
    durations.sort()
    p95 = durations[max(0, round(0.95 * len(durations)) - 1)]
    print(json.dumps({"n": args.n, "p50": round(statistics.median(durations), 2), "p95": round(p95, 2),
                      "max": round(durations[-1], 2), "target_p95_seconds": 30, "ok": p95 <= 30}))
    return 0 if p95 <= 30 else 1


if __name__ == "__main__":
    sys.exit(main())
