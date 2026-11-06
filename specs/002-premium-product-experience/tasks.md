---

description: "Task list for the Premium Product Experience"
---

# Tasks: Premium Product Experience

**Input**: Design documents from `/specs/002-premium-product-experience/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included. Constitution IV and S001 NFR-011 require automated tests for critical workflows and regressions, and the plan defines automated gates. Write each test before the code it covers, and see it fail first.

**Organization**: Phases follow the delivery increments in [plan.md](./plan.md#delivery-increments), which order stories by dependency. US3 and US4 are each split into two phases, because their navigation work must come before the public experience.

| Increment | Phases | Stories |
|-----------|--------|---------|
| 1. Visual foundation | 1–3 | US1 |
| 2. Navigation and routes | 4 | US4 (part), US3 (part) |
| 3. Public experience | 5–6 | US2, US5 |
| 4. Learning environment | 7–10 | US3, US6, US7, US8 |
| 5. Quality assurance | 11–12 | US4, all |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story from [spec.md](./spec.md) (US1–US8)
- **(human)**: Needs a person; cannot be completed by an automated agent

## Global rules for every task

- **Frontend only.** Do not change `backend/`, `runner/`, `content/`, `specs/001-agentic-academy-mvp/` or `frontend/nginx.conf` (FR-053, SC-005). If a task seems to need one of them, stop and raise it.
- Follow the contracts exactly: [design tokens](./contracts/design-tokens.md), [routes and shells](./contracts/routes-and-shells.md), [UI components](./contracts/ui-components.md), [public content](./contracts/public-content.md).
- Colors, spacing, type, radii and motion come only from tokens. No raw color outside `frontend/src/styles/tokens.css`. No JSX `style`, except data-driven custom properties on the allow-list.
- Every user-visible string, including accessible names, goes through react-i18next (S001 FR-055).
- Every interactive element is keyboard operable, with visible focus and an accessible name. Status is never conveyed by color alone (FR-049).
- Respect the frozen behavior and the test selectors in [UI components](./contracts/ui-components.md). If a selector must change, change its test in the same task.
- `GET /modules/{id}` records a content view: call it only when a learner opens that module.
- `/verify-email` and `/reset-password` must not move: emails link to them.
- Public copy must match the [claim register](./spec.md#claim-register). Never invent legal text, testimonials, prices, statistics or credentials.
- Do not describe evaluation as tamper-proof (S001 D1), and do not imply a certificate.
- Run commands from the repository root. On Windows, read the note in [quickstart.md](./quickstart.md#prerequisites) first.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, ADR, test projects and the CI job

- [X] T001 Add the dependencies `@fontsource-variable/geist`, `@fontsource-variable/geist-mono`, `@codemirror/view`, `@codemirror/language` and `@lezer/highlight` in `frontend/package.json` and `frontend/pnpm-lock.yaml`, keeping the lockfile valid for `pnpm --dir frontend install --frozen-lockfile` with pnpm 10, as used in CI; add no other dependency
- [X] T002 [P] Write ADR 0007 from research R1, R2, R3, R4 and R7 (plain CSS with cascade layers, no UI library, self-hosted fonts, JavaScript regex engine for highlighting with the measured evidence and the reason `wasm-unsafe-eval` was rejected, dark only) in `docs/adr/0007-frontend-design-system.md`
- [X] T003 Change `frontend/playwright.config.ts` to keep the `desktop` and `mobile-360` projects with `testIgnore` for `**/csp.spec.ts` and `**/visual.spec.ts`; add a `production` project with `testMatch: "**/csp.spec.ts"` and `baseURL` from `PROD_BASE_URL` (default `http://localhost:5173`), and a `visual` project with `testMatch: "**/visual.spec.ts"`; do not start `webServer` when `PLAYWRIGHT_NO_SERVERS=1`
- [X] T004 Update scripts in `frontend/package.json`: `e2e` runs only `--project=desktop --project=mobile-360`; add `e2e:production` (`playwright test --project=production`, for which the config starts no servers, since inline environment variables do not work in `pnpm` scripts on Windows) and `visual` (`playwright test --project=visual`)
- [X] T005 Add an `e2e` job in `.github/workflows/ci.yml`, on `runs-on: ubuntu-24.04` (pinned, because visual references depend on it), based on the backend job's PostgreSQL service: install uv and pnpm; `uv sync --project backend` and `--project runner`; `docker build -t academy-sandbox:dev runner/sandbox-image`; `pnpm --dir frontend install --frozen-lockfile`; `pnpm --dir frontend exec playwright install --with-deps chromium`; then `pnpm --dir frontend e2e` with `RUNNER_RUNTIME=runc`. Comment that `runc` proves behavior and not sandbox security. Set `continue-on-error: true` until T137

**Checkpoint**: The existing suite still gives 15 passed and 3 skipped locally, and the CI job has run.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tokens, gates, base styles, shared components and page metadata

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests

- [X] T006 [P] Write a failing unit test that parses `frontend/src/styles/tokens.css` and checks every pair in "Required pairings" of the tokens contract (text and syntax tokens ≥ 4.5:1 on each listed surface, `--on-accent` on `--accent`, `--on-danger` on `--danger`, `--border-control` and `--focus-ring` ≥ 3:1 on every surface, `--syntax-foreground` ≥ 4.5:1 on `--syntax-selection`) in `frontend/tests/unit/design/tokens.test.ts`
- [X] T007 [P] Write a failing unit test that scans `frontend/src/styles/**/*.css` and `frontend/src/**/*.tsx` for raw color values and `prefers-color-scheme`, excluding `tokens.css` and, until T047 only, `legacy.css`, and that checks the canvas color in `frontend/index.html` equals `--surface-canvas`, in `frontend/tests/unit/design/no-raw-values.test.ts`
- [X] T008 [P] Write failing component tests for `Button`, `Field`, `Alert`, `ProgressBar`, `Tabs`, `ConfirmDialog` and `Breadcrumb` per the components contract (names, states, `aria-describedby`, `aria-invalid`, arrow keys and roving `tabindex`, Escape cancels and focus returns; stub `HTMLDialogElement.showModal` where jsdom lacks it) in `frontend/tests/unit/ui/components.test.tsx`
- [X] T009 [P] Write a failing unit test for `usePageMeta` (sets `document.title` to `"<page> · Agentic Academy"`, updates the description) in `frontend/tests/unit/navigation/usePageMeta.test.tsx`
- [X] T010 Add an ESLint `no-restricted-syntax` rule for `JSXAttribute[name.name='style']` at `warn` level, with a comment naming the allow-list (data-driven custom properties only), in `frontend/eslint.config.js`; T047 raises it to `error`

