# Research: Premium Product Experience

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-06

No unknowns remain. Entries marked **Measured** were tested on 2026-11-06 against this repository at `ecedfd0`, using prototypes kept outside it. Other entries are design decisions and have not been prototyped. Decisions are judged against the constitution and the spec's constraints.

## R0. Baseline

- **Regression suite (Measured)**: the existing end-to-end suite gives **15 passed, 3 skipped** in 2.1 minutes, on desktop and 360 px projects. The skipped tests are by design: the performance test on the 360 px project, and the resilience test on both projects (it needs a runner started by the suite, which cannot run directly on Windows). This is the reference for SC-004.
- **Performance (Measured)**: module readable at 1,168 ms p95 and feedback at 140 ms p95, on the development server. The current application entry is 122 KB compressed.
- **Unit and static checks**: pass, as recorded when the base branch merged.
- **Note**: the suite is not part of CI today, despite Spec 001's plan listing it (see R13).

## R1. Styling architecture

- **Decision**: plain CSS with custom properties and cascade layers, split into a few files ([contract](./contracts/design-tokens.md)). No build-time CSS tool is added.
- **Rationale**: the current application already uses global CSS with variables, so this evolves it and keeps the classes that tests rely on. Cascade layers make the order explicit without specificity battles, and all supported browsers include them. Fits the owner's constraint against new frameworks.
- **Alternatives considered**: Tailwind (a new build dependency and a second vocabulary, and its utility classes make token discipline harder to check); CSS Modules (available in Vite, but hashed names would break structural selectors, with no real gain at this size); CSS-in-JS (a runtime cost, and it fights the security policy).

## R2. Component library

- **Decision**: none. A small set of own components over native elements ([contract](./contracts/ui-components.md)).
- **Rationale**: the needed set is small. Native `dialog`, `button`, `details` and form controls cover focus trapping, Escape and semantics. The only composite pattern, tabs, already exists in the editor. FR-011 requires a concrete justification for a library, and none exists.
- **Alternatives considered**: Radix or React Aria (good accessibility, but they add dependencies for a handful of patterns that the platform already provides); a styled kit such as MUI (imposes its own look and weight, contrary to the visual identity).

## R3. Typefaces

- **Decision**: Geist Variable for interface and prose, Geist Mono Variable for code, self-hosted from `@fontsource-variable` packages, Latin subset only. No separate display family, to keep weight down. To be confirmed in visual review.
- **Rationale (Measured)**: the two files add 52.5 KB. Both are OFL-1.1, and they are drawn as a pair, which gives a technical identity less common than Inter.
- **Measured sizes (Latin, variable, normal)**:

| Family | Size | License | Note |
|--------|------|---------|------|
| **Geist** | 29.4 KB | OFL-1.1 | Has italic (31.0 KB) |
| Manrope | 24.8 KB | OFL-1.1 | No italic file in the package |
| IBM Plex Sans | 45.7 KB | OFL-1.1 | Larger |
| Inter | 48.3 KB | OFL-1.1 | Larger and very common |
| **Geist Mono** | 23.1 KB | OFL-1.1 | Pair of Geist |
| JetBrains Mono | 40.4 KB | OFL-1.1 | Larger |

- **Constraint**: the security policy has `font-src 'self'`, and the laboratory test forbids external requests, so font services are not an option.
- **Risk**: UI symbols outside the Latin subset, such as arrows, fall back to system fonts. Decorative arrows should move to the icon set.

## R4. Code highlighting works only in development (defect found)

