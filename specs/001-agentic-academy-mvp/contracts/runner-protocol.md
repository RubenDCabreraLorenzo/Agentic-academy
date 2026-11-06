# Contract: Submission runner protocol

**Parties**: backend API (producer), runner service (consumer), sandbox container (executor).
Requirements: FR-022, FR-022a–c, FR-047, FR-051, NFR-006, NFR-006a, SC-011, SC-012.
Decision record: [research R6, R7](../research.md). Review: [architecture-review.md](../architecture-review.md).

## 0. Trust boundaries

| Zone | Trusted with | Must never have |
|------|--------------|-----------------|
| **Browser** (untrusted) | Its own session cookie; challenge tests and starter files | Reference solutions, other learners' data |
| **API host** (trusted) | Full database role, session secrets, SMTP credentials, content bundle | Execution of learner code; reference solutions |
| **PostgreSQL** (trusted) | All learner data | — |
| **Runner host** (trusted, exposed) | Docker/gVisor daemon, content bundles (challenge tests by version), a database role limited to the runner functions in §1 | API secrets, SMTP credentials, direct table access, learner identity (account ids, emails), reference solutions |
| **Sandbox container** (untrusted) | Learner files, the tests of the one challenge being evaluated, `academy_sim`, its own `/out` directory | Network, environment secrets, database, other submissions, reference solutions, the rest of the content bundle |

Everything produced inside the sandbox — stdout, stderr and `/out/result.json` — is written by a
process that also runs learner code, so the runner treats it as **untrusted input** (§5, §8.2).

The runner host is treated as *trusted but exposed*: a sandbox escape is assumed to compromise it,
so it holds nothing beyond what is needed to execute and report jobs.

## 1. Queue (PostgreSQL) and database access

The runner's database role has **no table privileges**. It may only execute three
`SECURITY DEFINER` functions owned by the API schema:

| Function | Behavior |
|----------|----------|
| `runner_claim_job(worker_id) → job` | Atomically picks the oldest available job (`FOR UPDATE SKIP LOCKED`), sets `status=running`, a fresh `lease_id` (UUID), `lease_expires_at = now() + 60 s`, increments `infra_attempts`, and returns only: `submission_id`, `lease_id`, `challenge_id`, `content_version`, `bundle_version`, `kind`, `files`, `limits`. No account id. |
| `runner_complete_job(submission_id, lease_id, result_json) → bool` | Writes the result only if `lease_id` matches and the lease has not been superseded (fencing). Returns false otherwise; the late result is discarded. |
| `runner_heartbeat(worker_id, capacity)` | Upserts `runner_worker.last_heartbeat_at`; also used to extend leases of the worker's running jobs. |

Rules:

- Workers send a heartbeat every 10 s. The API considers evaluation **available** if at least one
  worker heartbeat is newer than 30 s.
- A job whose lease expired (worker crashed or hung) becomes claimable again. After 3 infrastructure
  attempts the submission becomes `error` (not counted as an attempt).
- Queue position for the learner = number of earlier jobs still `queued`.
- The API rejects new submissions with `503 evaluation_unavailable` when no worker is available, or
  when the queue exceeds 200 jobs; the learner's code stays in the workspace (spec edge case).
- A submission queued for more than 5 minutes is shown as "delayed" to the learner.

## 2. Execution

Every job runs in **one fresh container**. `visible_run` and `submission` execute the same tests;
only a `submission` can complete a challenge and count as an attempt. The MVP has no hidden tests
(architecture review D2).

```text
/work/                        # read-only bind mount, rebuilt for every job
├── submission/               # learner files
├── tests/                    # only the tests of this challenge, copied from the content bundle
│                             # of the submission's bundle_version (never from learner input)
└── manifest.json             # test ids expected, limits (no secrets)
/out/                         # writable per-job directory (see §3), result file only
/tmp/                         # writable tmpfs (16 MB)
```

- Learner files are rejected before execution (job `failed`, reason "invalid submission files")
  when a path is absolute, contains `..`, or uses a reserved name that could shadow the harness:
  `conftest.py`, `sitecustomize.py`, `usercustomize.py`, `pytest.py`, `pytest/`, `_pytest/`,
  `academy_sim*`, `*.pth`. This blocks accidental and trivial shadowing; it does not make the harness
  tamper-proof (§8.2).

- Reference solutions are **never** mounted in any learner run; they are used only by the content
  validator (content-schema rule 7).
- Test output is returned to the learner (truncated, scrubbed), since all tests are visible.
- *Later release*: hidden tests would run in a second, fresh container whose output is never
  returned (design retained from the architecture review, C1).

## 3. Sandbox configuration

- Image: `academy-sandbox@sha256:<pinned digest>` with Python 3.13, pytest, `academy_sim`; no other
  packages; rebuilt and re-pinned through normal review.
- Runtime: gVisor `runsc`; `--network none`; `--read-only`; `--tmpfs /tmp:size=16m`;
  `/out` bind-mounted from a fresh, empty per-job directory owned by `65534` inside a fixed-size
  host tmpfs dedicated to the runner (e.g. `/var/lib/academy-runner/out`, provisioned on the runner
  host; total size = concurrency × 2 MB), removed after the result is read — an in-container
  `--tmpfs` would be discarded when the container exits, before the runner can read it;
  `--user 65534:65534`; `--cap-drop ALL`;
  `--security-opt no-new-privileges`; `--pids-limit 64`; `--memory 256m --memory-swap 256m`;
  `--cpus 1`; `--ulimit nofile=64`; labels `academy.submission=<id>`, `academy.worker=<id>`,
  `academy.deadline=<epoch>`.