### Styles

- [X] T011 Move `frontend/src/styles.css` to `frontend/src/styles/legacy.css` unchanged, and create `frontend/src/styles/index.css` declaring `@layer legacy, reset, tokens, base, layout, components, content, screens;` and importing each file into its layer; `legacy` is the lowest layer, and is temporary; update the import in `frontend/src/main.tsx`
- [X] T012 Create `frontend/src/styles/tokens.css` with every token named in the tokens contract, using the values in the spec's "Design Token Contract" and the contract's syntax table, plus `@font-face` rules for Geist and Geist Mono pointing at the package's Latin variable files (`font-display: swap`; italic loaded only when used) and fallback metric overrides, until T006 passes
- [X] T013 [P] Create `frontend/src/styles/reset.css` and `frontend/src/styles/base.css`: element defaults, type scale, links, `:focus-visible` per rule 3 of the tokens contract, `html { scroll-padding-top: var(--header-offset) }`, `prefers-reduced-motion` (rule 7) and `forced-colors` (rule 8)
- [X] T014 [P] Create `frontend/src/styles/layout.css` with the page container (`--layout-max`), `.reading` column (`--measure-wide`), with `--measure-prose` applied to prose elements only per rule 9 of the tokens contract, and grid helpers, plus empty, layered `frontend/src/styles/components.css`, `frontend/src/styles/content.css` and `frontend/src/styles/screens.css`
- [X] T015 Set `color-scheme: dark` and the canvas color in a small inline `style`, and add `<meta name="color-scheme" content="dark">` and `<meta name="theme-color">`, in `frontend/index.html`, until the canvas check in T007 passes

### Shared components

- [X] T016 [P] Create `Icon` with an inline SVG set (check, cross, warning, info, external link, arrows, and the four trace kinds), decorative by default with `aria-hidden`, in `frontend/src/components/ui/Icon.tsx`
- [X] T017 [P] Create `Button` and `LinkButton` (variants `primary`, `secondary`, `ghost`, `danger`; native `button` or router link; hover, active, focus and disabled states; at least 24 × 24 px, with primary actions 44 px tall on touch widths) in `frontend/src/components/ui/Button.tsx`
- [X] T018 [P] Create `Field` (label, optional hint, error linked through `aria-describedby`, `aria-invalid`), keeping accessible names equal to the label text, in `frontend/src/components/ui/Field.tsx`
- [X] T019 [P] Create `Alert` (tones `info`, `success`, `warning`, `danger`, always with icon and text; `role` passed by the caller) and `Badge` (same tones; never interactive) in `frontend/src/components/ui/Alert.tsx` and `frontend/src/components/ui/Badge.tsx`
- [X] T020 [P] Create `Card` (surface only; heading level chosen by the caller) and `ProgressBar` (`role="progressbar"`, name, value, text equivalent; width through the `--progress` custom property, on the style allow-list) in `frontend/src/components/ui/Card.tsx` and `frontend/src/components/ui/ProgressBar.tsx`
- [X] T021 [P] Create `Tabs` (ARIA tabs pattern, arrow keys, roving `tabindex`) in `frontend/src/components/ui/Tabs.tsx`
- [X] T022 [P] Create `ConfirmDialog` (native modal `dialog` with `role="alertdialog"`; focus in on open; Escape cancels; focus returns to the opener; optional typed confirmation that keeps the submit action disabled until it matches) in `frontend/src/components/ui/ConfirmDialog.tsx`
- [X] T023 [P] Create `Breadcrumb` (`nav` with a translated name and an ordered list) in `frontend/src/components/ui/Breadcrumb.tsx`
- [X] T024 [P] Create `usePageMeta` per the navigation protocol in `frontend/src/app/navigation/usePageMeta.ts`
- [X] T025 Create `PageHeader` (`h1` with `tabindex="-1"`, summary, metadata slot; calls `usePageMeta`) in `frontend/src/components/ui/PageHeader.tsx`
- [X] T026 Add the styles for all shared components, using only tokens, in `frontend/src/styles/components.css`, until T008 passes visually and in tests
- [X] T027 Evolve `Loading`, `EmptyState`, `ErrorState` and `OfflineBanner` onto `Alert`, `Icon`, `Button` and tokens, keeping names, `role` values and strings, in `frontend/src/components/states/index.tsx`
- [X] T028 [P] Add translations for shared components (`ui.*`, including `ui.mainNav`, `ui.breadcrumb`) in `frontend/src/i18n/en/common.json`

**Checkpoint**: Tokens and components exist and pass their tests. The application looks unchanged, because screens still use legacy styles.

---

## Phase 3: User Story 1 — Work in one coherent, legible environment (Priority: P1) 🎯 MVP · Increment 1

**Goal**: Every existing screen uses the design system, dark only. Code, diagrams and editor are readable and share the tokens. No flow changes.

**Independent Test**: Quickstart P1 and P10. All existing end-to-end tests still pass.

### Tests for User Story 1

