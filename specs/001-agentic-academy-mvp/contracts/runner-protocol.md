# Contract: Submission runner protocol

**Parties**: backend API (producer), runner service (consumer), sandbox container (executor).
Requirements: FR-022, FR-022a–c, NFR-006, NFR-006a, SC-011, SC-012. Decision record: [research R6, R7](../research.md).

## 1. Queue (PostgreSQL)

- The API inserts a `ChallengeSubmission` (`status=queued`) and a `SubmissionJob` in one transaction.
- A runner worker claims one job:

  ```sql
  SELECT submission_id FROM submission_job
  WHERE available_at <= now() AND (locked_at IS NULL OR locked_at < now() - interval '2 minutes')
  ORDER BY available_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1;
  ```

- The runner's database role may only `SELECT/UPDATE` `submission_job` and `challenge_submission`
  (least privilege). It has no access to accounts, sessions or other tables.
- Queue position for the learner = number of earlier jobs still `queued`.

## 2. Job input (runner → sandbox)

The runner builds a read-only work tree and mounts it at `/work`:

```text
/work/
├── submission/     # learner files (from ChallengeSubmission.files)
├── tests/          # visible tests, plus hidden tests if kind=submission
└── manifest.json
```

`manifest.json`:

```json
{
  "submission_id": "uuid",
  "challenge_id": "string",
  "content_version": "1.2.0",
  "kind": "visible_run | submission",
  "criteria": [{ "id": "c1", "mandatory": true, "tests": ["test_tool_schema_valid"] }],
  "limits": { "cpu_seconds": 10, "memory_mb": 256, "wall_seconds": 20, "output_kb": 64 }
}
```

## 3. Sandbox execution

- Image: `academy-sandbox:<pinned digest>` with Python 3.13, pytest, `academy_sim`; no other packages.
- Runtime: gVisor `runsc`; `--network none`; `--read-only`; `--tmpfs /tmp:size=16m`;
  `--user 65534`; `--cap-drop ALL`; `--security-opt no-new-privileges`; `--pids-limit 64`;
  `--memory 256m --memory-swap 256m`; `--cpus 1`; no environment variables except `PYTHONHASHSEED=0`.
- Entrypoint: `python -m academy_sim.run /work` → runs pytest with the JSON report plugin and writes
  the report to stdout as a single JSON document.
- The runner kills the container at `wall_seconds` (stop_reason `timeout`), on OOM (`memory`),
  when output exceeds `output_kb` (`output_limit`), or when the sandbox reports a blocked syscall /
  network attempt (`forbidden_operation`).

## 4. Result (sandbox → runner → database)

```json
{
  "submission_id": "uuid",
  "status": "passed | failed | stopped | error",
  "stop_reason": null,
  "duration_ms": 2140,
  "tests": [
    { "id": "test_tool_schema_valid", "outcome": "passed | failed | error | skipped",
      "message": "AssertionError: expected 'priority' to be required", "hidden": false }
  ],
  "output_excerpt": "…truncated to 64 KB…"
}
```

The runner maps tests to criteria (`met` ⇔ all its tests passed), sets `passed` ⇔ all mandatory
criteria met, attaches per-criterion feedback authored in `challenge.yaml`, scrubs secret-like
patterns from messages and output, and updates the submission in one transaction. For hidden
tests only the test title and the criterion feedback are returned, never the test source.

## 5. Failure semantics

| Situation | Submission status | Counts as attempt |
|-----------|-------------------|-------------------|
| Tests fail | `failed` | yes |
| Limit exceeded / forbidden operation | `stopped` + reason | yes |
| Runner crash, image pull failure, host error (after 3 retries) | `error` | no |
| Malformed report from sandbox | `error` | no |

## 6. `academy_sim` public API (used by challenge tests)

| Symbol | Purpose |
|--------|---------|
| `ScriptedModel(turns)` | Model double returning scripted messages / tool-call requests per turn |
| `FakeTool(name, permission, handler)` | Tool double that records calls and enforces declared permission |
| `ApprovalGate(decisions)` | Simulates human approval decisions for destructive tools |
| `TraceRecorder` | Captures the four trace element kinds produced by learner code |
| `assert_tool_called(trace, name, **args)` and similar helpers | Readable assertions for criteria |

The package is vendor-neutral; learner code interacts with it through a small `ModelClient`
protocol taught in the course (Principle VI).