- Environment: only `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`; pytest runs with
  `-p no:cacheprovider`.
- Entrypoint: `python -m academy_sim.run /work /out`. The harness installs Python audit hooks
  (`sys.addaudithook`, which cannot be removed) **before** importing learner code, to *detect and
  report* attempts to open sockets, spawn processes or access paths outside `/work`, `/tmp`.
  Enforcement is the sandbox's job; the hooks only provide a clear `forbidden_operation` reason.

## 4. Limits and stop reasons

| Limit (platform maximum) | Enforced by | stop_reason |
|--------------------------|-------------|-------------|
| Wall clock: 10 s per job (challenge may set lower) | Runner kills the container at deadline | `timeout` |
| Memory: 256 MB | cgroup; container exits with OOM | `memory` |
| Output: 64 KB per job | Runner stops reading and kills the container | `output_limit` |
| Socket/process/path access attempts | Network namespace + gVisor (enforce), audit hooks (report) | `forbidden_operation` |
| PIDs: 64; open files: 64 | cgroup / ulimit | reported as test errors |

## 5. Result

The harness writes `/out/result.json`; the runner never parses stdout as a result. Learner code
can also write or overwrite this file (same process, same user), so the file is untrusted input:
validation below rejects malformed or inconsistent results, but **cannot detect a forged result
that reports the exact expected test ids as passed**. This is the residual risk accepted in D1.

```json
{
  "tests": [
    { "id": "test_tool_schema_valid", "outcome": "passed | failed | error | skipped",
      "message": "AssertionError: expected 'priority' to be required" }
  ],
  "audit_events": [ { "event": "socket.connect", "count": 1 } ],
  "duration_ms": 2140
}
```

The runner **validates** the result before accepting it:

1. The file is a regular file (opened with `O_NOFOLLOW`; symlinks, directories and other file
   types are rejected), is ≤ 1 MB, is valid JSON and matches the schema above.
2. The set of test ids equals exactly the expected set from `manifest.json` (no missing, extra or
   duplicated ids); otherwise the job is `failed` with reason "test harness integrity check
   failed".
3. The container exit status is consistent with the reported outcomes.

Then it maps tests to criteria (`met` ⇔ all its tests passed), sets `passed` ⇔ all mandatory
criteria met, attaches authored feedback, scrubs secret-like patterns from messages and output
(FR-047), and calls `runner_complete_job`.

## 6. Failure semantics

| Situation | Submission status | Counts as attempt |
|-----------|-------------------|-------------------|
| Tests fail | `failed` | yes |
| Limit exceeded / forbidden operation | `stopped` + reason | yes |
| Integrity check fails (missing/extra test ids, malformed result) | `failed` | yes |
| Worker crash or hang (lease expires) | re-queued, then `error` after 3 attempts | no |
| Image pull failure, Docker/gVisor daemon error, host error | re-queued, then `error` after 3 attempts | no |
| No worker available at submission time | rejected `503`, nothing stored except the workspace | no |
| Late result after lease superseded | discarded (fencing) | — |

**Orphan containers**: on start-up each worker removes containers labeled with its `worker_id`;
a reaper on the runner host removes any `academy.*` container past `academy.deadline + 30 s`.

## 7. Content versions

The runner resolves challenge tests by `bundle_version` from a local store that keeps every
published bundle (immutable), so a submission started before a content release is evaluated against
the version the learner was working on (spec edge case, FR-051).

## 8. Known limitations of the isolation model

1. **gVisor is not a virtual machine.** It reduces the host kernel attack surface by implementing
   syscalls in a user-space kernel, but a bug in gVisor or in the host kernel paths it uses could
   allow an escape. Mitigation: dedicated runner host with nothing valuable on it, pinned and
   patched gVisor, restricted DB functions. Upgrade path: microVMs (Firecracker).
2. **Result integrity is not tamper-proof.** Learner code runs in the same process as the tests and
   the harness, so a deliberate learner can subvert pytest or the harness and fake a pass for
   *their own* submission. Validation (§5) prevents trivial forgery, not a determined attacker.
   Impact is limited to the learner's own progress because the MVP issues no certificates or
   public credentials. Accepted by the product owner (architecture review D1); to be revisited if
   certificates or public credentials are introduced.
3. **All tests are visible** (D2), so a learner can write code that satisfies the tests without
   generalizing. Challenge design mitigates this with behavior-oriented tests and the reference
   explanation shown after passing.
4. **Micro-architectural side channels** (e.g. Spectre-class) are not addressed; acceptable because
   the sandbox holds no secrets and runs one submission at a time per container.
5. **Resource exhaustion on the host** is limited by cgroups and worker concurrency, not eliminated;
   a burst of heavy submissions increases queue time (visible to learners), not cross-tenant access.
6. **Development exception**: `RUNNER_RUNTIME=runc` (plain containers) exists for machines without
   gVisor (e.g. macOS). It is refused at start-up when `APP_ENV=production` and logs a warning in
   every other environment. The security suite is only meaningful under `runsc`.

## 9. `academy_sim` public API (used by challenge tests)

| Symbol | Purpose |
|--------|---------|
| `ScriptedModel(turns)` | Model double returning scripted messages / tool-call requests per turn |
| `FakeTool(name, permission, handler)` | Tool double that records calls and enforces declared permission |
| `ApprovalGate(decisions)` | Simulates human approval decisions for destructive tools |
| `TraceRecorder` | Captures the four trace element kinds produced by learner code |
| `assert_tool_called(trace, name, **args)` and similar helpers | Readable assertions for criteria |

The package is vendor-neutral; learner code interacts with it through a small `ModelClient`
protocol taught in the course (Principle VI).