- [X] T029 [P] [US1] Add `expectNoSeriousA11yViolations` (fails on critical and serious findings) to `frontend/tests/e2e/fixtures.ts`, keeping the existing helper
- [X] T030 [P] [US1] Write a failing end-to-end test: with `colorScheme` light and dark, a module, a challenge and the dashboard render the same canvas, code and editor backgrounds; plain code in the editor has at least 4.5:1; the module and challenge pass `expectNoSeriousA11yViolations` (baseline: 13 findings); control states are distinct, in `frontend/tests/e2e/premium/us1-visual-system.spec.ts`
- [X] T031 [P] [US1] Write a failing test for the production project: listen for `securitypolicyviolation` through an init script; sign in; assert that `figure.code-block .shiki` exists on a lesson, `.diagram svg` renders, the editor works, fonts come from the origin, and no violation occurred, in `frontend/tests/e2e/csp.spec.ts`; it runs against the nginx image on port 5173, so the development server must be stopped first
- [X] T032 [P] [US1] Write a failing unit test: the highlighter returns output using `--code-` variables with no WebAssembly engine, for each of the five languages, in `frontend/tests/unit/content/highlighter.test.ts`

### Content components

- [X] T033 [US1] Create a single highlighter with `createHighlighterCore`, `createJavaScriptRegexEngine`, `createCssVariablesTheme` and only the Python, JSON, Bash, YAML and TypeScript grammars, in `frontend/src/components/content/highlighter.ts`, using imports `shiki/core`, `shiki/engine/javascript` and `shiki/langs/*`
- [X] T034 [US1] Use the highlighter in `frontend/src/components/content/CodeBlock.tsx`: remove the `themes` light and dark options; keep the language label, copy, annotations, internal scroll with `tabindex="0"`, plain fallback and `figure.code-block`; move "Line {n}" to translations
- [X] T035 [US1] Change `frontend/src/components/content/Diagram.tsx` to `theme: "base"` with `themeVariables` read from resolved tokens through `getComputedStyle` (use the variable set proven in research R6), remove `matchMedia`, and keep `securityLevel: "strict"`, accessible name, caption and fallback
- [X] T036 [US1] Map `--code-*` to `--syntax-*`, and style code blocks, diagrams, callouts, tables and lesson prose, in `frontend/src/styles/content.css`
- [X] T037 [US1] Apply `Icon`, `Badge` and tokens to `frontend/src/components/content/Callouts.tsx`, keeping labels, `aria-label` and `role="note"`
- [X] T038 [US1] Change `frontend/src/features/challenge/Editor.tsx`: `theme="none"`, an `EditorView.theme` using `var(--…)` values marked dark, a `HighlightStyle` using `--syntax-*`, `EditorView.contentAttributes` for `aria-label` on the editable element, and "(read-only)" moved to translations; keep `.cm-content`, tabs, line numbers and autosave wiring

### Move existing screens onto the design system (no flow or route changes)

For each task: use shared components, remove all inline `style`, remove legacy classes, and keep the listed selectors.

- [X] T039 [US1] Move the frame and not-found page in `frontend/src/app/Layout.tsx` and `frontend/src/app/NotFound.tsx`, moving "Main" to `ui.mainNav`
- [X] T040 [US1] Move all authentication and account pages in `frontend/src/features/auth/pages.tsx`
- [X] T041 [US1] Move the catalog and path pages in `frontend/src/features/catalog/CatalogPage.tsx` and `frontend/src/features/catalog/PathPage.tsx`
- [X] T042 [US1] Move the dashboard, competencies, completion and reset views in `frontend/src/features/dashboard/DashboardPage.tsx`, `frontend/src/features/dashboard/CompetenciesPage.tsx`, `frontend/src/features/dashboard/PathCompletion.tsx` and `frontend/src/features/dashboard/ResetPathDialog.tsx`, using `ProgressBar`
- [X] T043 [US1] Move module views in `frontend/src/features/module/ModulePage.tsx`, `frontend/src/features/module/LessonView.tsx` and `frontend/src/features/module/ModuleStatus.tsx`, using `Breadcrumb`
- [X] T044 [US1] Move knowledge-check views in `frontend/src/features/knowledge-check/KnowledgeCheckPage.tsx` and `frontend/src/features/knowledge-check/questions/QuestionInput.tsx`, keeping `.question`, `label.option` and `ol.ordering li`
- [X] T045 [US1] Move the challenge page in `frontend/src/features/challenge/ChallengePage.tsx`, keeping `#result`
- [X] T046 [US1] Move the laboratory in `frontend/src/features/lab/LabPage.tsx` and `frontend/src/features/lab/CompareView.tsx`, keeping button names and labelled comparison cards
- [X] T047 [US1] Delete `frontend/src/styles/legacy.css` and its layer; remove the exclusion in `frontend/tests/unit/design/no-raw-values.test.ts`; raise the lint rule to `error` in `frontend/eslint.config.js`; verify that inline styles remain only on the allow-list (SC-010; baseline 64)
- [X] T048 [US1] Run the full end-to-end suite and the build, then stop the development server and run the production test against `docker compose up --build api web`; record the new asset count, compared with the 344 baseline files, in the research note R4 of `specs/002-premium-product-experience/research.md`

**Checkpoint**: US1 can ship alone. The worst measured defects are gone, including production highlighting (FR-054).

---

## Phase 4: User Story 4 and User Story 3 (part) — Navigation and routes (Priority: P1) · Increment 2

**Goal**: Shells, the route table, redirects, titles, focus, scroll and working lesson links.

**Independent Test**: Quickstart P3 and P5 steps 1–2. SC-007 and SC-008.

### Tests

