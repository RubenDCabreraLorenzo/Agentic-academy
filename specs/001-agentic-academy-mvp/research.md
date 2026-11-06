# Research: Agentic Academy MVP

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-06

Each entry records the decision, why it was chosen and what else was considered. Decisions are
evaluated against the constitution: educational value, technical suitability and maintenance cost
(Principle VI), testability and clear boundaries (Principle IV), and least privilege (Principle V).

---

## R1. Backend language and framework

- **Decision**: Python 3.13 with FastAPI, Pydantic v2 for all request/response and content schemas,
  SQLAlchemy 2 (typed ORM) and Alembic for migrations.
- **Rationale**: Python is the learners' language (FR-003a) and the dominant language of the agentic
  ecosystem, so the platform's own code can serve as a reference for learners. Pydantic gives one
  source of truth for content schemas, API contracts and generated OpenAPI (Principle IV: explicit
  contracts). FastAPI produces the OpenAPI document used to generate the frontend client.
- **Alternatives considered**: Django (heavier, admin and templates not needed, weaker typed
  contracts); Node.js/TypeScript backend (single language across tiers, but splits the content
  schema from the Python challenge tooling); Go (no educational alignment).

## R2. Frontend

- **Decision**: TypeScript single-page application built with React 19 and Vite, React Router for
  navigation, TanStack Query for server state, Shiki for syntax highlighting, react-i18next for
  interface text, CodeMirror 6 as the in-browser code editor for challenges.
- **Rationale**: The product is an interactive application (dashboard, assessments, editor, trace
  stepper) behind sign-in, so server-side rendering brings little SEO value; a SPA keeps one clear
  boundary (frontend ↔ HTTP API). Shiki renders accurate, theme-consistent highlighting (FR-009).
  CodeMirror 6 is lightweight and has good keyboard and screen-reader support (NFR-001), unlike
  heavier editors. react-i18next satisfies FR-055 with externalized strings from day one.
- **Alternatives considered**: Next.js (SSR and file routing; extra server runtime and coupling to a
  hosting model, not needed for an authenticated app); Monaco editor (heavier, weaker accessibility
  on mobile); Prism (less accurate highlighting).
- **Note**: the public catalog pages (FR-045) are served by the same SPA; pre-rendering them is a
  later optimization if search visibility becomes a goal.
- **Rendering**: content Markdown is rendered in the frontend (Markdown → sanitized HTML, Shiki for
  code, Mermaid for diagrams). The content build validates Markdown but does not pre-render it,
  because Shiki and Mermaid are JavaScript tools.
- **Same origin**: the SPA and the API are served from one origin (`/` and `/api/v1`) through a
  reverse proxy in production and the Vite dev proxy locally, so `SameSite=Lax` session cookies and
  CSRF protection work without CORS.

## R3. Persistent storage

- **Decision**: PostgreSQL 17 for accounts, sessions, progress, assessment attempts, challenge
  submissions and the submission job queue.
- **Rationale**: Relational integrity fits progress records keyed by learner, content id and content
  version (FR-051). Using PostgreSQL as the job queue (`SELECT … FOR UPDATE SKIP LOCKED`) avoids a
  separate broker for the expected MVP load (R10), reducing infrastructure (lean MVP).
- **Alternatives considered**: Redis/RabbitMQ queue (extra service with no MVP-scale benefit);
  SQLite (insufficient for concurrent API + runner workers); document database (weaker
  relational guarantees for progress evidence).

## R4. Educational content storage and governance

- **Decision**: Content lives in the repository under `content/`, authored as Markdown lessons with
  YAML metadata files (paths, modules, knowledge checks, challenges, competencies) and JSON lab
  recordings. A content CLI (`academy content validate` / `academy content build`) validates every
  file against Pydantic schemas and cross-references (prerequisite chains, competency mapping,
  versions, language ids) and produces an immutable, versioned content bundle that the backend
  loads at start-up. Validation runs in CI; a failing validation blocks the merge ("publication").
- **Rationale**: Satisfies FR-048–FR-051 and NFR-009 with git as the versioning and review workflow
  (pull requests = review; merge = publish), without building an authoring interface (out of scope).
  Content is separated from application behavior and diffable.
- **Alternatives considered**: Headless CMS (vendor coupling, extra service, weak cross-reference
  validation); content in the database with an admin UI (out of MVP scope).
- **Versioning rule**: each content item carries `version` (SemVer) and `last_reviewed` date. A
  MAJOR bump on an assessment or challenge means previously recorded results remain valid for the
  version they were obtained on (FR-051); results are never revoked.

