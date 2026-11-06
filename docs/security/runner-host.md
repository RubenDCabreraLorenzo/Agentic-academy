# Runner host security — checklist and known limitations

Source of truth: `specs/001-agentic-academy-mvp/contracts/runner-protocol.md` (§0 trust boundaries,
§8 limitations) and ADR 0005.

## Trust boundaries (runner protocol §0)

| Zone | Trusted with | Must never have |
|------|--------------|-----------------|
| Browser (untrusted) | Its own session cookie; challenge tests and starter files | Reference solutions, other learners' data |
| API host (trusted) | Full database role, session secrets, SMTP credentials, content bundle | Execution of learner code; reference solutions |
| PostgreSQL (trusted) | All learner data | — |
| Runner host (trusted, exposed) | Docker/gVisor daemon, content bundles, `academy_runner` role limited to three functions | API secrets, SMTP credentials, table access, learner identity, reference solutions |
| Sandbox (untrusted) | Learner files, the evaluated challenge's tests, `academy_sim`, its own `/out` | Network, secrets, database, other submissions, reference solutions |

Everything produced inside the sandbox — stdout, stderr and `/out/result.json` — is untrusted input.

## Hardening checklist (before the first public deployment)

- [ ] Dedicated host or VM for the runner; nothing else deployed there.
- [ ] gVisor `runsc` installed, version pinned, updated monthly; `docker run --runtime=runsc hello-world` verified.
- [ ] `APP_ENV=production` (refuses `runc`, unpinned images and a non-tmpfs `RUNNER_OUT_DIR`).
- [ ] `RUNNER_SANDBOX_IMAGE` pinned by digest; image rebuilt through review only.
- [ ] `RUNNER_OUT_DIR` is a fixed-size tmpfs (size = concurrency × 2 MB), mode 0700, owned by the runner user.
- [ ] Only secret on the host: `RUNNER_DATABASE_URL` for `academy_runner` (no table privileges; verified by
      `backend/tests/integration/challenges/test_runner_functions.py`).
- [ ] Docker socket reachable only by the runner process; no other users on the host.
- [ ] Reaper enabled (default); alerts on repeated `error` submissions and on missing heartbeats.
- [ ] Sandbox security suite green **under runsc**: `uv run --project runner pytest tests/security`.
      (On 2026-11-06 it passed 20/20 under `runc` in development; that run is NOT security evidence.)

## Accepted residual risks (product owner, 2026-11-06)

- **D1 — result tampering**: learner code runs in the same process as the harness and can write
  `/out/result.json`. Validation (exact test-id set, regular file ≤ 1 MB, exit status) is an
  integrity check, **not tamper-proof evaluation**: a determined learner can fake a pass for their
  own submission. Acceptable only while no certificates or public credentials exist; revisit before
  introducing any.
- **D2 — no hidden tests**: all tests are visible; learners can overfit to them.
- gVisor is not a VM; micro-architectural side channels are not addressed (runner protocol §8).

## External penetration test scope

1. Sandbox escape attempts from learner code under `runsc` (filesystem, syscalls, `/proc`, Docker socket).
2. Runner database role: privilege escalation through the `SECURITY DEFINER` functions.
3. API: authentication, CSRF, session handling, rate limiting, IDOR on attempts and submissions.
4. Stored content rendering (Markdown sanitization, Mermaid strict mode) and CSP.
