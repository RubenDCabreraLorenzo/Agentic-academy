# Contract: Public content, claims and legal text

**Requirements**: FR-012–FR-017, FR-021, FR-022, FR-022a, SC-006, SC-012, SC-019. Decisions: [research](../research.md) R15–R17.

Copy lives in `frontend/src/i18n/en/marketing.json`, loaded with the landing page so that it does not enlarge the application entry.

## Landing sections

| # | Section | Static copy | Live data | If the data fails |
|---|---------|-------------|-----------|-------------------|
| 1 | Hero | Value proposition; two actions | Session, for the action | Shows the visitor action |
| 2 | Learning methodology | Study → check understanding → build code → inspect executions | None | — |
| 3 | Curriculum and paths | Section intro | `GET /catalog`: title, level, availability, effort, competency count, in order | `ErrorState` with retry, plus a link to `/curriculum` |
| 4 | Challenges | Explanation; excerpt | None | — |
| 5 | Laboratories | Explanation; excerpt; statement that recordings are replayed and no model is called | None | — |
| 6 | Skills and competencies | Section intro | Competencies of available paths, from `GET /catalog` | Hidden; the section keeps its intro and a link to `/curriculum` |
| 7 | Entry prerequisites | Section intro | `entry_prerequisites` from `GET /paths/{firstAvailablePath}` | Link to the path page |
| 8 | Closing action | Short text; two actions | Session | Shows the visitor action |
| 9 | Footer | Links; legal and publisher details when supplied | Legal availability | — |

Rules:

- Sections 3, 6 and 7 use the same query keys as the curriculum and path pages. No number, title or date is fixed in copy.
- The available path is the first with `status: "available"`. If there is none, sections 6 and 7 show an empty state, and the hero's copy still makes no availability claim.
- The landing page does not load the code editor, diagram engine, code highlighter or Markdown renderer.

## Calls to action

| Audience | Primary | Secondary |
|----------|---------|-----------|
| Visitor | "Create account" → `/register` | "Explore the curriculum" → `/curriculum` |
| Signed-in learner | "Go to my progress" → `/dashboard` | "Explore the curriculum" → `/curriculum` |

## Showcase excerpts

Showcases display fixed excerpts from real published content, rendered with static markup and no highlighter.

| Excerpt | Source file | What is shown |
|---------|-------------|---------------|
| Challenge | `content/en/paths/foundations-of-agentic-ai-engineering/modules/01-llm-foundations/challenges/apply-temperature/` | Title, evaluation criteria and a short code fragment |
| Laboratory | `content/en/lab/prompt-injection-and-approval.json` | A few trace steps, including one tool call with its permission and the approval step |

`marketing.json` holds the excerpt strings, with their source path recorded next to them. A unit test reads the source files from the repository and fails if an excerpt no longer appears there (R-15). Reference solutions are never a source.

## Claims

The [claim register](../spec.md#claim-register) is authoritative.

| Check | How | Fails when |
|-------|-----|-----------|
| Forbidden terms | Unit test scans `marketing.json` and public strings for: certif*, accredit*, testimonial, "free", price, pricing, "$", "€", "guarantee", "video", "AI tutor", "expert-reviewed", "trusted by", or a percentage or count of users | A term appears, except on an explicit, commented allow-list |
| Laboratory disclosure | Component test on the landing page | The replay statement is missing |
| Human review | Quickstart P2 | A statement has no register entry (SC-006) |

The automated scan only assists: the human review remains the gate.

## Metadata and share preview

| Item | Location | Notes |
|------|----------|-------|
| Default title, description | `index.html` | What clients that do not run scripts see |
| `og:title`, `og:description`, `og:type`, `twitter:card` | `index.html` | One product-level preview (FR-021) |
| `og:image`, `og:url` | `index.html`, filled at build time from `VITE_PUBLIC_ORIGIN` | Absolute addresses are required; omitted when the variable is not set |
| Image, favicon | `frontend/public/` | Served from the origin; no third party |
| Per-route title and description | `usePageMeta` | Keys under `meta.*` in the strings |
| No-script message | `<noscript>` in `index.html` | Product name and one sentence, on the dark canvas |

## Legal and publisher files

Owner-supplied files live in `frontend/src/legal/en/`. None may be generated. `privacy.md` and `terms.md` currently hold lorem ipsum, at the owner's request; `publisher.json` does not exist.

| File | Effect when present | When absent |
|------|---------------------|-------------|
| `privacy.md` | `/privacy` renders it; links in footer and registration | Route shows not found; links hidden |
| `terms.md` | `/terms` renders it; links in footer and registration | Route shows not found; links hidden |
| `publisher.json` (`name`, `contact_email`; optional `address`, `registration`) | Publisher and contact in the footer | Not shown |

- Availability is read at build time (`import.meta.glob`), so that it cannot disagree with the deployed files, and tests can pass in fixtures.
- Text renders through the existing `Markdown` component and is loaded only on those routes.
- This is application text, not educational content; it is not part of the content bundle and is not governed by the content validator.
- Registration does not record acceptance (spec, "Requirements That Would Need Architecture Changes").

## Public launch gate (SC-019)

The release checklist for opening public registration MUST confirm: `privacy.md`, `terms.md` and `publisher.json` exist; `privacy.md` and `terms.md` hold the owner's real text, with no lorem ipsum left; links appear in the footer and on `/register`; `VITE_PUBLIC_ORIGIN` is set; and the subject-matter review (S001 T121) is complete.