- **Finding (Measured)**: with the production build under the exact policy of `frontend/nginx.conf`, **0 of 3 code blocks are highlighted**. The highlighter fails silently into the plain fallback. Compiling WebAssembly fails with a `CompileError` under `script-src 'self'`, and works without the policy or with `'wasm-unsafe-eval'`. The development server applies no policy, which hid this. So S001 FR-009 is not met in production today.
- **Decision**: use the highlighter's JavaScript regex engine and a CSS-variable theme, with only the five languages the component supports.
- **Rationale (Measured)**: on all 11 code blocks in the published lessons, both engines give **identical output**. No security policy change is needed. A CSS-variable theme makes `tokens.css` the only source of colors and removes the operating-system dependency. Importing only five languages should also remove most of the current 344 build files, to be confirmed during implementation.
- **Alternatives considered**: adding `'wasm-unsafe-eval'` (works, but weakens a security control to fix a styling concern); highlighting at content build (rejected in S001 R2: the build is Python, and lessons stay as Markdown).
- **Follow-up**: the output comparison must be repeated if lessons add other languages.
- **Result (Measured, T048)**: the build went from 344 asset files to **82**. The production test passes under the exact policy of `frontend/nginx.conf`: code highlighting, diagrams, editor and fonts work, with no policy violations and no external requests.
- **Known limit of this check**: the API image does not start as built. `uv run` needs a home directory for its cache, and writes to a `.venv` owned by root, but the image's user has neither. This defect in `backend/Dockerfile` predates Spec 002, which does not change the backend. The test therefore ran with a temporary Compose override, kept out of the repository, that starts `.venv/bin/uvicorn` directly, so `docker compose up --build api web` from quickstart P10 does not work as written until that is fixed.

## R5. Code editor theme and accessibility

- **Decision**: `theme="none"`, an editor theme using `var(--…)` values, a highlight style using `--syntax-*`, and an accessible name through `EditorView.contentAttributes`.
- **Rationale (Measured)**: today the editor has a white background and inherited light text (1.18:1). The current `aria-label` prop does not reach the editable element (`aria-label` is null). Under the production policy the editor works.
- **Keyboard (Measured)**: Tab stays inside the editor and indents, as expected. **Esc then Tab moves focus out** to the next control. So no behavior change is needed, only a visible instruction (FR-034).
- **Alternatives considered**: `@uiw/codemirror-themes` (an extra package, for what a few lines do); a ready-made dark theme (colors outside the tokens, which contrast checks could not see).

## R6. Diagrams