- [X] T049 [P] [US4] Write a failing unit test for the route table in `frontend/tests/unit/navigation/routes.test.ts`, listing the expected routes in one array: paths and shells equal the routes contract, except `/privacy`, `/terms` and `/knowledge-checks/:checkId/history`, which T077 and T099 add to the array; titles are unique, with the `/sign-up` redirect exempt; and `/verify-email` and `/reset-password` are present
- [X] T050 [P] [US4] Write a failing end-to-end test: `/sign-up?x=1` redirects to `/register?x=1`; after in-app navigation the title changes and focus is on the `h1`; scroll resets, but back navigation does not force it; skip link, offline notice and session-expiry warning exist in each shell; a signed-in learner does not see "Sign in" flash; every navigation link and "Sign out" stay visible at 360 px; not-found links to `/` and `/curriculum`; `/sign-in?next=` still returns; sign-out lands on `/`, in `frontend/tests/e2e/premium/us4-navigation.spec.ts`
- [X] T051 [P] [US3] Write a failing end-to-end test: "Review in the lesson" and a direct `#lesson-…` load bring the section into view, unobscured and focused, and it stays there after code and diagrams render; an unknown fragment raises no error; no identifier repeats on the module page, in `frontend/tests/e2e/premium/us3-lesson-links.spec.ts`
- [X] T052 [US4] Change `frontend/tests/e2e/us6-catalog.spec.ts` to open `/curriculum` rather than `/`, as recorded in the spec's conflicts table

### Implementation

- [X] T053 [US4] Extend `RouteDef` with `shell` (`public` | `learning` | `session`) and `titleKey` per data-model §2, and add all routes from the routes contract, except `/privacy` and `/terms` (T077) and `/knowledge-checks/:checkId/history` (T099), and with `/` temporarily rendering the catalog until T075, in `frontend/src/app/routes.ts`
- [X] T054 [US4] Add document titles (`meta.*`) and descriptions in `frontend/src/i18n/en/common.json`
- [X] T055 [US4] Create `AppFrame` (skip link, `main#main`, offline notice, session-expiry warning and sign-in link, footer slot, `RouteFocus`), moving this behavior out of `Layout.tsx`, in `frontend/src/app/shells/AppFrame.tsx`
- [X] T056 [US4] Create `RouteFocus` per the navigation protocol: on PUSH or REPLACE with no fragment, scroll to top and, after the `h1` exists or after 3 s using `main`, focus it; never on first load; leave POP to the browser, in `frontend/src/app/navigation/RouteFocus.tsx`
- [X] T057 [P] [US4] Create `PublicShell` (brand, Curriculum, Sign in, Create account, wrapping at narrow widths with no collapsed menu; full footer slot) in `frontend/src/app/shells/PublicShell.tsx`
- [X] T058 [P] [US4] Create `LearningShell` (brand, My progress, Curriculum, Account, and "Sign out" kept as a visible `button`, wrapping at narrow widths with no collapsed menu; footer with the product name, to which T078 adds legal links; no marketing content) in `frontend/src/app/shells/LearningShell.tsx`
- [X] T059 [US4] Rework `frontend/src/app/App.tsx` to resolve shells, including `session` from `useMe` with navigation held empty and its space kept while the session is unknown; make authentication pages lazy; add `Navigate replace` from `/sign-up` to `/register` keeping the query string; delete `frontend/src/app/Layout.tsx`
- [X] T060 [US4] Apply the link changes in the contract's "Link destinations that change" table (except evidence and laboratory links, T100 and T122) in `frontend/src/app/shells/PublicShell.tsx`, `frontend/src/app/NotFound.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx` and `frontend/src/features/auth/pages.tsx`
- [X] T061 [US4] Add the notice with a link to `/dashboard` for signed-in learners on `/sign-in` and `/register`, in `frontend/src/features/auth/pages.tsx`
- [X] T062 [US4] Use `PageHeader` or `usePageMeta` on every page, so that each route has a unique title, including API titles for path, module, challenge and scenario, in `frontend/src/features/**/*.tsx`
- [X] T063 [US3] Create `useFragmentTarget` per the fragment protocol (scroll and focus after render; re-apply on size change until the first user scroll, key or pointer input, or at most 3 s; ignore unknown fragments; no smooth scroll under reduced motion) in `frontend/src/app/navigation/useFragmentTarget.ts`
- [X] T064 [US3] Use the hook in `frontend/src/features/module/ModulePage.tsx`; change contents links to router links; in `frontend/src/features/module/LessonView.tsx` keep `section#lesson-<id>`, use `h2#lesson-<id>-title` and point `aria-labelledby` at it
- [X] T065 [US4] Update the e2e selectors affected only by titles or moved links in `frontend/tests/e2e/`, and rerun the full suite

**Checkpoint**: All Spec 001 tests pass with the catalog at `/curriculum`. Lesson links work.

---

## Phase 5: User Story 2 — Understand the offer and decide to join (Priority: P1) · Increment 3

**Goal**: The public landing page, legal availability and metadata.

**Independent Test**: Quickstart P2 and P11. SC-006 and SC-012.

### Tests for User Story 2

- [X] T066 [P] [US2] Write a failing unit test scanning `frontend/src/i18n/en/marketing.json` and public keys in `common.json` for the forbidden terms in the public content contract, with an explicit, commented allow-list, in `frontend/tests/unit/marketing/claims.test.ts`
- [X] T067 [P] [US2] Write a failing unit test: each showcase excerpt's strings appear in its source file under `content/`, and no source path contains `solution/`, in `frontend/tests/unit/marketing/excerpts.test.ts`
- [X] T068 [P] [US2] Write a failing unit test for legal availability, using injected file maps: absent gives `unavailable`, hidden links and not found; present gives links; `publisher.json` must have `name` and `contact_email`, in `frontend/tests/unit/legal/availability.test.ts`
- [X] T069 [P] [US2] Write a failing end-to-end test: all sections and both actions exist; the first viewport has the value proposition and actions at 360 px; curriculum data matches `GET /catalog`; laboratory text states replay and no model call; with the catalog blocked, other sections remain and a retry appears; a signed-in learner sees "Go to my progress" with no redirect; no legal links appear; `expectNoSeriousA11yViolations`, in `frontend/tests/e2e/premium/us2-landing.spec.ts`
- [X] T070 [P] [US2] Write a size check: build, then sum the compressed entry, its landing chunks, CSS and fonts for `/`, fail above 300 KB, and fail if the editor, diagram, highlighter or Markdown chunks are loaded by `/`, in `frontend/scripts/check-landing-size.mjs`, exposed as the `size` script in `frontend/package.json`

