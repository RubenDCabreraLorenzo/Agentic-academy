# Architecture Review: Agentic Academy MVP

**Date**: 2026-11-06 | **Scope**: [plan.md](./plan.md), [research.md](./research.md),
[data-model.md](./data-model.md), [quickstart.md](./quickstart.md), [contracts/](./contracts/),
checked against [spec.md](./spec.md) and the constitution.

**Outcome**: The architecture holds (modular monolith, PostgreSQL queue, gVisor runner; no stack
change). Five critical flaws were found in the sandbox and content-version design and **have been
corrected in the documents**, because existing requirements demanded it. The four product-owner
decisions were taken on 2026-11-06 and applied (section 4).

Legend: ✅ corrected in docs · 💡 recommended, not applied · ⚖️ needs product-owner decision.

---

## 1. Critical issues

| # | Issue | Why it is critical | Requirement | Status |
|---|-------|--------------------|-------------|--------|
| C1 | **Hidden tests and the reference solution were readable by learner code.** Both were mounted into the same container as the submission, whose output was returned to the learner, so `print(open('/work/tests/hidden/...').read())` would leak them. | Leaks hidden tests and solutions to every learner. | FR-022c, FR-022a | ✅ Hidden tests now run in a second fresh container whose output is never returned. Solutions moved to `solution/`, used only by the validator and never mounted. After D2 the MVP has no hidden tests: every job runs in one container, with tests taken from the content bundle and never from learner input. The two-container design is kept for a later release (runner protocol §2). |
| C2 | **The result was parsed from the sandbox's stdout**, which learner code controls, so a printed fake JSON report was accepted as a pass. | Trivial forgery of competency evidence. | Principle VII, FR-036 | ✅ The result now comes from `/out/result.json`, validated against the exact expected set of test ids and the exit status (runner protocol §5). The remaining tamper risk is documented → D1. |
| C3 | **Runner database role could `SELECT` all of `challenge_submission`.** A sandbox escape on the runner host would expose every learner's code and allow results to be rewritten at will. | Breaks least privilege and the "other learners' data" guarantee. | FR-022a, NFR-006, SC-011 | ✅ The runner has no table access. It uses three `SECURITY DEFINER` functions (claim, fenced complete, heartbeat) and never receives account ids (runner protocol §0–§1). |
| C4 | **No fencing or stale-job semantics.** A slow worker whose lock was reclaimed could overwrite a newer result. Orphan containers survived worker crashes. The API could not tell that the runner was down, although quickstart V7.3 expected an "evaluation unavailable" message. | Double execution, wrong results, untestable resilience requirement. | Spec edge case "evaluation service unavailable", Reliability standard | ✅ 60 s leases extended by heartbeat, `lease_id` fencing, 3 infrastructure attempts then `error` (not counted as an attempt), orphan reaper, `runner_worker` heartbeat, `503 evaluation_unavailable`, `/health` (runner protocol §1, §6; data-model §2.8–2.9a; OpenAPI). |
| C5 | **The backend kept only one content bundle**, contradicting the spec edge case "the learner finishes the version they started" and FR-051. An attempt or submission started before a release could not be scored. | Wrong scoring or lost attempts after every content release. | FR-051, spec edge case | ✅ All published bundles are kept as immutable versions. Attempts and submissions are scored with their own `bundle_version` (data-model §1.9, §2.6; runner protocol §7). |

## 2. Recommended changes

### 2.1 Sandbox security and resilience

- ✅ **Trust boundaries** are now explicit: browser, API host, PostgreSQL, runner host and sandbox,
  with what each zone may and may never hold (runner protocol §0). The runner host is treated as
  trusted but exposed, so it holds no API secrets, no SMTP credentials and no learner identity.
- ✅ **`forbidden_operation` was not detectable.** With no network, a socket call simply fails
  inside the process. The harness now installs non-removable Python audit hooks before importing
  learner code. The hooks only report; enforcement stays with the sandbox.
- ✅ **Limits per phase** are 10 s, applied to each of the two phases. Each phase gets a separate
  `/out` tmpfs. The sandbox runs with `PYTHONDONTWRITEBYTECODE` and pytest's cache disabled, so the
  read-only `/work` mount works.
- ✅ **Known limitations of the isolation model** are documented in runner protocol §8: gVisor is
  not a VM, results can be tampered with in-process, pass/fail on hidden tests is a side channel,
  micro-architectural side channels exist, host resources can be exhausted, and the `runc`
  exception applies in development.
- ✅ **Visible vs hidden tests.** Visible tests are *intentionally* shown to the learner (FR-022c).
  After D2 every test is visible. Only reference solutions must never be exposed: they are never
  bundled or mounted, and the repository must stay private.
- 💡 Before launch, run an external penetration test on the runner host. Re-pin gVisor monthly.

### 2.2 Incremental delivery

- ✅ **Increment 1 can never complete a module.** FR-037 requires a passed challenge, and
  challenges arrive in increment 2. This is correct behavior, not a bug. The docs now forbid any
  temporary relaxation, and require the UI to say "challenge available in a later release" rather
  than imply completion. Objectives are demonstrated by passed checks (US2 scenario 3). Competencies
  stay `in_progress` (data-model §2.12; plan increments table).
- ✅ **Missing derivation of objective status.** FR-040 needs it, and it is now defined.
- ✅ **Order inside increment 2.** The dashboard (US3) cannot show a demonstrated competency
  without challenge evaluation, so US4 now comes first within increment 2.
