# Data Model: Agentic Academy MVP

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-06

The model has two parts:

- **Content model** (read-only at runtime): authored as files under `content/`, validated and built
  into a versioned content bundle (research R4). File formats: [contracts/content-schema.md](./contracts/content-schema.md).
- **Learner data model** (read/write): stored in PostgreSQL. It references content only by stable
  `id` and `version`, never by text, so content can be translated or updated without migrating
  learner data (FR-051, FR-055).

---

## 1. Content model

All content items share: `id` (kebab-case, globally unique per type, language-independent),
`version` (SemVer), `lang` (BCP 47, `en` in the MVP), `last_reviewed` (ISO date),
`deprecation` (optional, see 1.10).

### 1.1 Competency

| Field | Type | Rules |
|-------|------|-------|
| id | string | unique |
| title, description | text | required |
| level | enum `foundational` \| `intermediate` \| `advanced` | required |

### 1.2 LearningPath

| Field | Type | Rules |
|-------|------|-------|
| id, version, lang, last_reviewed | — | common |
| title, summary | text | required |
| level | enum (as Competency) | required |
| status | enum `available` \| `planned` | `planned` paths may omit modules |
| order | int | position in the curriculum roadmap (FR-002) |
| objectives | list of text | ≥ 1 |
| entry_prerequisites | list of {label, resource_url} | FR-003a/FR-003b self-assessment |
| prerequisite_paths | list of path ids | must exist; no cycles |
| competencies | list of competency ids | derived = union of its modules' competencies; validated |
| estimated_hours | number | > 0 |
| modules | ordered list of module ids | ≥ 1 if `available` |

### 1.3 Module

| Field | Type | Rules |
|-------|------|-------|
| id, version, lang, last_reviewed | — | common |
| path_id | path id | must exist |
| order | int | unique within path |
| title, summary | text | required |
| objectives | list of LearningObjective | ≥ 1 |
| prerequisites | list of module or competency ids | must exist; must precede in order; no cycles (FR-050) |
| competencies | list of competency ids | ≥ 1 |
| lessons | ordered list of Lesson | ≥ 1 |
| knowledge_check | KnowledgeCheck id | exactly 1 (FR-007) |
| challenges | list of Challenge ids | ≥ 1 (FR-008) |
| lab_scenarios | list of LabScenario ids | ≥ 0 (guided practice only) |
| references | list of {title, url, vendor?} | ≥ 1 |
| multi_agent | bool | if true, module order must follow all single-agent modules (FR-005) |

### 1.4 LearningObjective

| Field | Type | Rules |
|-------|------|-------|
| id | string | unique within module |
| statement | text | observable verb ("Explain…", "Implement…") |
| competencies | list of competency ids | ≥ 1, subset of module competencies (FR-044) |

### 1.5 Lesson

| Field | Type | Rules |
|-------|------|-------|
| id | string | unique within module |
| title | text | required |
| body | Markdown | may contain directives: `:::maturity{level=established\|emerging\|experimental}`, `:::vendor{name=…}` with limitations, `:::deprecated{ref=…}`, code blocks with language + optional annotations, diagrams (Mermaid or image) with mandatory `alt` text (FR-010, FR-011, FR-014) |
| anchors | derived | section anchors used by feedback links (FR-018) |

### 1.6 KnowledgeCheck and Question

KnowledgeCheck: `id, version, module_id, pass_threshold` (0–1, default 0.70, FR-017),
`questions` (≥ 5, FR-016).

| Question field | Type | Rules |
|----------------|------|-------|
| id | string | unique within check |
| type | enum `single_choice` \| `multiple_choice` \| `ordering` \| `matching` | FR-016 |
| prompt | Markdown | scenario-based allowed (FR-020) |
| options / items / pairs | per type | ≥ 2 options; correct answer(s) defined |
| explanation | Markdown | required, per option where applicable (FR-018) |
| objective_id | objective id | required (FR-044) |
| lesson_anchor | lesson id + anchor | must resolve (FR-018) |

Scoring: each question scores 0 or 1 (multiple choice: all and only correct options; ordering:
exact order; matching: all pairs). Score = correct / total.

### 1.7 Challenge

| Field | Type | Rules |
|-------|------|-------|
| id, version, lang, last_reviewed | — | common |
| module_id | module id | must exist |
| difficulty_rank | int | strictly increasing along the path (FR-025) |
| scenario, problem, expected_outcome, instructions | Markdown | required (FR-021) |
| criteria | list of {id, description, mandatory: bool, tests: list of test ids} | ≥ 1 mandatory; every test belongs to exactly one criterion |
| hints | ordered list of Markdown | ≥ 2, general → specific (FR-021) |
| reference_explanation | Markdown | shown only after the challenge is passed |
| competencies | list of competency ids | ≥ 1 |
| starter_files | file tree | editable by learner |
| visible_tests, hidden_tests | file trees | hidden tests never shipped to the frontend (R6) |
| limits | {cpu_seconds, memory_mb, wall_seconds} | ≤ platform maximums (R6) |