## R5. Authentication and accounts

- **Decision**: First-party email + password accounts inside a dedicated `auth` module: Argon2id
  password hashing, opaque server-side session tokens stored hashed in PostgreSQL and sent as
  `HttpOnly; Secure; SameSite=Lax` cookies, CSRF protection via double-submit token on state-changing
  requests, single-use time-limited tokens for email verification and password reset, rate limiting
  on sign-in and reset endpoints. Email sending goes through an `EmailSender` port with an SMTP
  adapter (production) and a console/file adapter (development and tests).
- **Rationale**: Meets FR-045a–b and NFR-007 with minimal data (email, password hash, timestamps) and
  no third-party identity dependency. Opaque server sessions are simple to revoke on sign-out and
  account deletion. The `EmailSender` port isolates the email provider (Principle VI).
- **Alternatives considered**: Managed identity provider (Auth0, Clerk, Cognito: faster but couples
  accounts to a vendor and sends learner data to a third party); JWT access tokens (harder
  revocation, no benefit for a single first-party frontend); passwordless magic links (depends
  entirely on email deliverability; can be added later).

## R6. Isolated execution of challenge code (highest-risk component)

- **Decision**: A separate **runner** service consumes submission jobs from the PostgreSQL queue and
  executes each submission in a fresh, ephemeral OCI container running under the **gVisor**
  (`runsc`) runtime, with:
  - no network (`--network none`), read-only root filesystem, a small `tmpfs` work directory;
  - non-root user, all Linux capabilities dropped, `no-new-privileges`, default seccomp profile;
  - limits: 1 vCPU, 256 MB memory, 64 PIDs, 10 s wall-clock per phase (visible tests; hidden tests
    in a second, fresh container), 64 KB captured output per phase;
  - a pinned, minimal sandbox image containing Python 3.13, pytest and the `academy_sim` package
    (R7), and nothing else; no platform secrets, credentials or database access;
  - the container is destroyed after each run; results are returned as a structured JSON report.
  The runner host is separate from the API host and may only call three `SECURITY DEFINER`
  database functions (claim, complete with lease fencing, heartbeat); it has no table access and
  never receives learner identity. Full protocol, trust boundaries, failure handling and known
  limitations: [contracts/runner-protocol.md](./contracts/runner-protocol.md).
- **Rationale**: gVisor intercepts system calls in a user-space kernel, adding a strong isolation
  layer over standard containers at modest start-up cost (sub-second), which fits NFR-006a
  (results < 30 s for 95% of submissions). A dedicated runner keeps untrusted execution away from
  the API, database and secrets (FR-022a, NFR-006, SC-011).
- **Alternatives considered**:
  - Plain Docker containers: weaker kernel isolation for untrusted code.
  - Firecracker microVMs: strongest isolation but much higher operational complexity for an MVP;
    retained as the upgrade path if threat assessment requires it.
  - nsjail: strong and light, but less common operational tooling.
  - In-browser execution (Pyodide/WebAssembly): no server risk, but results produced on the
    learner's device cannot be trusted as evidence of competency (Principle VII) and hidden tests
    would be exposed. Pyodide MAY later be used for the optional "run visible tests" preview only.
  - Third-party code execution APIs: vendor coupling and sends learner code to a third party.
- **Hidden tests**: stored in the content repository under `tests/hidden/` folders, built into a
  private bundle mounted only on the runner host, and executed in a separate container whose output
  is never returned to the learner. Reference solutions live in `solution/` and are never mounted
  in learner runs. If the content repository becomes public, hidden tests and solutions must move to
  a private location (documented risk; review decision D2).
- **Result integrity**: results are read from a result file and validated (exact expected test-id
  set), but learner code shares the process with the test harness, so a determined learner can fake
  a pass for their own submission. Accepted only while no certificates exist (review decision D1).

## R7. Simulated model and tool responses in challenges

- **Decision**: A small, vendor-neutral Python package `academy_sim` is installed in the sandbox image.
  It provides a `ScriptedModel` (returns scripted responses, including tool-call requests, keyed by
  turn), fake tools with declared permissions, and assertion helpers for traces. Challenge tests use
  it to drive learner code deterministically (FR-022b).
- **Rationale**: Deterministic, offline evaluation; teaches learners to design agent code behind an
  abstraction that can be tested without a real model (Principles IV, VI).
- **Alternatives considered**: Recording/replaying a real provider SDK (vendor coupling,
  non-portable); allowing network calls to a model (forbidden by FR-022a/FR-022b).

