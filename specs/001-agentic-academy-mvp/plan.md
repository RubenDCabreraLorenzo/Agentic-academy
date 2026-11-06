# Implementation Plan: Agentic Academy MVP

**Branch**: `claude/gifted-davinci-t1hlbh` (feature dir `001-agentic-academy-mvp`) | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-agentic-academy-mvp/spec.md`

## Summary

Agentic Academy is a web application for learning Agentic AI engineering through a structured
introductory path with lessons, knowledge checks, code challenges evaluated automatically in an
isolated sandbox, a laboratory that replays curated agent execution traces, and competency-based
progress tied to learner accounts.

Technical approach (see [research.md](./research.md)):

- **Frontend**: TypeScript React SPA (Vite) talking to a versioned HTTP API generated from OpenAPI.
- **Backend**: Python 3.13 / FastAPI modular monolith with clear domain modules (auth, content,
  assessments, challenges, lab, progress) and PostgreSQL storage.
- **Content as code**: Markdown + YAML + JSON under `content/`, validated by a content CLI in CI
  and built into an immutable versioned bundle (publish = merge).
- **Runner**: a separate worker that claims submission jobs from a PostgreSQL queue and executes
  each submission in an ephemeral gVisor container with no network and strict limits; tests use a
  vendor-neutral `academy_sim` package with scripted model and tool doubles.
- **Laboratory**: recorded, reviewed traces replayed entirely client-side; no model calls.
- Delivered in three increments following spec priorities, then hardening (research R13).
- Architecture review findings and corrections: [architecture-review.md](./architecture-review.md).

## Technical Context

**Language/Version**: Python 3.13 (backend, runner, content CLI, sandbox); TypeScript 5.x on
Node.js 24 LTS (frontend tooling)

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, argon2-cffi, pytest
(sandbox); React 19, Vite, React Router, TanStack Query, react-i18next, Shiki, CodeMirror 6,
Mermaid; gVisor `runsc` + OCI containers for the sandbox

**Storage**: PostgreSQL 17 (accounts, sessions, progress, attempts, submissions, job queue);
versioned content bundle files built from `content/`

**Testing**: pytest (unit, integration with disposable PostgreSQL), schemathesis (API contract),
runner security suite; Vitest + Testing Library; Playwright + axe-core (end-to-end, accessibility);
ruff, mypy, ESLint, TypeScript strict

**Target Platform**: Modern evergreen desktop and mobile browsers (last 2 versions of Chromium,
Firefox, Safari; initial value D4); Linux x86_64 servers with gVisor for the runner; hosting provider not chosen
(R12)

**Project Type**: Web application (SPA frontend + API backend + background runner)

**Performance Goals**: module pages readable < 2 s p95 (NFR-003); knowledge-check feedback < 1 s
p95; challenge results < 30 s p95 (NFR-006a, SC-012); sandbox start + run typically 2–5 s

**Constraints**: no learner data to external model services (NFR-007); no network, secrets or
shared state inside the sandbox (FR-022a); WCAG 2.2 AA (NFR-001); 360 px minimum width (NFR-002);
English only but i18n-ready (FR-054, FR-055); 99.5% monthly availability target post-launch
(NFR-005)

**Scale/Scope**: ≤ 1,000 registered learners, ≤ 100 concurrent, peak 10 simultaneous submissions
(working hypothesis R10, approved D3); 1 available path with 5–7 modules, ≥ 3 lab scenarios; ~20 screens

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / Standard | How the plan complies | Pre | Post |
|----------------------|-----------------------|-----|------|
| I. Learning First | Every component maps to a user story with learning outcomes; content directives enforce maturity labels and "why" explanations (FR-010, FR-012); UI favors reading mode (NFR-012) | ✅ | ✅ |
| II. Hands-on Learning | Each module has ≥ 1 code challenge executed for real against tests; lab replays realistic scenarios incl. failures; difficulty_rank enforced in validation (FR-025) | ✅ | ✅ |
| III. Progressive Complexity | Prerequisite graphs and single-agent-before-multi-agent rule validated in CI (content-schema rules 3–4); competency levels in data model | ✅ | ✅ |
| IV. Engineering Excellence | Modular monolith with explicit module boundaries; domain logic (scoring, competency derivation, runner mapping) as pure functions with unit tests; explicit contracts (OpenAPI, content schema, lab schema, runner protocol); ADRs in `docs/adr/`; coverage gate ≥ 90% on domain modules | ✅ | ✅ |
| V. Responsible AI | Sandbox with least privilege and no network (R6); runner DB role restricted; destructive tool approval modeled in lab traces (FR-030); secrets never in frontend or logs, output scrubbing (FR-047); private model reasoning excluded from recordings (FR-027a); curriculum covers injection, hallucination, autonomy (FR-013) | ✅ | ✅ |
| VI. Model & Framework Agnosticism | No model provider dependency at runtime; `academy_sim` and lab schema are vendor-neutral; `EmailSender` port; hosting deferred behind requirements (R12); vendor notes labeled in content | ✅ | ✅ |
| VII. Measurable Learning Outcomes | Competency derivation rules (data-model §2.12) based only on passed checks and challenges; every item traceable to competencies, validated in CI (FR-044) | ✅ | ✅ |
| UX & Accessibility | axe-core in end-to-end tests, keyboard-accessible editor (CodeMirror 6), responsive layouts tested at 360 px, single-screen dashboard contract | ✅ | ✅ |
| Reliability & Performance | Runner failures isolated from content/progress (SC-008); idempotent submissions; queue retries; performance targets validated in quickstart V4 and load script | ✅ | ✅ |
| Content Governance | Content in git, SemVer per item, last_reviewed, deprecations, validation blocks merges; results bound to content version | ✅ | ✅ |
| Governance | No conflicts identified; complexity deviations justified below | ✅ | ✅ |

**Result**: PASS (pre-research and post-design). No unresolved NEEDS CLARIFICATION remain; R10
(scale) is an approved working hypothesis (D3) that does not affect the architecture.

## Project Structure

### Documentation (this feature)

```text
specs/001-agentic-academy-mvp/
├── plan.md              # This file
├── research.md          # Phase 0 decisions (R1–R13)
├── data-model.md        # Phase 1 entities, rules, state transitions
├── quickstart.md        # Phase 1 run + validation guide
├── contracts/
│   ├── openapi.yaml           # Frontend ↔ backend HTTP API
│   ├── content-schema.md      # Content files, directives and validation rules
│   ├── lab-trace.schema.json  # Laboratory scenario / trace format
│   └── runner-protocol.md     # Queue, sandbox execution and result format
├── checklists/requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── alembic/
├── src/academy/
│   ├── main.py                  # app factory, routers wiring
│   ├── config.py
│   ├── shared/                  # errors (problem details), clock, ids, security helpers
│   ├── db/                      # session, base models, migrations glue
│   ├── auth/                    # accounts, sessions, tokens, EmailSender port + adapters
│   ├── content/                 # Pydantic content schemas, loader, validate/build CLI
│   ├── catalog/                 # catalog, path and module read APIs
│   ├── assessments/             # knowledge checks: attempts, scoring
│   ├── challenges/              # workspaces, hints, submissions, queue producer
│   ├── lab/                     # scenario serving, lab visits
│   └── progress/                # content views, competency derivation, dashboard
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

