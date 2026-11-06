# Implementation Plan: Premium Product Experience

**Branch**: `002-premium-product-experience` | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-premium-product-experience/spec.md`

## Summary

Turn the existing MVP into a polished commercial product without touching what runs behind the browser. All implementation work is in `frontend/`, plus one CI job and documentation.

Technical approach (see [research.md](./research.md)):

- **One visual system**: semantic tokens in plain CSS with cascade layers, dark only, self-hosted Geist fonts, and a small set of own components over native elements. No UI library.
- **Code, diagrams and editor share the tokens**: CSS-variable theme for code, resolved tokens for diagrams, and a token-based theme for the editor.
- **A defect fixed along the way**: code highlighting silently fails under the production security policy, because WebAssembly is blocked. The JavaScript regex engine gave identical output on all published code, so the policy stays as it is.
- **Marketing and learning shells** on one `AppFrame`, with `/` as the landing page and the catalog at `/curriculum`.
- **Navigation that works for everyone**: page titles, focus, scroll and working lesson links, under one protocol.
- **Honest public content**: live data for all numbers, a claim register with automated checks, and legal text only when the owner supplies it.
- **Quality gates**: contrast, raw values and claims as unit tests; accessibility, production policy and visual references end to end; and the end-to-end suite joins CI for the first time.

## Technical Context

**Language/Version**: TypeScript 5.x, React 19; Node.js 22 in CI and images

**Primary Dependencies**: unchanged (React Router, TanStack Query, react-i18next, markdown-it, DOMPurify, Shiki, Mermaid, CodeMirror 6). Additions, none of them a UI framework:

| Package | Why | New code executed |
|---------|-----|-------------------|
| `@fontsource-variable/geist`, `@fontsource-variable/geist-mono` | Self-hosted font files (OFL-1.1) | None; font files only |
| `@codemirror/view`, `@codemirror/language`, `@lezer/highlight` | Editor theme and name; pnpm requires direct declaration | None; already installed through the editor package |

**Storage**: N/A. No database, API or content change; no new browser storage key

**Testing**: existing tools only: Vitest, Testing Library, Playwright, axe-core, ESLint, TypeScript strict

**Target Platform**: last 2 versions of Chromium, Firefox and Safari (S001 D4); static hosting through the existing nginx image, under its existing security policy

**Project Type**: Web application; only the SPA changes

**Performance Goals**: landing readable < 2 s p95 and ≤ 300 KB compressed on first visit (SC-012; estimated about 190 KB); module readable < 2 s p95 and feedback < 1 s p95 (S001 NFR-003; measured baseline 1,168 ms and 140 ms)

**Constraints**: WCAG 2.2 AA; 320 to 2560 CSS px; `script-src 'self'`, `font-src 'self'` and no external requests; no inline scripts; `/verify-email` and `/reset-password` frozen; `GET /modules/{id}` records a view; English only

**Scale/Scope**: about 22 routes across 3 audiences; 11 lessons in 5 modules; 15 end-to-end tests to keep green (baseline: 15 passed, 3 skipped)

No NEEDS CLARIFICATION remains: the owner answered Q1–Q3 on 2026-11-06.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / Standard | How the plan complies | Pre | Post |
|----------------------|-----------------------|-----|------|
| I. Learning First (v1.1.0) | Learning shell has no marketing (FR-024); reading comfort, working lesson links and honest progress are priorities; decoration is limited (FR-010). The landing page is a public orientation surface and meets the three conditions: accurate information (FR-015, SC-006), a measurable route to the first lesson (SC-015) and no promotion in the learning environment (FR-024) | ✅ | ✅ |
| II. Hands-on Learning | Challenges and laboratories are central in public content; their behavior is frozen | ✅ | ✅ |
| III. Progressive Complexity | Curriculum order, prerequisites and levels stay visible; planned paths cannot look available | ✅ | ✅ |
| IV. Engineering Excellence | Explicit [contracts](./contracts/); tests before implementation; gates for tokens, claims and production behavior; defects found are recorded, not silently absorbed; ADR planned | ✅ | ✅ |
| V. Responsible AI | Human approval cannot be bypassed, and the existing weakness is closed (R19); decision summaries stay labeled; no secrets involved; no third-party requests | ✅ | ✅ |
| VI. Model and Framework Agnosticism | Vendor notes preserved; public copy names no provider as a dependency | ✅ | ✅ |
| VII. Measurable Learning Outcomes | Progress keeps meaning demonstrated competencies; no credential is implied; evidence becomes reviewable (R18) | ✅ | ✅ |
| User Experience and Accessibility | US4, FR-044–FR-051, SC-001, SC-002; the manual audit is finally a gate | ✅ | ✅ |
| Reliability and Performance | Shared states everywhere; budgets in SC-012, SC-013; production policy tested | ✅ | ✅ |
| Educational Content Governance | Content untouched; showcase excerpts checked against source; "Last reviewed" is not promoted | ✅ | ✅ |
| Governance | Conflicts identified in the spec before implementation | ✅ | ✅ |

**Result**: PASS against constitution 1.1.0. The owner chose to amend Principle I on 2026-11-06, after analysis flagged the landing page as a conflict with 1.0.0. Post-design: no new conflict.

## Project Structure

### Documentation (this feature)

```text
specs/002-premium-product-experience/
├── spec.md
├── plan.md              # This file
├── research.md          # Decisions R0–R20, with measurements
├── data-model.md        # Frontend-only models; no persisted data changes
├── quickstart.md        # Validation scenarios P1–P12
├── contracts/
│   ├── design-tokens.md
│   ├── routes-and-shells.md
│   ├── ui-components.md
│   └── public-content.md
├── checklists/requirements.md
└── tasks.md             # Next step (/speckit-tasks); not created here
```

### Source Code (repository root)

```text
frontend/
├── index.html                    # CHANGED: metadata, canvas color, no-script message
├── public/                       # NEW: favicon, share image
├── src/
│   ├── styles/                   # NEW: replaces styles.css (index, tokens, reset, base, layout, components, content, screens)
│   ├── app/
│   │   ├── App.tsx, routes.ts    # CHANGED: shell, title, new routes, redirect
│   │   ├── shells/               # NEW: AppFrame, PublicShell, LearningShell (replaces Layout.tsx)
│   │   └── navigation/           # NEW: usePageMeta, RouteFocus, useFragmentTarget
│   ├── components/
│   │   ├── ui/                   # NEW: Button, Field, Alert, Badge, Card, ProgressBar, Tabs, ConfirmDialog, Breadcrumb, PageHeader, Icon
│   │   ├── states/               # EVOLVED
│   │   └── content/              # EVOLVED: highlighter.ts (new), CodeBlock, Diagram, Markdown, Callouts
│   ├── features/
│   │   ├── marketing/            # NEW: LandingPage and its sections
│   │   ├── legal/                # NEW: LegalPage, availability
│   │   ├── catalog/              # REDESIGNED
│   │   ├── dashboard/            # REDESIGNED
│   │   ├── module/               # REDESIGNED: contents, lesson view trigger
│   │   ├── knowledge-check/      # REDESIGNED; HistoryPage (new)
│   │   ├── challenge/            # REDESIGNED: Editor theme and name
│   │   ├── lab/                  # REDESIGNED: stepper; player.ts gains maxReachableIndex
│   │   └── auth/                 # REDESIGNED; lazy; /register
│   ├── i18n/en/                  # common.json CHANGED; marketing.json NEW
│   └── legal/en/                 # Reserved for owner-supplied files; none shipped
├── tests/
│   ├── unit/                     # NEW: tokens, raw values, claims, excerpts, legal, player guard, components
│   └── e2e/                      # CHANGED: catalog test moves; NEW: landing, navigation, a11y matrix, csp, visual
├── playwright.config.ts          # CHANGED: production and visual projects
└── Dockerfile                    # CHANGED: build argument VITE_PUBLIC_ORIGIN

