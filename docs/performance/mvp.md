# Performance measurements — MVP

**Date**: 2026-11-06 · **Environment**: single development container (API under uvicorn, Vite dev
server, PostgreSQL 17 in Docker, runner with `RUNNER_RUNTIME=runc`, concurrency 2).
These are development measurements; repeat them on the production host before release.

| Target | Requirement | Measured | Command |
|--------|-------------|----------|---------|
| Module page readable | < 2 s p95 (NFR-003) | **1,023 ms** p95 over 10 loads (dev server, unminified) | `pnpm --dir frontend exec playwright test perf --project=desktop` |
| Knowledge-check feedback | < 1 s p95 (NFR-003) | **86 ms** p95 over 7 answers | same |
| Challenge result | 95% < 30 s (NFR-006a, SC-012) | **p50 3.96 s, p95 6.02 s, max 6.02 s** for 10 simultaneous correct submissions | `uv run --project backend python runner/tests/load/submit_burst.py --n 10` |

Caveats:

- Sandbox timings were taken with `runc`. gVisor (`runsc`) adds container start-up overhead
  (typically sub-second); re-measure on a gVisor host.
- The production frontend is a minified build served by nginx; page timings should improve.