## R8. Laboratory recordings

- **Decision**: Each laboratory scenario is a JSON document validated by
  [contracts/lab-trace.schema.json](./contracts/lab-trace.schema.json). A scenario has one or more
  *variants*; each variant holds one recorded execution trace composed of the four element kinds of
  FR-027 (execution event, tool call, state transition, decision summary). Recordings are produced
  offline by maintainers with a recording script, then edited: private model reasoning is removed and
  decision summaries are written and reviewed (FR-027a). The frontend replays traces entirely
  client-side.
- **Rationale**: No model calls at runtime (FR-033), deterministic replays, zero runtime cost, and
  recordings reviewed like any other content (FR-033a). The schema is framework-neutral, so
  scenarios recorded with different providers or frameworks fit the same player (NFR-010).
- **Alternatives considered**: OpenTelemetry GenAI traces as the stored format (good for production
  observability but verbose and still evolving; the recording script MAY import from it later).

## R9. Testing strategy and quality gates

- **Decision**:
  - Backend: pytest (unit), pytest + a disposable PostgreSQL (integration), schemathesis against the
    generated OpenAPI (contract), coverage gate on domain modules (progress, assessments, challenges,
    auth) of ≥ 90% lines.
  - Runner: pytest with a security test suite of malicious submissions (network access, fork bomb,
    infinite loop, memory exhaustion, large output, filesystem escape, reading environment) that
    MUST all be contained (SC-011).
  - Frontend: Vitest + Testing Library (components), Playwright end-to-end for the critical
    workflows (NFR-011) with axe-core accessibility assertions (NFR-001, SC-007).
  - Content: `academy content validate` in CI on every change.
  - Static checks: ruff + mypy (strict on domain code), ESLint + TypeScript strict, OpenAPI client
    regeneration check (no drift).
- **Rationale**: Covers every critical workflow and regression scenario required by Principle IV and
  the Reliability standard, including the riskiest component (sandbox).
- **Alternatives considered**: Cypress (Playwright has better multi-browser and mobile emulation);
  manual accessibility review only (insufficient as a regression gate).

## R10. Expected MVP scale (pending spec item)

- **Decision (assumption)**: up to 1,000 registered learners, 100 concurrently active, and a peak of
  10 simultaneous challenge submissions during the beta. The runner starts with 2 workers × 2
  concurrent sandboxes and scales by adding workers.
- **Rationale**: Realistic for a first beta cohort; sizes the queue and runner without
  over-engineering. NFR-006a (95% of results < 30 s) holds at this load with ~2–5 s per run.
- **To confirm with the product owner** before launch; it does not change the architecture.

## R11. Internationalization readiness

- **Decision**: All interface strings in react-i18next resource files (`frontend/src/i18n/en/*.json`);
  content folders are partitioned by language (`content/en/…`); every content item has a `lang`
  field and a language-independent `id`; competencies, objectives and progress reference ids only,
  never text; dates and numbers formatted with `Intl` using the active locale.
- **Rationale**: Implements FR-054/FR-055: adding Spanish means adding `content/es/…` and
  `i18n/es/*.json` without schema or progress changes.

## R12. Hosting and deployment

- **Decision**: Deliver as three OCI images (frontend static assets served by a web server, API,
  runner) plus PostgreSQL, run locally with Docker Compose. The production hosting provider is
  deliberately not chosen in this plan; requirements on it: a Linux host able to run gVisor for the
  runner, managed PostgreSQL with backups, TLS termination, and SMTP-compatible email delivery.
- **Rationale**: Keeps the architecture provider-agnostic (Principle VI) and defers a cost decision
  that does not affect design. Recorded as an ADR to be taken before the first public deployment.

## R13. Delivery phasing (pending spec item)

- **Decision**: Deliver in increments that follow the spec priorities, so the sandbox never blocks
  learning content:
  1. **Increment 1 (P1)**: content model + validator, catalog, module reader, accounts, knowledge
     checks, basic progress (US1, US2, US6 catalog part).
  2. **Increment 2 (P2)**: dashboard and competency view (US3), challenges with runner and sandbox
     (US4).
  3. **Increment 3 (P3)**: laboratory player and comparison (US5), content governance features
     (US7: deprecations, version display, publish validation already in CI from increment 1).
  4. **Hardening**: accessibility audit, sandbox security suite, performance validation, release.
- **Rationale**: Each increment is independently demonstrable, matching the spec's independent
  tests; the MVP is complete only after increment 3 plus hardening.