- **Decision**: `theme: "base"` with `themeVariables` read at runtime from resolved tokens.
- **Rationale (Measured)**: a prototype with the proposed values rendered both real diagrams from Module 1 with **0 audit findings**, and with 5 text nodes passing contrast (today: 4.43:1 on edge labels). Visually, nodes, edges and labels read clearly on the dark surface. Mermaid calculates derived colors, so it receives resolved values rather than `var()` references.
- **Alternatives considered**: built-in `dark` theme (the source of the 4.43:1 failure); styling the output from CSS (fragile, tied to Mermaid's internals).

## R7. Dark only

- **Decision**: one set of values. Remove the `prefers-color-scheme` rule, the `matchMedia` call and the highlighter's light variant. `index.html` sets `color-scheme: dark` and the canvas color in a small inline `style`, which the policy allows.
- **Rationale**: decided by the owner (Q1=A). Painting the canvas before stylesheets load avoids a white flash. No inline script is needed, which the policy would block. Semantic token names leave room for a light theme later.

## R8. Page titles

- **Decision**: a `usePageMeta` hook that sets `document.title` and the description.
- **Rationale**: `index.html` must keep its static title and description for clients that do not run scripts (Q2=A). The first `title` element in a document defines its title, so React 19's rendering of `<title>` could lose to the static one, and this avoids the question entirely.
- **Alternatives considered**: a head-management library (a dependency for a two-line need); removing the static title (contrary to R15).

## R9. Focus, scroll and fragments

- **Decision**: the protocols in the [routes contract](./contracts/routes-and-shells.md), inside `AppFrame`, with no data router.
- **Rationale (Measured)**: lesson links fail because content arrives after navigation, and because the browser's own fragment handling has already run: page at 0, target at 3,387 px. Height changes from code and diagrams require re-positioning, and it must stop at the first user input so as not to fight the learner. `scroll-padding-top` covers WCAG 2.4.11.
- **Alternatives considered**: moving to a data router for `ScrollRestoration` (a broad change to the application's entry for a narrow need; it also does not handle fragments in late content).
- **Implementation note**: `AppFrame` must stay mounted when the shell changes. A session that expires on a learning page moves to the public shell, and remounting there would lose the warning and treat the move as a first load. So `PublicShell.tsx` and `LearningShell.tsx` provide the contents of its navigation and footer slots, rather than wrapping it.
- **Finding (Measured, T065)**: under the development server, 10 of 25 module loads left a diagram on its placeholder for good, with no error, and 0 of 25 with the production image. `StrictMode` runs each effect twice, and the cancelled effect still started a Mermaid render with the same identifier. Not starting a render for a cancelled effect gave 0 of 25. This pattern predates Spec 002, and it explains a test failure in T031 first put down to recompilation.

## R10. Lesson view recording

- **Decision**: report when the lesson crosses a band at the center of the viewport.
- **Rationale (Measured)**: the 25% rule can never fire when a lesson is taller than four viewports. At 360 × 780, one of the 11 lessons is 3,786 px against a limit of 3,120 px, and larger type would add more. No lesson exceeds it at 1280 × 800 today. The API request stays identical.
- **Trade-off**: a lesson crossed during a quick scroll is still recorded. This is also true today once 25% becomes visible, and it does not count as evidence (S001 FR-036). It can move "Continue", as it can today.
- **Alternatives considered**: a lower threshold (only moves the limit); a sentinel at the heading (would not also give the "current lesson" that the module contents need, so two observers would be required).

## R11. Heading structure in lessons

- **Decision**: render lesson headings one level lower, in the frontend.
- **Rationale (Measured)**: lessons use 28 `##` headings, which render as `h2`, siblings of the lesson's own `h2`. This flattens the outline (S001 NFR-012 asks for a consistent hierarchy). Content cannot change (FR-053), but the renderer can.
- **Risk**: the content validator and anchors are unaffected, since this happens only at rendering.

## R12. Automated style and claim gates

- **Decision**: reuse existing tools. A built-in lint rule forbids JSX `style`, with an allow-list. Vitest tests check contrast from `tokens.css`, raw colors, forbidden claim terms, showcase excerpts against source files and legal availability.
- **Rationale**: they make SC-003, SC-006 and SC-010 mechanical without new dependencies. Frontend tests can read the repository, since CI checks it out whole.
- **Alternatives considered**: Stylelint (an added tool for one or two rules); Chromatic or similar services (external, and contrary to the privacy-minded setup).

## R13. Verifying production behavior and adding end-to-end tests to CI

- **Decision**: (a) a `production` Playwright project and `csp.spec.ts`, against the real nginx image, asserting that highlighting, diagrams, editor and fonts work with no policy violation; (b) a new CI job running the end-to-end suite.
- **Rationale (Measured)**: R4 shows that development results are not valid for this. `nginx.conf` does not need to change. Today's CI does not run the suite at all, so SC-004 would otherwise rest on manual runs.
- **Runner in CI**: GitHub's runners have Docker but no gVisor, so the job uses the documented `RUNNER_RUNTIME=runc` exception. These results prove behavior, not sandbox security, and the security suite remains separate.
- **Windows**: the runner works only in its container (`os.O_NOFOLLOW`), so local runs use `E2E_START_RUNNER=0`. See the [quickstart](./quickstart.md).

## R14. Visual references

- **Decision**: Playwright screenshot comparison on a pinned CI runner (`ubuntu-24.04`), reusing the end-to-end job's setup. A manual workflow generates references and publishes them as a build artifact. A person reviews them and commits them to the repository (SC-011). The `e2e` job compares against them. They are not generated or compared on developer machines.
- **Rationale**: font rendering differs between systems, so references must come from one environment. The runner already has what the suite needs: `uv` for its preparation, and the application at `localhost` with `COOKIE_SECURE=false`. Playwright is already a dependency. Fixed test data: the seeded learner, with progress reset, and animations disabled.
- **Alternatives considered**: the official Playwright container (it has no `uv`, which the suite's preparation needs, and from a container the application is not at `localhost`, so the `Secure` session cookie is rejected over HTTP unless the stack is reconfigured); hosted visual review services (external; adds an account and sends screenshots to a third party).
- **Limitation**: minutes of CI per run, and references must be regenerated if the pinned runner image changes font rendering.

## R15. Search and share metadata

- **Decision**: static metadata and one product-level share preview in `index.html`, with absolute addresses filled at build time from `VITE_PUBLIC_ORIGIN`.
- **Rationale**: decided by the owner (Q2=A). Share scrapers do not run scripts, so per-route tags would be invisible to them. The hosting address is undecided (S001 R12), so it must be a build setting. Tags requiring it are omitted when it is unset, rather than publishing a wrong address.

## R16. Legal text

- **Decision**: optional files in `frontend/src/legal/en/`, detected at build time, with no generated text. See the [contract](./contracts/public-content.md).
- **Rationale**: decided by the owner (Q3=A). Presence-based behavior makes "no placeholders" automatic, and a pull request is enough to publish. Keeping these files outside the content bundle avoids touching content governance.

## R17. Landing page size

- **Decision**: lazy authentication pages, marketing strings outside the entry, and no heavy content engines on the landing page.
- **Estimate**: entry about 122 KB today, minus moved authentication pages, plus landing code and strings (about 15 KB) and two fonts (52.5 KB), gives **about 190 KB**, under the 300 KB limit of SC-012. To be measured once built.

## R18. Reviewing past attempts

- **Decision**: a new frontend route, `/knowledge-checks/:checkId/history`, using the existing history endpoint.
- **Rationale**: today's evidence link opens the live check, which starts or resumes an attempt. This meets S001 FR-041 with no contract change.
- **Limitation**: the endpoint has no question prompts, so the review shows numbered questions with their result, explanation and lesson link. Showing prompts would require a contract change.

## R19. Jumping across an approval

- **Decision**: clamp `jump` in the player, using `maxReachableIndex`, with unit tests for both branches.
- **Rationale (Measured from code)**: `reduce` clamps `jump` only to the last element, so a stepper offering every step could bypass human approval (S001 FR-030). The current interface hides this by showing only steps already reached.

## R20. Reading measure

- **Decision**: `--measure-prose: 50ch` on prose elements only, and `--measure-wide: 46rem` for code, diagrams and tables. The requirement applies to the median line, with 90 characters as a hard limit.
- **Rationale (Measured)**: with real lesson text in Geist Variable, at 1440 px wide:

| Measure | Lines measured | Characters: min | Median | Max |
|---------|----------------|-----------------|--------|-----|
| 70ch (first sample; 5 lines) | 5 | 93 | 98 | 100 |
| 58ch | 32 | 71 | 80 | 86 |
| 54ch | 35 | 65 | 75 | 83 |
| 52ch | 35 | 66 | 73 | 83 |
| **50ch** | 36 | 59 | **69** | 78 |
| 48ch | 42 | 59 | 67 | 74 |
| 46ch | 45 | 55 | 63 | 69 |

  `ch` is the width of the zero, which is wide in Geist, so 70ch would exceed the 90-character limit of S001 NFR-012. Font size does not change the result, since `ch` scales with it (at 50ch: identical at 1.0625 rem and 1.125 rem). Unjustified text always varies by line, so a strict 65–75 per line cannot be met with any value.
- **Alternatives considered**: a fixed width in `rem` (would not follow font size); justified text (rivers of space, and worse for people with dyslexia).
- **Follow-up**: measure again if the family changes (T131).