### Implementation for User Story 2

- [X] T071 [US2] Write `frontend/src/i18n/en/marketing.json`: every statement mapped to a claim register entry; excerpts with their source path; no fixed numbers, titles or dates; loaded with the landing chunk through `addResourceBundle`
- [X] T072 [P] [US2] Create the hero and closing action, with actions per the contract's "Calls to action" table, in `frontend/src/features/marketing/Hero.tsx` and `frontend/src/features/marketing/ClosingAction.tsx`
- [X] T073 [P] [US2] Create the methodology section (study, check understanding, build code, inspect executions) in `frontend/src/features/marketing/Methodology.tsx`
- [X] T074 [P] [US2] Create curriculum, competencies and prerequisites sections, using the same query keys as the catalog and path pages, the first `status: "available"` path, and the fallbacks in the contract's table, in `frontend/src/features/marketing/CurriculumSection.tsx`, `frontend/src/features/marketing/CompetenciesSection.tsx` and `frontend/src/features/marketing/PrerequisitesSection.tsx`
- [X] T075 [US2] Create the challenge and laboratory showcases with static markup and text alternatives, assemble `frontend/src/features/marketing/LandingPage.tsx` (with `frontend/src/features/marketing/ChallengeShowcase.tsx` and `frontend/src/features/marketing/LabShowcase.tsx`), and point `/` to it in `frontend/src/app/routes.ts`
- [X] T076 [US2] Add `.public-hero` and `.public-showcase`, full-width sections and responsive rules, using only tokens and gradients only in those two classes, in `frontend/src/styles/screens.css`
- [X] T077 [US2] Create build-time availability through `import.meta.glob` over the named files only (`frontend/src/legal/en/{privacy.md,terms.md,publisher.json}`), and `LegalPage` (renders through `Markdown`, loaded only on those routes; not found when absent), add `/privacy` and `/terms` to `frontend/src/app/routes.ts` and to the expected array in `frontend/tests/unit/navigation/routes.test.ts`, in `frontend/src/features/legal/availability.ts` and `frontend/src/features/legal/LegalPage.tsx`; add `frontend/src/legal/en/README.md` stating that only the owner supplies these files
- [X] T078 [US2] Create the footer per FR-022 and FR-022a (product name; curriculum, registration and sign-in links; publisher, contact and legal links only when available) in `frontend/src/app/shells/PublicFooter.tsx`; add privacy, terms and contact, only when available, to the footer in `frontend/src/app/shells/LearningShell.tsx`; and add legal links to registration, with no acceptance recorded, in `frontend/src/features/auth/pages.tsx`
- [X] T079 [US2] Add default title and description, `og:*` and `twitter:card` tags and a `<noscript>` message in `frontend/index.html`; add a small Vite HTML transform that fills `og:image` and `og:url` from `VITE_PUBLIC_ORIGIN`, and omits them when unset, in `frontend/vite.config.ts`; add the build argument in `frontend/Dockerfile`
- [X] T080 [P] [US2] Add the favicon and a 1200 × 630 share image with only the product name and a claim from the register, in `frontend/public/`
- [X] T081 [US2] Run `pnpm --dir frontend size` and record the measured landing size against the 190 KB estimate in `specs/002-premium-product-experience/research.md`

**Checkpoint**: `/` is the landing page. Public launch stays blocked until the owner supplies legal text (SC-019).

---

## Phase 6: User Story 5 — Evaluate the curriculum and a learning path (Priority: P2) · Increment 3

**Goal**: A polished `/curriculum` and path page for visitors and learners.

**Independent Test**: Quickstart P6.

### Tests for User Story 5

- [ ] T082 [P] [US5] Write a failing end-to-end test, signed out and signed in: order and level groups; all data of S001 FR-001; a planned path is distinct and not startable, with no date; a visitor sees a call to register or sign in, and a learner sees module statuses and a study action; sign-in returns to the path; the self-assessment makes no request; `expectNoSeriousA11yViolations` at each width, in `frontend/tests/e2e/premium/us5-curriculum.spec.ts`

### Implementation for User Story 5

- [ ] T083 [US5] Redesign `frontend/src/features/catalog/CatalogPage.tsx` (FR-018) with roadmap order, level groups, and a clearly different treatment for planned paths (badge, no primary action), keeping the heading "Curriculum", level headings and "Not yet available"
- [ ] T084 [US5] Redesign `frontend/src/features/catalog/PathPage.tsx` (FR-019) for both audiences, keeping every field, the local-only self-assessment and "This path is planned and cannot be started yet."; add a `/register` action for visitors, and return through `next` for sign-in
- [ ] T085 [US5] Add curriculum and path layout in `frontend/src/styles/screens.css`

**Checkpoint**: US2 and US5 complete the public experience.

---

## Phase 7: User Story 3 — Study a lesson for a long session (Priority: P1) · Increment 4

**Goal**: Comfortable reading, orientation and reliable lesson view recording. Links are already fixed in Phase 4.

**Independent Test**: Quickstart P5.

### Tests for User Story 3

- [ ] T086 [P] [US3] Write a failing end-to-end test at 360 × 780: scrolling through the Module 1 lesson that measures about 3,786 px sends `?lesson=` once and "Continue" returns to it; at 1440 px, the median prose line is 65–75 characters, no line exceeds 90, and code uses the wider column; lessons never brought into view send no `?lesson=` request, while a lesson opened through a direct link is recorded; contents show the current lesson with `aria-current="location"`; wide code scrolls in its own region, with no page scroll; lesson headings are `h2` with `h3` subsections, in `frontend/tests/e2e/premium/us3-reading.spec.ts`
- [ ] T087 [P] [US3] Add failing unit tests that lesson headings render one level lower and tables are wrapped in a keyboard-scrollable region, in `frontend/tests/unit/markdown.test.ts`

### Implementation for User Story 3

