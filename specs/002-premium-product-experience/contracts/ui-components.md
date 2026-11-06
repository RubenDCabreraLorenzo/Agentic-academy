# Contract: Shared components and preserved behavior

**Requirements**: FR-005–FR-008, FR-032–FR-037, FR-044–FR-051. Decisions: [research](../research.md) R1, R2, R4–R6, R11, R18, R19. Location: `frontend/src/components/ui/`, unless noted.

No UI library is adopted. All components use native elements first.

## Component inventory

| Component | Replaces today | Behavior that is part of the contract |
|-----------|----------------|---------------------------------------|
| `Button`, `LinkButton` | `.btn`, `.btn.secondary`, `.btn.danger`, `.linklike` | Variants `primary`, `secondary`, `ghost`, `danger`. Native `button` or `a`. Hover, active, focus and disabled states. At least 24 × 24 px, and 44 px tall on touch widths for primary actions |
| `Field` | Bare `label` and `input` | Label, optional hint, error text linked with `aria-describedby`, and `aria-invalid` |
| `Alert` | `.alert` | Tones `info`, `success`, `warning`, `danger`, each with an icon and text. `role` passed by the caller |
| `Badge` | `.badge` | Tones as above. Never interactive |
| `Card` | `.card` | Surface only; heading level chosen by the caller |
| `ProgressBar` | `.progress-bar` | `role="progressbar"`, name, value and text equivalent; width through `--progress` |
| `Tabs` | Editor tabs | ARIA tabs pattern, arrow keys, roving `tabindex` |
| `ConfirmDialog` | Inline `alertdialog` forms | Native modal `dialog`, `role="alertdialog"`. Focus in on open, Escape cancels, focus returns to the opener. Supports the typed confirmation |
| `Breadcrumb` | Bare links | `nav` with a translated name and an ordered list |
| `PageHeader` | Repeated markup | `h1` with `tabindex="-1"`, summary, metadata; calls `usePageMeta` |
| `Icon` | None | Inline SVG set kept in the repository; decorative by default (`aria-hidden`) |
| `Loading`, `EmptyState`, `ErrorState`, `OfflineBanner` | Same (`components/states`) | **Evolved**, keeping names and behavior; `role` values unchanged |
| `Markdown`, `CodeBlock`, `Diagram`, callouts, `ContentMeta` | Same (`components/content`) | **Evolved**, as below |

## Content components

| Component | Required change | Must stay |
|-----------|-----------------|-----------|
| `CodeBlock` | Highlighter from `highlighter.ts`: JavaScript regex engine, CSS-variable theme, languages limited to the five in `LANG_NAMES` | Language label, copy, annotations, internal scroll with `tabindex="0"`, plain fallback, `figure.code-block` |
| `Diagram` | `theme: "base"`, with `themeVariables` read from resolved tokens; no `matchMedia` | `securityLevel: "strict"`, accessible name, visible caption, source fallback |
| `Markdown` | Lesson headings render one level lower than authored, so `##` inside a lesson becomes `h3` under the lesson's `h2`; tables get a keyboard-scrollable region | Sanitization, directives, content untouched |
| Callouts | Icons and token colors | Translated labels, `aria-label`, `role="note"` on deprecations |

## Feature behavior frozen by this redesign

| Feature | Frozen behavior | Allowed changes |
|---------|-----------------|-----------------|
| Knowledge check | Question order, one question at a time, immediate feedback, answer lock after feedback, threshold text, unanswered confirmation, retry, best score, draft replay, heading focus on question change | Layout, states, inputs' appearance. `ConfirmDialog` for unanswered questions |
| Challenge | Autosave after 1 s, local draft, hints in order, reset, run and submit, one run at a time, polling, statuses, per-criterion results, output, history, reference explanation only after passing, editor file tabs, read-only tests | Layout (FR-033), status presentation |
| Laboratory | Client-side replay, variants, element kinds, educational label, failure notes, comparison counts and unique steps, no external requests | Layout, stepper |
| Dashboard | All fields of FR-030, next-step link building, reset with typed "RESET" | Layout |
| Account | Typed "DELETE" and its warning | Moves into `ConfirmDialog` |
| Authentication | Validation, generic errors, no account enumeration, `safeNext` | Layout |

## Editor (`features/challenge/Editor.tsx`)

| Item | Contract |
|------|----------|
| Theme | `theme="none"` with an `EditorView.theme` whose values are `var(--…)` tokens, marked dark, plus a `HighlightStyle` using `--syntax-*` |
| Accessible name | `EditorView.contentAttributes` sets `aria-label` on the editable element. The current prop only reaches the outer wrapper |
| Leaving by keyboard | A visible, translated hint: "Press Esc, then Tab, to leave the editor". Verified to work on 2026-11-06, and covered by a test |
| Dependencies | `@codemirror/view`, `@codemirror/language` and `@lezer/highlight` become direct dependencies; they are already installed through the current editor package |

## Laboratory additions

- **Reachable steps** (FR-035, R-08): `player.ts` gains `maxReachableIndex(scenario, state)`: the first undecided `approval_request`, or the last element. `reduce` clamps `jump` to it. This is a required fix, because today's `jump` could cross an approval.
- **Stepper**: an ordered list of every step, showing kind icon and number; steps beyond the limit are disabled and explain why. Revealed element details behave as today.
- **Approval panel**: stays inline and non-modal, because the learner must be able to inspect the trace before deciding. Focus moves into it when it appears. Escape returns focus to the replay controls without deciding, and the decision stays pending.
- **Return link** (FR-036): uses navigation state when present, otherwise `/dashboard`.

## Attempt review (`/knowledge-checks/:checkId/history`)

Reads `GET /knowledge-checks/{id}/attempts/history` and never starts an attempt. It shows date, version, score, passed state and, per question, correct or incorrect, explanation and lesson link. **Limitation**: this endpoint does not return question prompts, so the review numbers questions rather than repeating their text; repeating it would need a contract change.

## Selectors tests rely on

Keep these, or change the tests in the same reviewed step (R-03, R-11):

| Used by tests | Keep |
|---------------|------|
| Sign in step | Labels "Email" and "Password"; buttons "Sign in" and "Sign out" |
| Lesson | `figure.code-block`; button "Copy"; image name of diagrams; texts "Established practice" and "Vendor-specific: …" |
| Knowledge check | `.question`, `label.option`, `ol.ordering li`, select label "Match “…” with", buttons "Check answer", "Next question", "Submit answers", "Try again", "Move up" |
| Challenge | `.cm-content`, `#result`, buttons "Run tests", "Submit", "Show hint 1 of 2" |
| Laboratory | "Step →", "← Back", "Reject"; `alertdialog` named "Human approval required"; labelled comparison cards; status "Step N of M" |
| Dashboard | Headings "My progress", "Active path", "Next step"; link "Continue where you left off"; link "View competencies and evidence" |
| Catalog | Heading "Curriculum", level headings, "Not yet available"; **the test moves to `/curriculum`** |