runner/
├── pyproject.toml
├── src/academy_runner/          # queue consumer, sandbox launcher, result mapper, scrubber
├── sandbox-image/
│   ├── Dockerfile
│   └── academy_sim/             # vendor-neutral model/tool doubles + pytest entrypoint
└── tests/
    ├── unit/
    ├── security/                # malicious submissions that must be contained
    └── load/

frontend/
├── package.json
├── src/
│   ├── app/                     # routing, layout, providers, error boundaries
│   ├── api/                     # client generated from contracts/openapi.yaml
│   ├── i18n/en/                 # interface strings
│   ├── components/              # design system: code block, diagram, callouts, progress
│   └── features/
│       ├── auth/
│       ├── catalog/
│       ├── module/
│       ├── knowledge-check/
│       ├── challenge/           # editor, hints, results
│       ├── lab/                 # trace player, comparison
│       └── dashboard/
└── tests/
    ├── unit/
    └── e2e/

content/
├── competencies.yaml
└── en/ (paths/, lab/, deprecations.yaml)

docs/adr/                        # architecture decision records
docker-compose.yml
.github/workflows/ci.yml         # lint, types, tests, content validation, e2e
```

**Structure Decision**: Web application with three deployable units (frontend, backend API,
runner) sharing one repository and one PostgreSQL database; educational content versioned in the
same repository. The frontend and API share one origin through a reverse proxy (Vite proxy in
development). Trust boundaries between browser, API host, database, runner host and sandbox are
defined in [contracts/runner-protocol.md §0](./contracts/runner-protocol.md). Backend is a modular monolith: each domain module owns its models, services and
router, and modules interact only through service interfaces, never through each other's tables.

## Delivery Increments

| Increment | User stories | Exit criteria |
|-----------|--------------|---------------|
| 1 | US1, US2, US6 (catalog), accounts, content validation in CI | quickstart V1, V2, V7.1, V7.5 pass; Module 1 content complete; modules shown as "in progress — challenge available in a later release", no competency demonstrated (data-model §2.12) |
| 2 | US4 (runner + sandbox) first, then US3 (dashboard, competency view) | V3, V4, V7.2–V7.4 pass; sandbox security suite green under `runsc` |
| 3 | US5, US7 | V5, V6 pass; ≥ 3 lab scenarios recorded and reviewed |
| Hardening | All | Accessibility audit (SC-007), performance (NFR-003, SC-012), full introductory path content |

## Risks

| Risk | Mitigation |
|------|------------|
| Sandbox escape or resource abuse | gVisor + no network + limits + separate host + restricted DB role; security suite in CI; Firecracker as upgrade path |
| Content authoring effort underestimated | Content is the critical path: write Module 1 during increment 1; validator enforces completeness early |
| Reference solutions leak | Solutions never bundled or mounted; repository kept private. No hidden tests in the MVP (D2) |
| Learner fakes a pass by subverting the in-process harness | Result-file validation; residual risk accepted by the product owner while no certificates exist (D1) |
| Lab recordings drift from current model behavior | `recorded_with` + `last_reviewed` + review cadence under content governance |
| Scale assumption wrong | Runner scales horizontally by adding workers; queue position shown to learners |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate runner service (3rd deployable unit) | Untrusted code must never run on the API host or near secrets/database (FR-022a, NFR-006) | Running sandboxes from the API process would put untrusted execution next to credentials and learner data |
| gVisor runtime instead of plain containers | Defense in depth for executing arbitrary learner code (SC-011) | Plain containers share the host kernel attack surface; microVMs add operational cost disproportionate to the MVP |