- [ ] T088 [US3] Render lesson headings one level lower and wrap tables in a focusable scroll region, without changing sanitization or directives, in `frontend/src/components/content/markdownParser.ts`
- [ ] T089 [US3] Replace the 25% visibility rule with a central viewport band (for example `rootMargin: "-40% 0px -40% 0px"`, threshold 0), reporting the current lesson and sending the same request once, in `frontend/src/features/module/LessonView.tsx`
- [ ] T090 [US3] Create module contents: all lessons, practice, adjacent modules and path overview, and current lesson from T089, without per-lesson completion marks, in `frontend/src/features/module/ModuleContents.tsx`
- [ ] T091 [US3] Redesign `frontend/src/features/module/ModulePage.tsx` with a reading column and contents: sticky side rail at 1200 px or wider, and a compact sticky bar below that only when the viewport is at least 500 px tall; set `--header-offset` accordingly; keep all current sections and link names; no promotional content
- [ ] T092 [US3] Add module layout, keeping the prose measure and the wider column for code, diagrams and tables (FR-029), in `frontend/src/styles/screens.css`

**Checkpoint**: Reading works at every width, including the long lesson.

---

## Phase 8: User Story 6 — Get oriented on the dashboard (Priority: P2) · Increment 4

**Goal**: A clear home for learners, evidence that can be reviewed, and safe confirmations.

**Independent Test**: Quickstart P7.

### Tests for User Story 6

- [ ] T093 [P] [US6] Write a failing end-to-end test: for a learner with progress, active path, competency progress, next step, "Continue" and the summary of completed and pending modules are in the viewport at 1280 × 800; the new-learner state; a knowledge-check evidence link opens the review with no `POST …/attempts`; reset and deletion keep typed confirmation, Escape cancels and focus returns, in `frontend/tests/e2e/premium/us6-dashboard.spec.ts`
- [ ] T094 [P] [US6] Write failing component tests for the review page: date, version, score, passed state, and per-question result, explanation and lesson link; the empty state; no call to start an attempt, in `frontend/tests/unit/knowledge-check/HistoryPage.test.tsx`

### Implementation for User Story 6

- [ ] T095 [US6] Redesign `frontend/src/features/dashboard/DashboardPage.tsx`, keeping all fields of FR-030 and the listed headings and links, with a summary of completed and pending modules from `modules` near the top and the full list below it; progress expresses demonstrated competencies only
- [ ] T096 [US6] Redesign `frontend/src/features/dashboard/PathCompletion.tsx` with no certificate or credential implied, and `frontend/src/features/dashboard/CompetenciesPage.tsx` with a keyboard-scrollable table at narrow widths
- [ ] T097 [US6] Move path reset onto `ConfirmDialog`, keeping "RESET" and its warning, in `frontend/src/features/dashboard/ResetPathDialog.tsx`
- [ ] T098 [US6] Move account deletion onto `ConfirmDialog`, keeping "DELETE" and its warning, in `frontend/src/features/auth/pages.tsx`
- [ ] T099 [US6] Create the read-only review at `/knowledge-checks/:checkId/history`, from `GET /knowledge-checks/{id}/attempts/history`, numbering questions because the endpoint returns no prompts, and never starting an attempt, in `frontend/src/features/knowledge-check/HistoryPage.tsx`; add the route in `frontend/src/app/routes.ts` and to the expected array in `frontend/tests/unit/navigation/routes.test.ts`
- [ ] T100 [US6] Point knowledge-check evidence links to the review in `frontend/src/features/dashboard/CompetenciesPage.tsx` and `frontend/src/features/dashboard/PathCompletion.tsx`, and show `check.history` from the result view in `frontend/src/features/knowledge-check/KnowledgeCheckPage.tsx`
- [ ] T101 [US6] Add dashboard layout in `frontend/src/styles/screens.css`

**Checkpoint**: S001 FR-041 is met, with no contract change.

---

## Phase 9: User Story 7 — Practise with knowledge checks and code challenges (Priority: P2) · Increment 4

**Goal**: A focused practice layout, with evaluation behavior frozen.

**Independent Test**: Quickstart P8. Existing `us2-knowledge-check` and `us4-challenge` tests pass unchanged.

### Tests for User Story 7

- [ ] T102 [P] [US7] Write a failing end-to-end test: at 1280 px, problem context and editor are in view together; at 360 px both are reachable; Esc then Tab leaves the editor, and the hint is visible; statuses are announced; code stays after a stopped run and when evaluation is unavailable, in `frontend/tests/e2e/premium/us7-practice.spec.ts`

### Implementation for User Story 7

- [ ] T103 [US7] Redesign `frontend/src/features/knowledge-check/KnowledgeCheckPage.tsx`, keeping every frozen behavior, and move the unanswered confirmation onto `ConfirmDialog`
- [ ] T104 [US7] Give each state in `frontend/src/features/knowledge-check/questions/QuestionInput.tsx` a clear selected, disabled and answered appearance, keeping selectors and accessible names
- [ ] T105 [US7] Use `Tabs`, and add the visible, translated hint "Press Esc, then Tab, to leave the editor", in `frontend/src/features/challenge/Editor.tsx`
- [ ] T106 [US7] Redesign `frontend/src/features/challenge/ChallengePage.tsx`: two columns at 1280 px or wider (scrollable context, editor and actions), stacked below; keep autosave, drafts, hints, reset, polling, history, reference explanation and `#result`
- [ ] T107 [US7] Redesign result and status presentation for every status in `frontend/src/features/challenge/ChallengePage.tsx` (`ResultView`), with icon and text per criterion, keeping messages, and with no copy calling evaluation tamper-proof
- [ ] T108 [US7] Add practice layouts in `frontend/src/styles/screens.css`

**Checkpoint**: Spec 001 V2, V4, V7.2 and V7.3 pass.

---

## Phase 10: User Story 8 — Explore an execution in the laboratory (Priority: P3) · Increment 4

**Goal**: A clear replay in the same system, with human approval impossible to bypass.

**Independent Test**: Quickstart P9. Existing `us5-lab` test passes unchanged.