### 1.8 LabScenario

See [contracts/lab-trace.schema.json](./contracts/lab-trace.schema.json).

| Field | Type | Rules |
|-------|------|-------|
| id, version, lang, last_reviewed | — | common |
| title, task, objective | text | required |
| tools | list of {name, description, permission: `read` \| `write` \| `destructive`} | FR-028 |
| variants | list of Variant (≥ 1) | Variant: {id, label, orchestration_pattern, recording} |
| comparisons | list of {left_variant, right_variant} | FR-029 |
| failure_cases | list of {element_id, risk, mitigation} | FR-031 |
| recorded_with | {model, framework, date} | per recording (FR-033a) |

Trace element kinds (FR-027): `execution_event`, `tool_call`, `state_transition`,
`decision_summary`. A `tool_call` on a `destructive` tool MUST be preceded by an `approval_request`
execution event and the variant set MUST contain both an approved and a rejected continuation
(FR-030).

### 1.9 Content bundle

Build output: `{bundle_version, built_at, lang, items}` (public part) plus a private part (hidden
tests) for the runner only. Lesson and feedback bodies stay as validated Markdown; rendering and
sanitization happen in the frontend (R2). New learner activity always uses the **current** bundle,
but every published bundle is kept (immutable) so that attempts and submissions started on an older
version are scored against that version (spec edge case "content updated mid-module", FR-051).
`bundle_version` is recorded on every learner result for traceability.

### 1.10 DeprecationNotice

`{target (api | framework | model | example id), reason, replacement?, since (date)}` — rendered
wherever the target is referenced (FR-049).

---

## 2. Learner data model (PostgreSQL)

### 2.1 Account

| Field | Type | Rules |
|-------|------|-------|
| id | UUID | PK |
| email | citext | unique, normalized lowercase |
| password_hash | text | Argon2id; never returned or logged |
| status | enum `pending_verification` \| `active` \| `deleted` | see transitions |
| email_verified_at | timestamptz | null until verified |
| locale | text | default `en` |
| created_at, updated_at | timestamptz | |

Transitions: `pending_verification → active` (verify email) · `active|pending_verification →
deleted` (learner request, FR-045a, FR-046): the account row, sessions, tokens and all progress
rows (2.4–2.12) are hard-deleted in one transaction; queued jobs of the account are cancelled.
Unverified accounts are deleted after 30 days *(assumption)*.

### 2.2 Session

`id (UUID), account_id (FK), token_hash, created_at, last_seen_at, expires_at, revoked_at`.
Idle timeout 7 days, absolute 30 days *(assumption, see review D4)*; all sessions revoked on
password reset and account deletion; sign-out revokes the current session.

### 2.3 OneTimeToken

`id, account_id, purpose (verify_email | reset_password), token_hash, expires_at, used_at`.
Single use; verify expires in 24 h, reset in 1 h *(assumption)*.

### 2.4 ContentView

`account_id, content_type (module | lesson), content_id, content_version, first_viewed_at,
last_viewed_at`. PK (account_id, content_type, content_id). Feeds "in progress" and
"continue where you left off" (FR-035, FR-038).

### 2.5 LastPosition

`account_id (PK), path_id, module_id, lesson_id?, updated_at`. Most recent activity wins
(multi-device edge case). May be derived from ContentView instead of stored (review R-S2).

### 2.6 AssessmentAttempt

| Field | Type | Rules |
|-------|------|-------|
| id | UUID | PK |
| account_id | FK | |
| knowledge_check_id, content_version, bundle_version | text | |
| status | enum `in_progress` \| `submitted` | |
| answers | JSONB {question_id: answer} | saved as drafts while `in_progress` (FR-045b) |
| question_order | JSONB | randomized per attempt |
| score | numeric(4,3) | set on submit |
| passed | bool | score ≥ threshold of that version |
| per_objective | JSONB {objective_id: correct/total} | for weak objectives (FR-019) |
| started_at, submitted_at | timestamptz | |

Best result per (account, knowledge_check) = max score among submitted attempts (FR-019).
An attempt is scored with the knowledge-check version it started on (`content_version`,
`bundle_version`), even if a newer version was published meanwhile.
Unsent answers are also kept client-side and re-sent after re-authentication (FR-045b).
Idempotent submit: a client-generated `attempt_id` prevents duplicates (connectivity edge case).