- ✅ **Account deletion validation (V7.5)** moved to increment 1, together with the rest of the
  account lifecycle.
- Each increment remains independently demonstrable through its quickstart scenarios.

### 2.3 Operational completeness (quickstart)

The quickstart now covers:

- ✅ The full tool list and how to install and verify gVisor.
- ✅ A table of environment variables per unit, with production rules.
- ✅ The development-only security exceptions, each refused when `APP_ENV=production`.
- ✅ Secret generation, the runner role and functions created by migrations, and API client
  generation with a drift check.
- ✅ A seed learner, and two ways to run the stack (all containers, or processes on the host).
- ✅ A health endpoint, plus new runner unit and load checks.
- ✅ New scenarios: printing the test directory, killing the runner mid-run, and runner
  unavailability within 30 s.

- ✅ **Cookies across origins.** `SameSite=Lax` cookies would break with the SPA on `:5173` and
  the API on `:8000`. Both now share one origin: a reverse proxy in production and the Vite proxy
  in development (research R2, plan).

### 2.4 Scope and complexity

No Kubernetes, Redis, microservices or model providers are needed. The modular monolith and the
PostgreSQL queue are kept.

- 💡 **CompetencyStatus materialization** is unnecessary at MVP scale: a few dozen items per
  learner. Computing it on read removes a class of consistency bugs. Keep the table only if
  dashboard latency requires it.
- 💡 **LastPosition** can be derived from `ContentView.last_viewed_at` instead of being stored.
- 💡 **schemathesis** contract fuzzing is optional for the MVP. The generated client drift check
  plus integration tests already enforce the contract.
- 💡 **Lab comparisons**: FR-029 only needs counts and unique elements. Avoid building a generic
  diff engine.

## 3. Minor improvements and consistency fixes

| Finding | Status |
|---------|--------|
| `content-schema.md` said bundles pre-render HTML with Shiki, but the build is in Python, Shiki is JavaScript, and the API returns Markdown | ✅ Rendering happens in the frontend; the bundle holds validated Markdown |
| FR-041 (review past knowledge checks) had no endpoint | ✅ `GET /knowledge-checks/{id}/attempts/history` |
| `AttemptResult` implied competencies are demonstrated by checks alone | ✅ Adds `objectives_demonstrated`; competencies stay empty until the challenge is passed |
| Account deletion said "tombstone or removed entirely" | ✅ Hard delete of all rows; queued jobs cancelled (FR-046) |
| Submission `cancelled` and `delayed` states were missing (account deletion, a queue over 5 min) | ✅ Added to data model and OpenAPI |
| FR-045b: unsent answers after session expiry | ✅ Kept client-side and re-sent after sign-in (data-model §2.6); code is autosaved in the workspace |
| Session lifetimes, token expiries, 12-character password, 30-day unverified cleanup were presented as facts | ✅ Marked *(assumption)* → D4 |
| Queue cap (200) and "delayed" threshold (5 min) | Engineering defaults, not product decisions; adjustable |
| Browser support "last 2 versions" | Assumption; confirm with D4 |

## 4. Decisions requiring product-owner approval

| ID | Decision | Options | Recommendation |
|----|----------|---------|----------------|
| ✅ D1 | **Accept that a determined learner can fake a challenge pass for their own account** by subverting the in-process test harness? | (a) Accept while there are no certificates or public credentials (they are out of scope). (b) Require out-of-process evaluation, where tests call learner code through a protocol; this adds significant cost and makes challenges harder to write | **Approved (a)**: revisit if certificates are introduced |
| ✅ D2 | **Hidden tests in the MVP?** | (a) Keep them, and keep the repository private or store hidden tests and solutions separately. (b) Drop hidden tests for the MVP (FR-022c says MAY): one phase per run, simpler runner, no leak risk | **Approved (b)**: no hidden tests for now; applied to spec FR-022c, runner protocol, content schema, data model, OpenAPI |
| ✅ D3 | **Confirm MVP scale** (research R10): ≤ 1,000 registered learners, ≤ 100 concurrent, peak of 10 simultaneous submissions | Confirm or adjust | **Approved as a working hypothesis**; re-validate with beta data |
| ✅ D4 | **Account and platform policies** | Session lifetime of 7 days idle / 30 days absolute; password of at least 12 characters; verification link 24 h; reset link 1 h; unverified accounts deleted after 30 days; last 2 browser versions | **Approved as initial values**; adjustable without a spec change |

## 5. Confirmed requirements vs assumptions

- **Confirmed by the spec or clarifications**:
  - Automatic isolated code evaluation; recorded lab traces; required accounts; English with i18n
    readiness; entry prerequisites; check plus challenge as evidence.
  - Every NFR target: 2 s, 1 s, 30 s, WCAG 2.2 AA, 360 px, 99.5% post-launch.
- **Engineering decisions (plan level, changeable without the product owner)**:
  - The stack (R1–R3, R5, R9); gVisor runtime; resource limits; lease and heartbeat timings; queue
    cap; delivery order inside increments.
- **Product-owner decisions (2026-11-06)**: D1 approved; D2 hidden tests removed for now; D3
  approved as a working hypothesis; D4 approved as initial values. Recorded in spec.md
  ("Resolved clarifications").
- **Still open by design**: hosting provider (R12), to be decided before the first public
  deployment.