### Tests for User Story 8

- [ ] T109 [P] [US8] Add failing unit tests to `frontend/tests/unit/lab/player.test.ts`: `maxReachableIndex` returns the first undecided `approval_request`, or the last element; `jump` beyond it clamps; after `decide`, later steps of that branch are reachable, for both branches
- [ ] T110 [P] [US8] Write a failing end-to-end test: every step is listed; steps beyond a pending approval are disabled and cannot be reached; Escape returns focus to the controls with the decision pending; kinds show text and icon; the return link goes to the module from a module link, and to the dashboard on a direct visit; the comparison is understandable at 360 px; no request leaves the origin, in `frontend/tests/e2e/premium/us8-lab.spec.ts`

### Implementation for User Story 8

- [ ] T111 [US8] Add `maxReachableIndex(scenario, state)` per data-model §5, and clamp `jump` to it, in `frontend/src/features/lab/player.ts`
- [ ] T112 [US8] Create a stepper listing every step with number and kind icon; unreachable steps are disabled and explain why, in `frontend/src/features/lab/Stepper.tsx`
- [ ] T113 [US8] Redesign `frontend/src/features/lab/LabPage.tsx` with the stepper and element kinds by text and icon, keeping button names, the `Step N of M` status, educational labeling, failure notes and client-side replay
- [ ] T114 [US8] Make the approval panel inline and non-modal, with `role="alertdialog"` and its current name; move focus in when it appears; Escape returns focus to the controls without deciding, in `frontend/src/features/lab/LabPage.tsx`
- [ ] T115 [US8] Redesign `frontend/src/features/lab/CompareView.tsx`, keeping labelled cards, counts and marked unique steps, with marking by text as well as color
- [ ] T116 [US8] Add laboratory layout, using `--accent-secondary` only for highlights, in `frontend/src/styles/screens.css`
- [ ] T117 [US8] Show the replay statement and recording details clearly, with no implication of live model calls, keeping strings tested today, in `frontend/src/features/lab/LabPage.tsx`
- [ ] T118 [US8] Keep autoplay user-initiated and pausable, with no smooth scroll under reduced motion, in `frontend/src/features/lab/LabPage.tsx`
- [ ] T119 [US8] Read `location.state.from` (`from.moduleId`, `from.moduleTitle`) for the return link, falling back to `/dashboard`, in `frontend/src/features/lab/LabPage.tsx`

### Link laboratories from modules

- [ ] T120 [US8] Keep laboratories reachable only from modules, and add no global index (FR-037), by verifying `frontend/src/features/module/ModuleStatus.tsx` lists them
- [ ] T121 [US8] Add translations for the stepper, approval hints and return link in `frontend/src/i18n/en/common.json`
- [ ] T122 [US8] Pass navigation state `{ from: { moduleId, moduleTitle } }` on laboratory links in `frontend/src/features/module/ModuleStatus.tsx`

**Checkpoint**: All stories are functionally complete. Spec 001 V5 passes.

---

## Phase 11: User Story 4 (completion) — Every device and assistive technology (Priority: P1) · Increment 5

**Goal**: Prove accessibility, responsiveness and states on every route.

**Independent Test**: Quickstart P4. SC-001, SC-002, SC-009 and SC-011.

### Automated

- [ ] T123 [P] [US4] Write an accessibility matrix: for every route in the routes contract and each reachable state in data-model §8, `expectNoSeriousA11yViolations` at 360 px and 1280 px, in `frontend/tests/e2e/premium/a11y-matrix.spec.ts`
- [ ] T124 [P] [US4] Write a responsive test: no horizontal page scroll on every route at 320, 360, 768, 1024, 1440 and 2560 CSS px, and at 640 px width as a stand-in for 200% zoom of 1280 px, excepting code, tables and traces, in `frontend/tests/e2e/premium/responsive.spec.ts`
- [ ] T125 [P] [US4] Write a test with `reducedMotion: "reduce"` and `forcedColors: "active"`: no running non-essential animation; focus, control boundaries and statuses are perceivable, in `frontend/tests/e2e/premium/preferences.spec.ts`
- [ ] T126 [P] [US4] Write a test that interactive targets measure at least 24 × 24 CSS px on key screens, and that a focused element is not hidden by a sticky bar, in `frontend/tests/e2e/premium/targets.spec.ts`
- [ ] T127 [P] [US4] Write component tests for loading, empty, error and success on each view in data-model §8 that lacks one, in `frontend/tests/unit/states/views.test.tsx`, and end-to-end tests for the spec's edge cases in `frontend/tests/e2e/premium/edge-cases.spec.ts`: JavaScript disabled shows the product name and message; a catalog that is empty or only planned implies no available content; long unbroken titles, identifiers and emails do not break layouts; font requests that fail leave text visible; a diagram that fails to render leaves its source and text alternative readable
- [ ] T128 [US4] Fix every finding from T123–T127 in the affected files under `frontend/src/`, recording anything intentionally left open in `docs/accessibility/audit-premium.md`

### Visual references

- [ ] T129 [US4] Write visual tests for each route at 360, 768 and 1280 px and the states in data-model §8, using the seeded learner and disabled animation, in `frontend/tests/e2e/visual.spec.ts`, and run them in the `e2e` job in `.github/workflows/ci.yml`
- [ ] T130 [US4] Create a manual (`workflow_dispatch`) workflow on `ubuntu-24.04`, with the `e2e` job's setup, that runs `pnpm --dir frontend visual --update-snapshots` and uploads the references as an artifact, in `.github/workflows/visual-references.yml`; run it, and commit the approved files to `frontend/tests/e2e/visual.spec.ts-snapshots/`, documenting the process in `specs/002-premium-product-experience/quickstart.md`
- [ ] T131 [US4] (human) Review and approve every visual reference, including the typeface choice, confirming or changing it in `frontend/src/styles/tokens.css` (a new family requires measuring `--measure-prose` again, research R20), and record the decision in `docs/adr/0007-frontend-design-system.md`