### 2.7 ChallengeWorkspace

`account_id, challenge_id, files (JSONB path→content, max 256 KB total), updated_at`.
Autosaved draft code; survives session expiry (FR-045b).

### 2.8 ChallengeSubmission

| Field | Type | Rules |
|-------|------|-------|
| id | UUID | PK; client-provided idempotency key |
| account_id | FK | |
| challenge_id, content_version, bundle_version | text | |
| kind | enum `visible_run` \| `submission` | visible runs never complete a challenge (FR-022c) |
| attempt_number | int | per account+challenge, submissions only |
| files | JSONB | snapshot of code |
| status | enum `queued` \| `running` \| `passed` \| `failed` \| `stopped` \| `error` | see transitions |
| stop_reason | enum `timeout` \| `memory` \| `output_limit` \| `forbidden_operation` \| null | FR-022a |
| criteria_results | JSONB [{criterion_id, met, tests:[{id, outcome, message, hidden}]}] | FR-022; `message` is always null for hidden tests |
| output_excerpt | text | ≤ 64 KB, secrets scrubbed (FR-047) |
| hints_used | int | snapshot at submission time (FR-024) |
| queued_at, started_at, finished_at | timestamptz | |

Transitions: `queued → running → passed | failed | stopped` · `running → queued` (lease expired,
infrastructure retry) · `queued|running → error` (after 3 infrastructure attempts; learner may
resubmit without counting an attempt) · `queued → cancelled` (account deleted) ·
`passed` = all mandatory criteria met in phase V and phase H (runner protocol §2).
`attempt_number` is assigned when the submission reaches a final state that counts as an attempt.

### 2.9 SubmissionJob (queue)

`submission_id (PK, FK), available_at, worker_id, lease_id, lease_expires_at, infra_attempts`.
Accessed by the runner only through the functions in
[runner-protocol §1](./contracts/runner-protocol.md): claim with `FOR UPDATE SKIP LOCKED`, 60 s
lease extended by heartbeat, fenced completion by `lease_id`, max 3 infrastructure attempts then
submission → `error`.

### 2.9a RunnerWorker

`worker_id (PK), capacity, started_at, last_heartbeat_at`. Evaluation is available ⇔ a heartbeat is
newer than 30 s; used by the API to reject submissions with `evaluation_unavailable`.

### 2.10 HintUsage

`account_id, challenge_id, hints_revealed (int), updated_at` — hints revealed in order (FR-024).

### 2.11 LabVisit

`account_id, scenario_id, variant_id, first_viewed_at, last_viewed_at` — recorded as exploration
only; never evidence (FR-008, FR-036).

### 2.12 CompetencyStatus (derived, materialized)

`account_id, competency_id, status (not_started | in_progress | demonstrated), demonstrated_at,
evidence (JSONB [{type: knowledge_check | challenge, id, version, result_id}])`.

Derivation rules (FR-036, FR-037, FR-040):

- **Objective demonstrated** ⇔ the knowledge check of its module has been passed (US2 scenario 3).
  Objectives are listed as pending (FR-040) until then. Objective status is derived, not stored.

- `demonstrated` ⇔ every knowledge check and every challenge mapped to the competency (through
  their objectives/competencies) has a passed result in any version.
- `in_progress` ⇔ not demonstrated and at least one related content view, attempt or submission.
- `not_started` otherwise.
- Once `demonstrated`, never reverts, even if content changes (FR-051).

Module completed ⇔ its knowledge check passed AND all its challenges passed. Path completed ⇔ all
modules completed. Both are computed, not stored.

**Increments without challenge evaluation** (plan increment 1): the rules above are not relaxed.
A passed knowledge check demonstrates objectives but never a competency or module completion; the
UI shows the module as "in progress — challenge available in a later release" instead of implying
completion. No temporary rule may mark competencies demonstrated.

### 2.13 Path reset (FR-043)

Deleting a learner's progress for a path removes rows in 2.4–2.12 scoped to that path's content ids,
after explicit confirmation; recomputes CompetencyStatus.

---

## 3. Relationships overview

```text
Competency ◄── LearningObjective ◄── Module ──► LearningPath
     ▲                 ▲              │ │ │
     │                 │              │ │ └──► LabScenario ──► Variant ──► Trace elements
     │                 └── Question ◄─┘ │
     │                     (KnowledgeCheck)
     └──────────────── Challenge ◄──────┘

Account ──► Session, OneTimeToken
Account ──► ContentView, LastPosition, AssessmentAttempt, ChallengeWorkspace,
            ChallengeSubmission ──► SubmissionJob, HintUsage, LabVisit, CompetencyStatus
```