.github/workflows/ci.yml          # CHANGED: end-to-end job, including visual comparison
.github/workflows/visual-references.yml  # NEW: manual generation of visual references
docs/adr/0007-*.md                # NEW: frontend design system and highlighting engine
docs/accessibility/audit-premium.md  # NEW: manual and automated audit results

backend/, runner/, content/, specs/001-*/, frontend/nginx.conf   # NOT CHANGED (SC-005)
```

**Structure Decision**: the existing web application structure, with all changes inside `frontend/`. Feature folders stay, and shared visual concerns move to `styles/` and `components/ui/`. `frontend/src/styles.css` and `Layout.tsx` are replaced once their successors are in place.

## Delivery Increments

Each increment leaves the application working, with the end-to-end suite green.

| Increment | Scope | Stories | Exit criteria |
|-----------|-------|---------|---------------|
| 1. Visual foundation | Tokens, fonts, base styles; highlighter, diagram and editor themes; shared components; existing screens moved onto them; style gates | US1 | P1, P10; contrast and raw-value tests pass; 13 baseline findings gone |
| 2. Navigation and routes | `AppFrame`, shells, route table, redirects, titles, focus, scroll, lesson links; catalog moves to `/curriculum` | US4 (part), US3 (part) | P3, and P5 steps 1–2; SC-007, SC-008 |
| 3. Public experience | Landing, curriculum and path redesign; authentication screens; legal availability; metadata | US2, US5 | P2, P6, P11; SC-006, SC-012 |
| 4. Learning environment | Module, dashboard, evidence review, knowledge checks, challenges, laboratory | US3, US6, US7, US8 | P5, P7, P8, P9; Spec 001 V1–V7 |
| 5. Quality assurance | Full state matrix, visual references, manual audit, moderated testing, end-to-end job in CI | US4 | P4, P12; SC-001, SC-002, SC-009, SC-011 |

Increment 1 can ship alone, and it would already fix the worst defects. The CI job should arrive as early as increment 1 if it proves stable, because it protects all later work.

## Risks

The spec lists regression risks R-01 to R-19. These are the planning risks.

| Risk | Mitigation |
|------|------------|
| Replacing the single stylesheet in one step breaks many screens | Layered files arrive alongside the old rules, and screens move over gradually within increment 1; the old file is removed last |
| JavaScript regex engine differs from WebAssembly on future lessons | Identical on all 11 current blocks; repeat the comparison if languages are added; the plain fallback remains |
| Test suite becomes flaky in CI, where it has never run | Introduced as its own job; stabilized before it is required |
| Screenshot references churn with minor changes | Created only in increment 5, after the design settles |
| Manual audit and moderated testing need people outside this work | Listed as dependencies in the spec; schedule them early, since they gate release |
| Geist may not suit long reading | Reading comfort is measured (SC-017); the family is changed in one place, and Inter is the measured alternative |

## Complexity Tracking

No constitution violation requires justification.
