---

description: "Task list for the Agentic Academy MVP"
---

# Tasks: Agentic Academy MVP

**Input**: Design documents from `/specs/001-agentic-academy-mvp/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md),
[architecture-review.md](./architecture-review.md)

**Tests**: Included. NFR-011 and Constitution IV require automated tests for critical workflows
(studying a module, taking a knowledge check, submitting a challenge, saving and viewing progress)
and regression scenarios; the sandbox requires a security suite (SC-011). Tests are written before
the implementation they cover and must fail first.

**Architecture decisions applied** (see [architecture-review.md](./architecture-review.md)):
D1 — in-process tampering of a learner's own result is an accepted residual risk while no
certificates exist; evaluation is **not** tamper-proof and no task or document may claim it is.
D2 — no hidden tests in the MVP: every challenge test is visible; reference solutions are used only
by the content validator. Trust boundaries: [runner-protocol §0](./contracts/runner-protocol.md).

**Organization**: Phases follow the delivery increments in [plan.md](./plan.md#delivery-increments),
which reorder P2/P3 stories by dependency: Increment 1 = US1, US2, US6; Increment 2 = US4, then US3;
Increment 3 = US5, US7; then curriculum completion and hardening.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story from spec.md (US1–US7)
- Paths follow [plan.md › Project Structure](./plan.md#project-structure): `backend/`, `runner/`,
  `frontend/`, `content/`, `docs/`

## Global rules for every task

- Follow the contracts exactly: [openapi.yaml](./contracts/openapi.yaml),
  [content-schema.md](./contracts/content-schema.md),
  [lab-trace.schema.json](./contracts/lab-trace.schema.json),
  [runner-protocol.md](./contracts/runner-protocol.md).
- Every backend error is an RFC 9457 problem with a stable `code`; never log passwords, tokens,
  session ids, emails or learner code (FR-047).
- Every migration adds `ON DELETE CASCADE` from learner tables to `account(id)` so account deletion
  removes all learner data in one transaction (FR-046).
- Every user-visible string goes through react-i18next (`frontend/src/i18n/en/*.json`) (FR-055).
- Every interactive UI element is keyboard operable with visible focus and accessible name
  (NFR-001).
- No task implements, distributes or mounts hidden tests (D2). Reference solutions (`solution/`)
  never leave the content validator: they are not bundled, served or mounted in learner runs.
- Everything produced inside the sandbox (stdout, stderr, `/out/result.json`) is untrusted input
  (runner-protocol §0, §5). Code comments, docs and UI must describe result validation as
  integrity *checks*, never as tamper-proof evaluation (D1).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository skeleton, toolchains and local stack

- [X] T001 Create the directory layout from plan.md (`backend/src/academy/{shared,db,auth,content,catalog,assessments,challenges,lab,progress}`, `backend/tests/{unit,integration,contract,fixtures}`, `runner/src/academy_runner`, `runner/sandbox-image/academy_sim`, `runner/tests/{unit,security,load}`, `frontend/src/{app,api,i18n/en,components,features}`, `frontend/tests/{unit,e2e}`, `content/en/{paths,lab}`, `docs/adr`) with `.gitkeep` files where empty
- [X] T002 Initialize the backend project with uv in `backend/pyproject.toml` (Python 3.13; deps: fastapi, uvicorn[standard], pydantic>=2, pydantic-settings, sqlalchemy>=2, alembic, psycopg[binary]>=3, argon2-cffi, pyyaml, markdown-it-py, jsonschema; dev: pytest, httpx, ruff, mypy, types-PyYAML) and a console script `academy = academy.cli:main`
- [X] T003 [P] Initialize the runner project with uv in `runner/pyproject.toml` (Python 3.13; deps: psycopg[binary]>=3, docker, pydantic>=2, pydantic-settings; dev: pytest, ruff, mypy) and a console script `academy-runner = academy_runner.main:main`
- [X] T004 [P] Initialize the frontend with pnpm + Vite React TypeScript template in `frontend/package.json` (deps: react@19, react-dom@19, react-router, @tanstack/react-query, react-i18next, i18next, shiki, @codemirror/* + @uiw/react-codemirror, mermaid, markdown-it, dompurify; dev: typescript, vitest, @testing-library/react, @testing-library/user-event, jsdom, @playwright/test, @axe-core/playwright, openapi-typescript, eslint, prettier) with scripts `dev`, `build`, `test`, `e2e`, `lint`, `generate:api`
- [X] T005 [P] Configure ruff and mypy (strict for `academy.auth`, `academy.assessments`, `academy.challenges`, `academy.progress`, `academy.content`, `academy_runner`) in `backend/pyproject.toml` and `runner/pyproject.toml`
- [X] T006 [P] Configure TypeScript strict mode, ESLint and Prettier in `frontend/tsconfig.json`, `frontend/eslint.config.js`, `frontend/.prettierrc`
- [X] T007 Configure the Vite dev proxy so `/api` is forwarded to `http://localhost:8000` (same-origin cookies, research R2) in `frontend/vite.config.ts`
- [X] T008 Create `docker-compose.yml` with services `db` (postgres:17, healthcheck), `mailpit` (ports 1025/8025), `api`, `runner` (mounts `/var/run/docker.sock`, runtime configured by `RUNNER_RUNTIME`), `web`; mount `./dist/content` read-only into `api` and `runner`
- [X] T009 [P] Create `.env.example` with every variable from quickstart.md "Environment variables" and dev defaults, and a `Makefile` with targets `dev-secrets` (writes a random 32-byte `SESSION_SECRET` into `.env`), `setup`, `up`, `test`, `e2e`
- [X] T010 [P] Create backend and runner Dockerfiles in `backend/Dockerfile` and `runner/Dockerfile`, and a static web image in `frontend/Dockerfile` (build + serve `dist/` with `/api` reverse-proxied to the API)
- [X] T011 [P] Write ADRs 0001–0006 (modular monolith; PostgreSQL as queue; content as code; first-party auth with server sessions; gVisor runner and trust boundaries, including the accepted in-process tampering risk D1 and the removal of hidden tests D2; recorded lab traces, no runtime model calls) from research.md and architecture-review.md in `docs/adr/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend, content pipeline, accounts, test harness library and frontend shell
used by every story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend core

- [X] T012 Implement settings with pydantic-settings in `backend/src/academy/config.py` (all API variables from quickstart.md); when `APP_ENV=production` refuse to start if `COOKIE_SECURE` is not true, `RATE_LIMIT_ENABLED` is not true or `EMAIL_BACKEND=console`; log a warning for each development exception otherwise
- [X] T013 [P] Implement RFC 9457 problem details (`type, title, status, code, detail`) and exception handlers in `backend/src/academy/shared/errors.py`
- [X] T014 [P] Implement structured JSON logging with a scrubbing filter that redacts emails, tokens, cookies, `password` fields and secret-like patterns in `backend/src/academy/shared/logging.py`
- [X] T015 Implement SQLAlchemy engine/session and declarative base in `backend/src/academy/db/session.py` and initialize Alembic in `backend/alembic/` (env reads `DATABASE_URL`)
- [X] T016 Implement the app factory mounting routers under `/api/v1` and `GET /api/v1/health` returning `database`, `content_bundle_version` and `evaluation` (`unavailable` until T087 adds runner heartbeats) in `backend/src/academy/main.py` and `backend/src/academy/shared/health.py`
- [X] T017 Implement the top-level CLI dispatcher (`academy content …`, `academy dev seed`, `academy maintenance …`) in `backend/src/academy/cli.py`

### Content pipeline (contracts/content-schema.md)

- [X] T018 [P] Write validator test fixtures (one valid mini-curriculum plus one invalid tree per rule 1–8 and 10 of content-schema.md) in `backend/tests/fixtures/content/`
- [X] T019 [P] Write failing unit tests for every validation rule in `backend/tests/unit/content/test_validate.py` and for the loader in `backend/tests/unit/content/test_loader.py`
- [X] T020 Implement Pydantic content schemas per data-model.md §1 in `backend/src/academy/content/schemas.py`: common header (`id` kebab-case, `version` SemVer, `lang`, `last_reviewed` ISO date, optional `deprecation`), Competency (`level` enum `foundational | intermediate | advanced`), LearningPath (`status` enum `available | planned`, `estimated_hours` > 0, ≥ 1 module if `available`), Module (≥ 1 objective, ≥ 1 lesson, exactly 1 knowledge check, ≥ 1 challenge, ≥ 1 reference, `multi_agent` bool), LearningObjective (≥ 1 competency), KnowledgeCheck (`pass_threshold` 0–1 default 0.70, ≥ 5 questions), Question (`type` enum `single_choice | multiple_choice | ordering | matching`, required `explanation`, `objective_id`, `lesson_anchor`), Challenge (`difficulty_rank` int, ≥ 1 mandatory criterion, ≥ 2 hints, `limits` ≤ platform maximums 10 s wall / 256 MB, `tests` all visible to the learner, `solution` validator-only; no hidden-test field, D2), DeprecationNotice
- [X] T021 Implement the content loader (reads `content/competencies.yaml` and `content/<lang>/…`, parses lesson front matter and Markdown with markdown-it-py, extracts directives `:::maturity`, `:::vendor`, `:::deprecated`, code blocks with language/title/annotate, diagrams with mandatory `alt`, and `{#anchor}` heading anchors) in `backend/src/academy/content/loader.py`
- [X] T022 Implement validation rules 1–8 and 10 of content-schema.md (schemas, references, acyclic prerequisites in path order, multi-agent ordering, module completeness, competency traceability, strictly increasing `difficulty_rank`, criteria/test mapping, lab scenarios against `contracts/lab-trace.schema.json`, secret scan) with a machine-readable report and non-zero exit in `backend/src/academy/content/validate.py`
- [X] T023 Implement rule 7 solution checks: run each challenge's `solution/` against its `tests/` with pytest in a subprocess with `academy_sim` installed (trusted maintainer code, no sandbox) and assert the starter code fails at least one mandatory criterion, behind `academy content validate --run-solutions` in `backend/src/academy/content/solutions.py`
- [X] T024 Implement `academy content build --lang en --out dist/content` producing `dist/content/en/bundle-<bundle_version>.json` (Markdown bodies, visible tests, starter files; never `solution/`; no hidden tests, D2), never overwriting an existing bundle file, in `backend/src/academy/content/build.py`
- [X] T025 Implement the runtime content registry that loads every bundle in `CONTENT_DIR`, exposes the current bundle per language and resolves items by `(id, bundle_version)` in `backend/src/academy/content/registry.py`
- [X] T026 Create the competency catalogue for the introductory path in `content/competencies.yaml` and the available path skeleton `content/en/paths/foundations-of-agentic-ai-engineering/path.yaml` (level `foundational`, objectives, `entry_prerequisites` exactly as FR-003a with a resource URL each, `estimated_hours`, module order: 01-llm-foundations, 02-agent-fundamentals, 03-tools-and-function-calling, 04-memory-and-state, 05-evaluation-observability-and-risks)

### Challenge test library (needed to author challenge content)

- [X] T027 [P] Write failing unit tests for `ScriptedModel`, `FakeTool`, `ApprovalGate`, `TraceRecorder` and assertion helpers in `runner/sandbox-image/academy_sim/tests/test_sim.py`
- [X] T028 Implement the vendor-neutral `academy_sim` package (runner-protocol §9: `ModelClient` protocol, `ScriptedModel(turns)`, `FakeTool(name, permission, handler)` enforcing `read | write | destructive`, `ApprovalGate(decisions)`, `TraceRecorder` producing the four element kinds, `assert_tool_called`) as an installable package in `runner/sandbox-image/academy_sim/`

### Accounts (FR-045, FR-045a–b; research R5)

- [X] T029 Create Alembic migration `0001_accounts` for `account` (`id` UUID PK, `email` citext unique, `password_hash`, `status` enum `pending_verification | active | deleted`, `email_verified_at`, `locale` default `en`, timestamps), `session` (`token_hash`, `created_at`, `last_seen_at`, `expires_at`, `revoked_at`) and `one_time_token` (`purpose` enum `verify_email | reset_password`, `token_hash`, `expires_at`, `used_at`) in `backend/alembic/versions/0001_accounts.py`
- [X] T030 [P] Implement ORM models for Account, Session, OneTimeToken in `backend/src/academy/auth/models.py`
- [X] T031 [P] Write failing integration tests for sign-up (identical 202 for existing email), verification, sign-in (403 `email_not_verified`), sign-out, password reset (revokes all sessions), CSRF rejection, rate limiting and account deletion in `backend/tests/integration/auth/test_auth_flow.py`
- [X] T032 [P] Implement Argon2id hashing with password length 12–128 in `backend/src/academy/auth/passwords.py`
- [X] T033 Implement opaque session tokens stored hashed, cookies `aa_session` (`HttpOnly; Secure; SameSite=Lax`) and `aa_csrf`, idle timeout 7 days and absolute 30 days, and double-submit CSRF middleware requiring `X-CSRF-Token` on state-changing requests in `backend/src/academy/auth/sessions.py`
- [X] T034 [P] Implement the `EmailSender` port with SMTP and console adapters and plain-text templates for verification and reset links built from `PUBLIC_BASE_URL` in `backend/src/academy/auth/email.py`
- [X] T035 [P] Implement per-IP and per-email rate limiting for sign-up, sign-in and reset endpoints (in-process token bucket, disabled only by `RATE_LIMIT_ENABLED=false`) in `backend/src/academy/auth/rate_limit.py`
- [X] T036 Implement the auth service: sign-up (no account enumeration), single-use tokens (verify 24 h, reset 1 h), sign-in, sign-out (current session), reset confirm (revoke all sessions), delete account with body `confirm: "DELETE"` hard-deleting the account and all cascaded rows in one transaction, in `backend/src/academy/auth/service.py`
- [X] T037 Implement auth routes `/auth/sign-up`, `/auth/verify-email`, `/auth/sign-in`, `/auth/sign-out`, `/auth/password-reset/request`, `/auth/password-reset/confirm`, `GET /me`, `DELETE /me` and the `current_learner` dependency in `backend/src/academy/auth/router.py` and `backend/src/academy/auth/dependencies.py`
- [X] T038 [P] Implement `academy maintenance purge-unverified` deleting accounts with `status=pending_verification` older than 30 days in `backend/src/academy/auth/maintenance.py`
- [X] T039 [P] Implement `academy dev seed` creating a verified learner `demo@example.com` (refused when `APP_ENV=production`) in `backend/src/academy/shared/seed.py`

### Frontend shell

- [X] T040 Implement routing, layout (header with progress entry point, skip link, consistent module navigation slot), error boundary and route-level code splitting in `frontend/src/app/`
- [X] T041 [P] Implement shared state components `Loading`, `EmptyState`, `ErrorState` (with retry), `OfflineBanner` (FR-052) in `frontend/src/components/states/`
- [X] T042 [P] Configure react-i18next with `en` resources and `Intl` date/number helpers using the active locale in `frontend/src/i18n/index.ts` and `frontend/src/i18n/en/common.json`
- [X] T043 Implement `generate:api` (openapi-typescript from `specs/001-agentic-academy-mvp/contracts/openapi.yaml` into `frontend/src/api/schema.ts`) and a typed fetch client that sends credentials, adds `X-CSRF-Token` from the `aa_csrf` cookie, parses problem details and emits a re-authentication event on 401 in `frontend/src/api/client.ts`
- [X] T044 [P] Implement a local draft store (localStorage wrapped in try/catch) that keeps unsent answers and code per learner and item and replays them after re-authentication (FR-045b) in `frontend/src/app/drafts.ts`
- [X] T045 [P] Implement content rendering components: `Markdown` (markdown-it → DOMPurify-sanitized HTML, heading anchors), `CodeBlock` (Shiki, language label, copy button, annotations, internal horizontal scroll at 360 px), `Diagram` (Mermaid rendered client-side with the `alt` text exposed to assistive technology), `MaturityBadge`, `VendorNote`, `DeprecationNotice` in `frontend/src/components/content/`
- [X] T046 Implement auth pages: sign up, check-your-email, verify, sign in, forgot password, reset password, account settings with irreversible-deletion confirmation in `frontend/src/features/auth/`
- [X] T047 [P] Configure Playwright (Chromium, desktop and 360 px projects, `--trace off` by default) with an axe helper failing on critical violations and a fixture that signs in the seeded learner in `frontend/playwright.config.ts` and `frontend/tests/e2e/fixtures.ts`

**Checkpoint**: Foundation ready — content validates and builds, learners can create accounts and
sign in, the frontend shell renders.

---

## Phase 3: User Story 1 — Study a module of the introductory learning path (Priority: P1) 🎯 MVP · Increment 1

**Goal**: A signed-in learner studies Module 1: objectives, prerequisites, lessons with explanations,
code examples, diagrams, maturity labels, vendor notes and references, with consistent navigation.

**Independent Test**: Signed in, open the introductory path and Module 1 and verify all elements are
present and readable at desktop and 360 px widths, without challenges, laboratory or dashboard
(quickstart V1).

### Tests for User Story 1

- [X] T048 [P] [US1] Write failing integration tests for `GET /paths/{pathId}` (public, module list; module `status` only when signed in) and `GET /modules/{moduleId}` (401 when signed out, records a ContentView, returns `missing_prerequisites`, `previous_module_id`, `next_module_id`) in `backend/tests/integration/catalog/test_module_api.py`
- [X] T049 [P] [US1] Write a failing end-to-end test for quickstart V1 steps 2–4 (sign in, path overview, Module 1 elements, 360 px no horizontal page scroll, axe clean) in `frontend/tests/e2e/us1-study-module.spec.ts`

### Implementation for User Story 1

- [X] T050 [US1] Create migration `0002_content_view` for `content_view` (`account_id`, `content_type` enum `module | lesson`, `content_id`, `content_version`, `first_viewed_at`, `last_viewed_at`; PK `(account_id, content_type, content_id)`) in `backend/alembic/versions/0002_content_view.py`
- [X] T051 [P] [US1] Implement the ContentView model and `record_view` / `last_position` (derived from the most recent `last_viewed_at`, replacing a stored LastPosition table per architecture-review §2.4) in `backend/src/academy/progress/views.py`
- [X] T052 [US1] Implement the catalog service: path detail, module detail with lessons, references, previous/next module, and non-blocking `missing_prerequisites` (FR-006) computed from the progress derivation in `backend/src/academy/catalog/service.py`
- [X] T053 [US1] Implement routes `GET /paths/{pathId}` (public) and `GET /modules/{moduleId}` (requires account) per openapi.yaml in `backend/src/academy/catalog/router.py`
- [X] T054 [P] [US1] Implement the path overview page (title, level, objectives, entry-prerequisite self-assessment checklist stored only locally and never counted as evidence per FR-003b, expected competencies, estimated effort, ordered modules) in `frontend/src/features/catalog/PathPage.tsx`
- [X] T055 [US1] Implement the module page (objectives, prerequisite warning with links, lessons rendered with T045 components, references with vendor labels, previous/next/back-to-path navigation, reading mode with ≤ 90 characters per line and no unrelated elements per NFR-012) in `frontend/src/features/module/ModulePage.tsx` and `frontend/src/features/module/LessonView.tsx`
- [X] T056 [US1] Author Module 1 "LLM foundations" in `content/en/paths/foundations-of-agentic-ai-engineering/modules/01-llm-foundations/` with `module.yaml`, lessons covering tokens, context windows, sampling, structured output and limitations (hallucination) with "why" explanations, maturity labels, vendor notes with limitations, ≥ 2 Python code examples, ≥ 1 Mermaid diagram with alt text and reference links; plus `knowledge-check.yaml` (≥ 5 questions across the four types, each with explanation, objective and lesson anchor) and one challenge (`challenge.yaml`, `starter/`, `tests/` using `academy_sim` — all visible to the learner, D2 —, `solution/` for validation only, `difficulty_rank: 1`, ≥ 2 hints) passing `academy content validate --run-solutions`

**Checkpoint**: US1 works on its own.

---

## Phase 4: User Story 2 — Validate understanding with knowledge checks (Priority: P1) · Increment 1

**Goal**: Learners take a module's knowledge check with per-question feedback, threshold, weak
objectives, retries and best-score retention.

**Independent Test**: Quickstart V2: answer with mistakes, see explanations and lesson links, fail,
retry, pass; a network interruption does not duplicate results.

### Tests for User Story 2

- [X] T057 [P] [US2] Write failing unit tests for scoring (0/1 per question; multiple choice = all and only correct options; ordering = exact order; matching = all pairs; score = correct/total; passed ⇔ score ≥ threshold of the attempt's version; per-objective ratios) in `backend/tests/unit/assessments/test_scoring.py`
- [X] T058 [P] [US2] Write failing integration tests for start/resume attempt (idempotent `attempt_id`), save answer with feedback, submit (422 `unanswered_questions` unless `confirm_unanswered`), idempotent re-submit, best score, attempt history and scoring against the version the attempt started on after a newer bundle is published in `backend/tests/integration/assessments/test_attempts.py`
- [X] T059 [P] [US2] Write a failing end-to-end test for quickstart V2 in `frontend/tests/e2e/us2-knowledge-check.spec.ts`

### Implementation for User Story 2

- [X] T060 [US2] Create migration `0003_assessment_attempt` (`id` UUID PK client-provided, `account_id`, `knowledge_check_id`, `content_version`, `bundle_version`, `status` enum `in_progress | submitted`, `answers` JSONB, `question_order` JSONB, `score` numeric(4,3), `passed` bool, `per_objective` JSONB, `started_at`, `submitted_at`) in `backend/alembic/versions/0003_assessment_attempt.py`
- [X] T061 [P] [US2] Implement the AssessmentAttempt model in `backend/src/academy/assessments/models.py`
- [X] T062 [P] [US2] Implement pure scoring functions in `backend/src/academy/assessments/scoring.py`
- [X] T063 [US2] Implement the assessment service (start or resume with randomized `question_order` and pinned `bundle_version`; questions returned without correct answers; save answer returning `correct`, `explanation_markdown`, `lesson_link`; submit; best score; history; weak objectives) in `backend/src/academy/assessments/service.py`
- [X] T064 [US2] Implement routes `POST /knowledge-checks/{checkId}/attempts`, `GET /knowledge-checks/{checkId}/attempts/history`, `PUT /attempts/{attemptId}/answers/{questionId}`, `POST /attempts/{attemptId}/submit` in `backend/src/academy/assessments/router.py`
- [X] T065 [US2] Implement the progress derivation module with objective status (demonstrated ⇔ the module's knowledge check passed in any version), and module status `not_started | in_progress | completed` where completed requires the knowledge check AND all module challenges passed (FR-037; never relaxed), in `backend/src/academy/progress/derivation.py` with unit tests in `backend/tests/unit/progress/test_derivation.py`
- [X] T066 [P] [US2] Implement accessible question components (single choice radio group, multiple choice checkboxes, ordering with move-up/move-down buttons, matching with selects) in `frontend/src/features/knowledge-check/questions/`
- [X] T067 [US2] Implement the knowledge check flow (intro with question count, threshold and objectives; per-question feedback with lesson link; unanswered-question confirmation; result with weak objectives and retry; best score; draft replay via T044) in `frontend/src/features/knowledge-check/KnowledgeCheckPage.tsx`
- [X] T068 [US2] Show the knowledge-check entry and module status on the module page, with the label "In progress — challenge available in a later release" while no challenge evaluation is enabled (feature flag `challenges_enabled` from `/health`), in `frontend/src/features/module/ModuleStatus.tsx`

**Checkpoint**: US1 + US2 work; no competency is shown as demonstrated.

---

## Phase 5: User Story 6 — Explore the curriculum and prerequisites (Priority: P3) · Increment 1

**Goal**: Public catalog and roadmap from LLM foundations to production deployment, with planned
paths and prerequisite visibility.

**Independent Test**: Signed out, open the catalog; every path shows level, prerequisites,
competencies and availability; planned paths cannot be started.

### Tests for User Story 6

- [X] T069 [P] [US6] Write failing integration tests for `GET /catalog` (public, ordered by `order`, includes planned paths) in `backend/tests/integration/catalog/test_catalog_api.py`

### Implementation for User Story 6

- [X] T070 [P] [US6] Author planned paths (status `planned`, level, summary, prerequisite paths, competencies) for: orchestration and workflows, multi-agent architectures, MCP, RAG and knowledge integration, evaluation and observability, security and responsible AI, production deployment (FR-002) in `content/en/paths/<path-id>/path.yaml`
- [X] T071 [US6] Implement `list_catalog` and route `GET /catalog` in `backend/src/academy/catalog/service.py` and `backend/src/academy/catalog/router.py`
- [X] T072 [US6] Implement the public catalog/roadmap page (grouped by level, roadmap order, "Not yet available" badge, planned paths inspectable but not startable, missing prerequisites shown for signed-in learners) and make it the landing route in `frontend/src/features/catalog/CatalogPage.tsx`
- [X] T073 [US6] Extend the e2e test with quickstart V1 step 1 in `frontend/tests/e2e/us6-catalog.spec.ts`

**Checkpoint (Increment 1 exit)**: quickstart V1, V2, V7.1, V7.5 pass; Module 1 content complete.

---

## Phase 6: User Story 4 — Complete a practical challenge (Priority: P2) · Increment 2

**Goal**: Learners edit code, run tests and submit; code runs in an isolated gVisor container and
returns per-criterion feedback; hints, attempts and history are recorded.

**Independent Test**: Quickstart V4 and V7.2–V7.4 (limits, forbidden operations, evaluation
unavailable, worker crash).

### Tests for User Story 4

- [X] T074 [P] [US4] Write failing runner unit tests for lease claim and fenced completion (a late result with a superseded `lease_id` is discarded), submission-file validation (absolute paths, `..`, and reserved names `conftest.py`, `sitecustomize.py`, `usercustomize.py`, `pytest.py`, `pytest/`, `_pytest/`, `academy_sim*`, `*.pth` → `failed` "invalid submission files"), result validation (missing file, symlink or non-regular file, > 1 MB, malformed JSON, schema mismatch, missing/extra/duplicated test ids, exit status inconsistent with outcomes → `failed` integrity error; a well-formed result with the exact expected ids is accepted, documenting that validation cannot detect forgery, D1), criteria mapping (`met` ⇔ all its tests passed; `passed` ⇔ all mandatory criteria met), output truncation to 64 KB and secret scrubbing in `runner/tests/unit/`
- [X] T075 [P] [US4] Write the sandbox security suite (requires `RUNNER_RUNTIME=runsc`): network access, fork bomb, infinite loop, memory exhaustion, 10 MB output, writing to `/work`, reading environment variables, listing the file system (no solution or other submission present), printing a forged result JSON to stdout (ignored), attempting to overwrite, shadow or replace the trusted evaluation tests — a learner file under `tests/` or named `manifest.json` (rejected as reserved), a learner module whose name equals one of the challenge's test module names (rejected), a learner file named like a test (`test_*.py`) that pytest would otherwise collect (not collected), and writes into `/work/tests` at run time (fail, read-only) — with an assertion that the executed test files are byte-identical to those in the immutable bundle of the submission's `bundle_version`, submitting a reserved file name such as `conftest.py` or `sitecustomize.py` (rejected), `/work/tests` containing only the evaluated challenge's tests — each must be contained with the expected status and stop reason, in `runner/tests/security/test_containment.py`; and a result-integrity suite in `runner/tests/security/test_result_integrity.py` where learner code manipulates `/out/result.json`: (a) overwrites it with a wrong test-id set → `failed` integrity error; (b) replaces it with a symlink → rejected; (c) writes more than 1 MB → rejected; (d) fills `/out` → write fails inside the container, other jobs and the host unaffected; (d2) any learner access to `/out` is reported as `out_access` audit events and is not reported as `forbidden_operation`; (e) writes, e.g. from an `atexit` handler, a well-formed result reporting the exact expected ids as passed → **accepted**, and the test asserts that only that learner's own submission is affected (no other submission, account or job row changes). Case (e) is named `test_d1_accepted_residual_risk` and documents D1; it must not be marked as a passing security guarantee
- [X] T076 [P] [US4] Write failing integration tests for challenge detail (reference explanation only when passed), workspace autosave (413 above 256 KB), hints (409 when exhausted, count recorded), submission creation (idempotent `submission_id`, 429 when one run is in progress, 503 `evaluation_unavailable` when no heartbeat newer than 30 s or queue > 200), queue position, `delayed` after 5 minutes, and attempt counting rules in `backend/tests/integration/challenges/test_challenges_api.py`; plus tests of the runner database functions connected as `academy_runner` in `backend/tests/integration/challenges/test_runner_functions.py`: no direct `SELECT/INSERT/UPDATE/DELETE` on any table succeeds; `PUBLIC` and the API role cannot execute the functions; invalid parameters are rejected; completion with a wrong or superseded `lease_id` returns false and changes nothing; completion of a job not in `running` is rejected; invalid status transitions are rejected; heartbeat extends only the calling worker's leases; claimed jobs never expose account ids
- [X] T077 [P] [US4] Write a failing end-to-end test for quickstart V4 in `frontend/tests/e2e/us4-challenge.spec.ts`

### Implementation for User Story 4

- [X] T078 [US4] Create migration `0004_challenges` for `challenge_workspace` (`files` JSONB, max 256 KB total), `hint_usage`, `challenge_submission` (`id` client UUID, `kind` enum `visible_run | submission`, `attempt_number`, `files`, `status` enum `queued | running | passed | failed | stopped | error | cancelled`, `stop_reason` enum `timeout | memory | output_limit | forbidden_operation | null`, `criteria_results` JSONB, `output_excerpt` ≤ 64 KB, `hints_used`, `content_version`, `bundle_version`, timestamps), `submission_job` (`worker_id`, `lease_id`, `lease_expires_at`, `infra_attempts`, `available_at`) and `runner_worker` (`worker_id`, `capacity`, `started_at`, `last_heartbeat_at`) in `backend/alembic/versions/0004_challenges.py`
- [X] T079 [US4] In the same migration create role `academy_runner` (`LOGIN`, `NOINHERIT`, no table, sequence or schema `CREATE` privileges; only `USAGE` on the schema that holds the functions) and the `SECURITY DEFINER` functions of runner-protocol §1, owned by a dedicated non-superuser owner role that has only the table privileges the functions need, in `backend/alembic/versions/0004_challenges.py`, with these hardening rules for every function:
  - fixed safe search path: `SET search_path = pg_catalog, pg_temp` on the function, with every table, type and function reference schema-qualified;
  - `REVOKE ALL ON FUNCTION … FROM PUBLIC`, then `GRANT EXECUTE` explicitly to `academy_runner` only; `ALTER DEFAULT PRIVILEGES … REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC` for the schema;
  - parameter validation, raising an error on failure: `worker_id` non-null, 1–64 characters of `[A-Za-z0-9_-]`; `submission_id` and `lease_id` non-null UUIDs; `capacity` between 1 and 16; `result_json` non-null, ≤ 1 MB, with `status` in `passed | failed | stopped | error`, `stop_reason` in `timeout | memory | output_limit | forbidden_operation` or null (non-null only with `stopped`), and `criteria_results` an array;
  - valid state transitions only: claim moves `queued → running` (or re-claims a `running` job whose lease expired); complete moves `running → passed | failed | stopped | error`; any other current state is rejected without changes; a lease expired 3 times moves the submission to `error` without counting an attempt;
  - lease fencing: `runner_claim_job(worker_id)` uses `FOR UPDATE SKIP LOCKED`, sets a fresh random `lease_id` and `lease_expires_at = now() + 60 s`, increments `infra_attempts` and returns only `submission_id, lease_id, challenge_id, content_version, bundle_version, kind, files, limits` (never `account_id`); `runner_complete_job(submission_id, lease_id, result_json)` updates only when `lease_id` equals the job's current lease, returning false otherwise; `runner_heartbeat(worker_id, capacity)` upserts `runner_worker` and extends only leases held by that `worker_id`;
  - the runner role keeps no direct table privileges; worker ids are self-asserted by the shared runner role, which is acceptable because the runner host is trusted-but-exposed (runner-protocol §0) and documented in the migration header
- [X] T080 [P] [US4] Implement ORM models for ChallengeWorkspace, HintUsage, ChallengeSubmission, SubmissionJob, RunnerWorker in `backend/src/academy/challenges/models.py`
- [X] T081 [US4] Implement the challenge service (detail from the current bundle with workspace or starter files and tests; autosave; reveal next hint; create submission + job in one transaction with availability and per-learner concurrency checks; list submissions; get submission with `queue_position` and `delayed`; `attempt_number` assigned only for final states that count; cancel queued jobs on account deletion) in `backend/src/academy/challenges/service.py`
- [X] T082 [US4] Implement routes `GET /challenges/{challengeId}`, `PUT /challenges/{challengeId}/workspace`, `POST /challenges/{challengeId}/hints`, `POST|GET /challenges/{challengeId}/submissions`, `GET /submissions/{submissionId}` in `backend/src/academy/challenges/router.py`
- [X] T083 [US4] Build the sandbox image (Python 3.13 slim, pytest, `academy_sim`, user 65534, no other packages) in `runner/sandbox-image/Dockerfile`
- [X] T084 [US4] Implement the in-sandbox harness `python -m academy_sim.run /work /out`: install non-removable `sys.addaudithook` hooks before importing learner code (report `socket.*`, `subprocess.Popen`, `os.system`, `os.exec*` and file access outside the permitted locations `/work`, `/tmp` and `/out` as `forbidden_operation` events; `/out` is an explicitly permitted output location, so learner opens, writes, renames or deletes under `/out` before the harness writes its final result are **not** classified as `forbidden_operation` but recorded as separate `out_access` audit events with operation and path, included in `audit_events` of the result and logged by the runner with the submission id for the result-integrity threat model; this observation is informational and does not by itself fail a submission, and because learner code shares the process it can suppress or forge these events, so D1 remains the documented residual risk), run pytest with `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`, write `/out/result.json` per runner-protocol §5 (never stdout); the module docstring states that learner code shares the process and can overwrite the result, so the harness only enables integrity checks and does not provide tamper-proof evaluation (D1), in `runner/sandbox-image/academy_sim/run.py`
- [X] T085 [P] [US4] Implement runner settings (`RUNNER_DATABASE_URL`, `CONTENT_DIR`, `RUNNER_RUNTIME`, `RUNNER_SANDBOX_IMAGE`, `RUNNER_CONCURRENCY`, `RUNNER_OUT_DIR`; refuse `runc`, image references without digest and a `RUNNER_OUT_DIR` that is not a tmpfs mount when `APP_ENV=production`, warn otherwise) in `runner/src/academy_runner/config.py`
- [X] T086 [US4] Implement the sandbox launcher with the exact flags of runner-protocol §3 (`--runtime runsc --network none --read-only --tmpfs /tmp:size=16m --user 65534:65534 --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 256m --memory-swap 256m --cpus 1 --ulimit nofile=64`, labels `academy.submission`, `academy.worker`, `academy.deadline`); reject submission files with absolute paths, `..` or reserved names before launching, where reserved names also include any path whose first segment is `tests` or equals `manifest.json`, and any module whose name equals one of the challenge's test module names; build a read-only `/work` with separate mounts so learner files can never overwrite, shadow or replace the trusted evaluation tests: `/work/submission/` (learner files only), `/work/tests/` (only the tests of the one challenge being evaluated, copied byte-for-byte from the immutable bundle file of the submission's pinned `bundle_version` — never from the submission payload, no other bundle content, never `solution/`; if that bundle version is missing the job ends as `error` without counting an attempt) and `/work/manifest.json` (expected test ids written by the runner); run pytest only on the explicit test file paths listed in the manifest with `--rootdir=/work/tests`, `--import-mode=importlib` (test modules are imported by path, never resolved by name from the learner's directory) and `-p no:cacheprovider`, so learner files are imported only by the tests and are never collected as tests; bind-mount a fresh empty per-job directory under `RUNNER_OUT_DIR` (owned by `65534`) at `/out`, read `result.json` after exit with `O_NOFOLLOW` and a 1 MB cap, then delete the directory; wall-clock kill at the challenge limit (≤ 10 s), streamed output cut at 64 KB, OOM detection, in `runner/src/academy_runner/sandbox.py`
- [X] T087 [US4] Implement the worker loop: claim via `runner_claim_job`, heartbeat every 10 s via `runner_heartbeat`, validate and map results, scrub messages, complete via `runner_complete_job`, concurrency `RUNNER_CONCURRENCY`; on start-up remove containers labeled with the worker id; reaper removing any `academy.*` container past `academy.deadline + 30 s`, in `runner/src/academy_runner/worker.py` and `runner/src/academy_runner/main.py`; switch `/health` `evaluation` to the heartbeat rule in `backend/src/academy/shared/health.py`
- [X] T088 [US4] Extend `progress/derivation.py` with competency status (demonstrated ⇔ every knowledge check and every challenge mapped to the competency has a passed result in any version; never reverts; `in_progress` ⇔ any related activity; computed on read) and path completion in `backend/src/academy/progress/derivation.py`
- [X] T089 [P] [US4] Implement the code editor (CodeMirror 6, file tabs, keyboard accessible, debounced autosave to the workspace plus local draft) in `frontend/src/features/challenge/Editor.tsx`
- [X] T090 [US4] Implement the challenge page (scenario, problem, expected outcome, instructions, criteria, validated competencies; progressive hints; "Run tests" and "Submit"; status polling with queue position, "delayed" and "evaluation unavailable" states; per-criterion results with messages and output; submission history; reference explanation after passing) in `frontend/src/features/challenge/ChallengePage.tsx`
- [X] T091 [US4] Remove the "challenge available in a later release" label when `challenges_enabled` is true and link the module page to its challenges in `frontend/src/features/module/ModuleStatus.tsx`
- [X] T092 [P] [US4] Implement the load script submitting N concurrent correct solutions and reporting p95 time-to-result against the 30 s target (NFR-006a) in `runner/tests/load/submit_burst.py`

**Checkpoint**: Modules can be completed and competencies demonstrated.

---

## Phase 7: User Story 3 — Track progress on the learning dashboard (Priority: P2) · Increment 2

**Goal**: Single-screen dashboard with active path, competencies demonstrated out of total, module
statuses, pending objectives, next step and "continue"; competency view with evidence; path
completion summary; path reset.

**Independent Test**: Quickstart V3: progress persists across sign-out and another browser.

### Tests for User Story 3

- [X] T093 [P] [US3] Write failing integration tests for `GET /me/dashboard` (new learner welcome state; module in progress vs completed; next step; continue; `path_completed`), `GET /me/competencies` (evidence with version) and `DELETE /me/paths/{pathId}/progress` (requires `confirm: "RESET"`, removes only that path's rows) in `backend/tests/integration/progress/test_dashboard_api.py`
- [X] T094 [P] [US3] Write a failing end-to-end test for quickstart V3 in `frontend/tests/e2e/us3-dashboard.spec.ts`

### Implementation for User Story 3

- [X] T095 [US3] Implement the dashboard service (active path = path of the most recent activity; competencies demonstrated/total; module statuses; pending objectives per module; next step: next unread lesson → knowledge check → challenge → next path; `continue` from the latest ContentView; `path_completed`) in `backend/src/academy/progress/service.py`
- [X] T096 [US3] Implement path reset deleting the learner's ContentView, attempts, workspaces, submissions, hint usage and lab visits scoped to the path's content ids in one transaction in `backend/src/academy/progress/reset.py`
- [X] T097 [US3] Implement routes `GET /me/dashboard`, `GET /me/competencies`, `DELETE /me/paths/{pathId}/progress` in `backend/src/academy/progress/router.py`
- [X] T098 [US3] Implement the dashboard page (single screen; welcome state for new learners; continue action; module list; pending objectives) in `frontend/src/features/dashboard/DashboardPage.tsx`
- [X] T099 [P] [US3] Implement the competency view (level, status, evidence links to attempt history and submissions per FR-041) in `frontend/src/features/dashboard/CompetenciesPage.tsx`
- [X] T100 [P] [US3] Implement the path completion summary (demonstrated competencies, evidence, recommended next path) and the reset dialog with explicit confirmation in `frontend/src/features/dashboard/PathCompletion.tsx` and `frontend/src/features/dashboard/ResetPathDialog.tsx`

**Checkpoint (Increment 2 exit)**: quickstart V3, V4, V7.2–V7.4 pass; sandbox security suite green
under `runsc`.

---

## Phase 8: User Story 5 — Explore an agent run in the basic laboratory (Priority: P3) · Increment 3

**Goal**: Replay curated recordings with four trace element kinds, variants, comparison, failure
explanations and human approval — without model calls.

**Independent Test**: Quickstart V5.

### Tests for User Story 5

- [X] T101 [P] [US5] Write failing unit tests for the trace player state machine (step forward/back, pause, resume, restart, jump; approval branch selection; comparison counts and elements present in only one variant) in `frontend/tests/unit/lab/player.test.ts`
- [X] T102 [P] [US5] Write a failing end-to-end test for quickstart V5, asserting no network requests leave the application origin, in `frontend/tests/e2e/us5-lab.spec.ts`

### Implementation for User Story 5

- [X] T103 [P] [US5] Author scenario `research-agent-with-tools` (single agent, read tools, decision summaries labeled `educational_explanation`, `recorded_with`) in `content/en/lab/research-agent-with-tools.json`
- [X] T104 [P] [US5] Author scenario `workflow-vs-agent-loop` with variants `fixed_workflow` and `agent_loop` on the same task and a `comparisons` entry in `content/en/lab/workflow-vs-agent-loop.json`
- [X] T105 [P] [US5] Author scenario `prompt-injection-and-approval` with a prompt-injection failure case (risk + mitigation), an invalid-tool-argument failure case and a `destructive` tool preceded by `approval_request` with approved and rejected branch variants in `content/en/lab/prompt-injection-and-approval.json`
- [X] T106 [US5] Create migration `0005_lab_visit` (`account_id`, `scenario_id`, `variant_id`, `first_viewed_at`, `last_viewed_at`) and implement the model, service and route `GET /lab/scenarios/{scenarioId}` (records a visit; never evidence) in `backend/alembic/versions/0005_lab_visit.py` and `backend/src/academy/lab/`
- [X] T107 [US5] Implement the trace player state machine in `frontend/src/features/lab/player.ts`
- [X] T108 [US5] Implement the laboratory page (task, objective, tools with permissions, pattern; trace list with element-kind labels; state panel before/after; decision summaries visually marked "Educational explanation"; controls pause/resume/restart/jump; `aria-live` announcements; failure highlight with risk and mitigation; approval prompt choosing the approved or rejected branch) in `frontend/src/features/lab/LabPage.tsx`
- [X] T109 [US5] Implement the side-by-side comparison view (per variant: element count, tool-call count, final outcome; elements present in only one variant marked) in `frontend/src/features/lab/CompareView.tsx`
- [ ] T110 [US5] Link lab scenarios from their modules (`lab_scenarios` in `module.yaml` of modules 02 and 03) and show them as guided practice on the module page in `frontend/src/features/module/ModulePage.tsx`

**Checkpoint**: US5 works on its own.

---

## Phase 9: User Story 7 — Maintain educational content safely (Priority: P3) · Increment 3

**Goal**: Versions, review dates and deprecations visible; publication blocked on inconsistencies;
demonstrated competencies preserved across versions.

**Independent Test**: Quickstart V6.

### Tests for User Story 7

- [ ] T111 [P] [US7] Write failing tests for validator rule 9 (content changed without a version bump relative to the previous bundle) in `backend/tests/unit/content/test_version_bump.py`
- [ ] T112 [P] [US7] Write a failing integration test: learner passes a check and challenge on version 1.0.0, a 2.0.0 bundle is published, the competency stays demonstrated with evidence on 1.0.0 (FR-051), in `backend/tests/integration/progress/test_version_retention.py`

### Implementation for User Story 7

- [ ] T113 [US7] Implement rule 9 comparing each item's content hash against the latest bundle in `dist/content/` in `backend/src/academy/content/validate.py`
- [ ] T114 [US7] Resolve `content/en/deprecations.yaml` and inline `:::deprecated` references so every API item carries its `deprecation` in `backend/src/academy/content/loader.py`
- [ ] T115 [P] [US7] Show version and last-reviewed date on module, challenge and lab pages, and deprecation notices wherever a deprecated item appears, in `frontend/src/components/content/ContentMeta.tsx`
- [ ] T116 [US7] Add the `academy content validate --run-solutions` and `academy content build` gates to CI so a failing validation blocks merges in `.github/workflows/ci.yml`

**Checkpoint (Increment 3 exit)**: quickstart V5, V6 pass; 3 lab scenarios reviewed.

---

## Phase 10: Curriculum completion

**Purpose**: Complete the introductory path (FR-003, FR-013, FR-025). Each module includes
`module.yaml`, lessons with "why" explanations, maturity labels and vendor notes, ≥ 1 Python code
example, ≥ 1 diagram with alt text, references, a knowledge check with ≥ 5 questions mapped to
objectives, and ≥ 1 challenge with tests using `academy_sim`, a `solution/`, ≥ 2 hints and a
strictly higher `difficulty_rank`, passing `academy content validate --run-solutions`.

- [ ] T117 [P] Author Module 2 "Agent fundamentals" (agent loop, workflow vs agent, stopping conditions, step limits, excessive autonomy; challenge `difficulty_rank: 3`) in `content/en/paths/foundations-of-agentic-ai-engineering/modules/02-agent-fundamentals/`
- [ ] T118 [P] Author Module 3 "Tools and function calling" (tool schemas, argument validation, least privilege, human approval for destructive tools, prompt injection via tool results; challenge `difficulty_rank: 4`) in `content/en/paths/foundations-of-agentic-ai-engineering/modules/03-tools-and-function-calling/`
- [ ] T119 [P] Author Module 4 "Memory and state management" (conversation state, scratchpads, summarization, persistence boundaries, privacy and data minimization; challenge `difficulty_rank: 5`) in `content/en/paths/foundations-of-agentic-ai-engineering/modules/04-memory-and-state/`
- [ ] T120 [P] Author Module 5 "Evaluation, observability and agentic risks" (trace-based evaluation, test doubles for models, hallucination detection, observability without private reasoning, risk catalogue; challenge `difficulty_rank: 6`) in `content/en/paths/foundations-of-agentic-ai-engineering/modules/05-evaluation-observability-and-risks/`
- [ ] T121 Technical review of all five modules by a subject-matter expert, setting `last_reviewed` and recording findings in `docs/content-review/2026-foundations.md`

---

## Phase 11: Polish & Cross-Cutting Concerns (Hardening)

- [ ] T122 [P] Add security headers (strict Content-Security-Policy without inline scripts, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`) in `frontend/Dockerfile` web-server config and `backend/src/academy/main.py`
- [ ] T123 [P] Run an accessibility audit of all learner screens at WCAG 2.2 AA (automated axe plus a manual keyboard and screen-reader pass) and record results in `docs/accessibility/audit-mvp.md` (SC-007)
- [ ] T124 [P] Measure NFR-003 (module page readable < 2 s p95, knowledge-check feedback < 1 s p95) with a Playwright performance script in `frontend/tests/e2e/perf.spec.ts`, and SC-012 with `runner/tests/load/submit_burst.py --n 10`; record results in `docs/performance/mvp.md`
- [ ] T125 [P] Verify SC-008: with the runner stopped and with SMTP unavailable, lessons, knowledge checks and dashboard keep working, in `frontend/tests/e2e/resilience.spec.ts`
- [ ] T126 Prepare the runner-host hardening checklist (dedicated host, gVisor version pinning and monthly update, no secrets beyond `RUNNER_DATABASE_URL`, Docker socket exposure, reaper enabled, fixed-size tmpfs for `RUNNER_OUT_DIR`), the trust-boundary description copied from runner-protocol §0, the known isolation limitations from runner-protocol §8 including the accepted D1 tampering risk (evaluation is not tamper-proof; revisit before any certificate), and the external penetration-test scope in `docs/security/runner-host.md`
- [ ] T127 [P] Update the repository `README.md` with the stack, commands and links to the quickstart and ADRs
- [ ] T128 Run every scenario in quickstart.md (V1–V7) from a clean environment and fix any drift between docs and behavior in `specs/001-agentic-academy-mvp/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks all stories. T028 (`academy_sim`) blocks all
  challenge content (T056, T117–T120) and the runner (T083–T087).
- **Increment 1**: US1 (Phase 3) → US2 (Phase 4) → US6 (Phase 5). US6 depends only on Foundational
  and can run in parallel with US1/US2.
- **Increment 2**: US4 (Phase 6) before US3 (Phase 7): the dashboard cannot show a demonstrated
  competency without challenge evaluation (architecture-review §2.2). US3 backend work (T095–T097)
  can start once T088 exists.
- **Increment 3**: US5 (Phase 8) and US7 (Phase 9) are independent of each other; US5 needs only
  Foundational + US1 module page (T110).
- **Curriculum (Phase 10)**: depends on T020–T024 and T028; can run in parallel with Phases 3–9.
- **Polish (Phase 11)**: depends on all stories.

### User Story Dependencies

| Story | Depends on | Notes |
|-------|-----------|-------|
| US1 | Foundational | — |
| US2 | Foundational, US1 module page (T055) for the entry point | Scoring testable alone |
| US6 | Foundational | — |
| US4 | Foundational, T065 derivation | Introduces runner, sandbox, migration 0004 |
| US3 | US2 (attempts), US4 (submissions, T088) | Demonstrated competencies need both |
| US5 | Foundational, T055 | Laboratory visits are never evidence |
| US7 | Foundational content pipeline | Retention test uses US2 + US4 data |

### Within Each Story

Tests first (must fail) → migrations/models → services → routes → frontend → content.

### Parallel Opportunities

- Setup: T003–T006, T009–T011.
- Foundational: T013/T014; T018/T019; T027 with the content pipeline; T030–T035 (different files);
  T041/T042/T044/T045/T047.
- US1: T048/T049 tests; T051 and T054 alongside backend service work.
- US2: T057–T059 tests; T061/T062; T066 while T063 is built.
- US4: T074–T077 tests; T080, T085, T089, T092 alongside the main chain.
- US5: T101/T102 tests; T103–T105 content authoring in parallel.
- Curriculum: T117–T120 in parallel by different authors.

---

## Parallel Example: User Story 4

```bash
# Tests first, in parallel:
Task: "Runner unit tests for leases, fencing, result validation in runner/tests/unit/"
Task: "Sandbox security suite in runner/tests/security/test_containment.py"
Task: "Challenge API integration tests in backend/tests/integration/challenges/test_challenges_api.py"
Task: "E2E for quickstart V4 in frontend/tests/e2e/us4-challenge.spec.ts"

# Then independent implementation files in parallel:
Task: "ORM models in backend/src/academy/challenges/models.py"
Task: "Runner settings in runner/src/academy_runner/config.py"
Task: "Code editor in frontend/src/features/challenge/Editor.tsx"
```

## Parallel Example: Curriculum

```bash
Task: "Author Module 2 in content/en/paths/foundations-of-agentic-ai-engineering/modules/02-agent-fundamentals/"
Task: "Author Module 3 in content/en/paths/foundations-of-agentic-ai-engineering/modules/03-tools-and-function-calling/"
Task: "Author Module 4 in content/en/paths/foundations-of-agentic-ai-engineering/modules/04-memory-and-state/"
Task: "Author Module 5 in content/en/paths/foundations-of-agentic-ai-engineering/modules/05-evaluation-observability-and-risks/"
```

---

## Implementation Strategy

### MVP first (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational.
2. Phase 3 (US1) → **stop and validate** with quickstart V1.

### Incremental delivery

1. **Increment 1**: US1 → US2 → US6 → demo (V1, V2, V7.1, V7.5). Modules show "in progress —
   challenge available in a later release"; no competency is demonstrated.
2. **Increment 2**: US4 → US3 → demo (V3, V4, V7.2–V7.4) with the security suite green under
   `runsc`.
3. **Increment 3**: US5 + US7 → demo (V5, V6).
4. **Curriculum completion** in parallel from Increment 1 onwards.
5. **Hardening**: Phase 11, then release.

### Parallel team strategy

- Developer A: backend (auth → assessments → challenges API → progress).
- Developer B: runner + sandbox + security suite (from Increment 2, after T028).
- Developer C: frontend (shell → module → knowledge check → challenge → dashboard → lab).
- Content authors: Module 1 in Increment 1, Modules 2–5 and lab scenarios in parallel.