### Manual audit

- [ ] T132 [US4] (human) Run the keyboard walkthrough, NVDA with Firefox, VoiceOver with Safari, 200% zoom, 320 px, text spacing, reduced motion and forced colors from quickstart P4, recording results in `docs/accessibility/audit-premium.md`; this also satisfies S001 T123
- [ ] T133 [US4] Fix blocking issues from T132 in the affected files under `frontend/src/`, and re-verify them in `docs/accessibility/audit-premium.md`

**Checkpoint**: SC-001, SC-002, SC-003, SC-009 and SC-011 are met.

---

## Phase 12: Polish & Cross-Cutting Concerns

- [ ] T134 (human) Review every public statement against the claim register, and record the result (SC-006) in `docs/content-review/public-claims.md`
- [ ] T135 Extend `frontend/tests/e2e/perf.spec.ts` to measure the landing page (readable < 2 s p95) and to assert that text stays visible while a font response is delayed; run it with the size check (SC-012, SC-013), compare with the baseline (module 1,168 ms p95, feedback 140 ms p95) and record the results in `docs/performance/premium.md`
- [ ] T136 Verify that `git diff --stat claude/gifted-davinci-t1hlbh -- backend runner content specs/001-agentic-academy-mvp frontend/nginx.conf` is empty (SC-005), and that all Spec 001 V1–V7 pass, with V1 step 1 replaced (FR-052, SC-004), recording the result in `docs/performance/premium.md`
- [ ] T137 Remove `continue-on-error` from the `e2e` job in `.github/workflows/ci.yml`, once it has been stable for several runs
- [ ] T138 (human) Run moderated testing with at least 5 target developers (quickstart P12; SC-014–SC-018), recording results and whether to revisit dark only in `docs/usability/premium.md`
- [ ] T139 [P] Update `README.md` with the design system, new routes, production check, and the Windows runner note
- [ ] T140 [P] Write the checklist for opening public registration from the contract's "Public launch gate" (legal files, links, `VITE_PUBLIC_ORIGIN`, S001 T121), in `docs/release/public-launch-checklist.md`
- [ ] T141 Run every scenario in `specs/002-premium-product-experience/quickstart.md` from a clean environment, and fix any drift between the documents and behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks all stories.
- **US1 (Phase 3)**: depends on Foundational. T047 needs T039–T046.
- **Navigation (Phase 4)**: depends on US1, because it replaces the frame moved in T039.
- **US2 (Phase 5) and US5 (Phase 6)**: depend on Phase 4; independent of each other, apart from `screens.css`.
- **US3 (Phase 7)**: depends on Phase 4 (T063, T064).
- **US6, US7, US8 (Phases 8–10)**: depend on Phase 4; independent of each other and of US3, apart from `screens.css`.
- **US4 completion (Phase 11)**: depends on all stories, as it tests the final screens.
- **Polish (Phase 12)**: depends on Phase 11.

### User Story Dependencies

| Story | Depends on | Notes |
|-------|-----------|-------|
| US1 | Foundational | Ships alone |
| US4 (navigation) | US1 | Needed by every later story |
| US3 (links) | Foundational, US1 | Done alongside US4 navigation |
| US2 | US4 navigation | Replaces the temporary `/` |
| US5 | US4 navigation | Catalog already at `/curriculum` |
| US3 (reading) | US3 links | — |
| US6 | US4 navigation | T098 touches authentication pages after T078 |
| US7 | US1 | Editor themed in T038 |
| US8 | US4 navigation | T122 touches module links |
| US4 (completion) | All | Final gate |

### Within Each Story

Tests first (must fail) → logic → components → screens → styles. Run the full end-to-end suite before closing a phase.

### Parallel Opportunities

- Setup: T002 alongside the others.
- Foundational: T006–T009; T013–T014; T016–T024; T028.
- US1: T029–T032.
- Navigation: T049–T051; T057–T058.
- US2: T066–T070; T072–T074; T080.
- US5 to US8: tests within each story. After Phase 4, the six story phases can proceed in parallel, with care on `screens.css`.
- US4 completion: T123–T127.
- Polish: T139, T140.

`frontend/src/styles/screens.css` and `frontend/src/i18n/en/common.json` are shared: tasks touching them should add separate, labeled sections, and are not marked [P].

---

## Parallel Example: Foundational components

```bash
Task: "Create Button and LinkButton in frontend/src/components/ui/Button.tsx"
Task: "Create Field in frontend/src/components/ui/Field.tsx"
Task: "Create Tabs in frontend/src/components/ui/Tabs.tsx"
Task: "Create ConfirmDialog in frontend/src/components/ui/ConfirmDialog.tsx"
Task: "Create Breadcrumb in frontend/src/components/ui/Breadcrumb.tsx"
```

## Parallel Example: User Story 2 tests

```bash
Task: "Claims scan in frontend/tests/unit/marketing/claims.test.ts"
Task: "Excerpt check in frontend/tests/unit/marketing/excerpts.test.ts"
Task: "Legal availability in frontend/tests/unit/legal/availability.test.ts"
Task: "Landing end-to-end in frontend/tests/e2e/premium/us2-landing.spec.ts"
```

---

## Implementation Strategy

### MVP first (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational.
2. Phase 3 (US1) → **stop and validate** with quickstart P1 and P10.
3. This can already ship: the product looks professional, and production highlighting and editor legibility are fixed.

### Incremental delivery

1. **Increment 1**: US1.
2. **Increment 2**: navigation, routes and lesson links. The catalog moves to `/curriculum`, and `/` still shows the catalog.
3. **Increment 3**: US2 and US5. `/` becomes the landing page.
4. **Increment 4**: US3, US6, US7 and US8, in any order.
5. **Increment 5**: accessibility matrix, visual references, manual audit, moderated testing.

Public registration opens only after the launch gate (T140, SC-019), which is separate from finishing this work.

### Human tasks

T131, T132, T134 and T138 need people. Schedule them early, since T132 and T134 gate release.
