# Quickstart & Validation Guide: Agentic Academy MVP

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This guide describes how to run the MVP locally and the end-to-end scenarios that prove each user
story works. Commands refer to the structure in [plan.md](./plan.md#project-structure); they become
runnable as the corresponding tasks are implemented.

## Prerequisites

- Linux or macOS with Docker Engine ≥ 27 and Docker Compose v2.
- gVisor `runsc` registered as a Docker runtime (required for the runner; on macOS run the runner
  in a Linux VM). A development flag `RUNNER_RUNTIME=runc` exists **for local development only** and
  is refused when `APP_ENV=production`.
- Python 3.13 with `uv`; Node.js 24 LTS with `pnpm`.

## Setup

```bash
cp .env.example .env                   # no real secrets needed locally
docker compose up -d db mailpit        # PostgreSQL + local mail catcher
uv sync --project backend
uv run --project backend alembic upgrade head
uv run --project backend academy content validate
uv run --project backend academy content build --lang en
docker build -t academy-sandbox runner/sandbox-image
pnpm --dir frontend install
```

## Run

```bash
docker compose up api runner web       # web on http://localhost:5173, api on :8000
```

Emails (verification, password reset) appear in Mailpit at http://localhost:8025.

## Automated checks

| Check | Command | Proves |
|-------|---------|--------|
| Content validation | `uv run --project backend academy content validate` | FR-044, FR-048–FR-050 |
| Backend unit + integration | `uv run --project backend pytest` | progress rules, scoring, auth |
| API contract | `uv run --project backend pytest tests/contract` | API matches [contracts/openapi.yaml](./contracts/openapi.yaml) |
| Sandbox security suite | `uv run --project runner pytest tests/security` | FR-022a, SC-011 |
| Frontend unit | `pnpm --dir frontend test` | components, i18n |
| End-to-end + accessibility | `pnpm --dir frontend e2e` | user stories below, NFR-001, SC-007 |

## Validation scenarios (map to spec user stories)

### V1 — Study a module (US1)
1. Open `/catalog` signed out → introductory path visible with level, objectives, prerequisites,
   estimated effort; planned paths marked "not yet available" (US6).
2. Sign up, open the verification link from Mailpit, sign in.
3. Open Module 1 → objectives, entry prerequisites self-assessment, lessons, highlighted code with
   copy button, diagram with text alternative, maturity labels, references, prev/next navigation.
4. Resize to 360 px → no horizontal page scroll; code blocks scroll internally (NFR-002).
**Expected**: all elements present; axe reports no critical violations.

### V2 — Knowledge check (US2)
1. Start Module 1 check → threshold (70%) and objectives shown.
2. Answer with 2 deliberate mistakes → each answer shows correct/incorrect + explanation + lesson link.
3. Submit with < 70% → "not passed", weak objectives listed; retry; submit ≥ 70% → passed; best
   score retained.
4. Disconnect network before submitting, reconnect, submit → single result recorded.

### V3 — Dashboard & persistence (US3)
1. After V2, sign out, sign in from a different browser profile → dashboard shows module "in
   progress" (challenge pending), competencies not yet demonstrated, "continue" to the last lesson.
2. Competency view lists each competency with level, status and evidence.

### V4 — Challenge (US4)
1. Open Module 1 challenge → scenario, problem, expected outcome, instructions, criteria, hints.
2. Reveal one hint → hint count = 1.
3. Run visible tests on starter code → failing criteria with messages.
4. Submit an infinite loop → `stopped (timeout)` within limit; submit code opening a socket →
   `stopped (forbidden_operation)`; platform unaffected.
5. Submit a correct solution → all mandatory criteria met; module completed; competencies
   demonstrated; reference explanation shown; previous submissions reviewable.
**Expected**: 95% of results within 30 s (measured with the load script `runner/tests/load`).

### V5 — Laboratory (US5)
1. Open scenario "research agent with tools" → task, tools with permissions, pattern, objective.
2. Step forward/back; each element labeled by kind; decision summaries labeled
   "educational explanation"; state shown per element.
3. Compare "fixed workflow" vs "agent loop" → counts and unique elements highlighted.
4. Open the prompt-injection variant → failing element highlighted with risk and mitigation.
5. Reach the destructive action → approval prompt; choose reject → rejected branch replayed.
**Expected**: no network calls to model providers (verify in browser network panel).

### V6 — Content governance (US7)
1. Change a question without bumping `version` → `content validate` fails with a clear message.
2. Bump version, mark an example deprecated → notice visible in the lesson; learners who passed the
   previous version keep their demonstrated competency.
3. Add a module prerequisite that creates a cycle → validation fails.

### V7 — Account lifecycle & resilience
1. Password reset flow via Mailpit → all sessions revoked.
2. Let the session expire while editing challenge code → after sign-in, code is restored.
3. Stop the runner → submitting shows a clear "evaluation unavailable" state while lessons, checks
   and dashboard keep working (SC-008).
4. Delete account → confirmation required; sign-in no longer possible; data removed.
