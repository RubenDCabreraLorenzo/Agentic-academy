# Contract: Routes, shells and navigation behavior

**Requirements**: FR-014, FR-020, FR-022a, FR-023–FR-028, FR-031, FR-036, FR-038–FR-043, SC-007, SC-008. Decisions: [research](../research.md) R8–R10, R18.

## Route table

`auth` is the existing `RouteDef` field. `shell` is new: `public`, `learning`, or `session` (chosen from the current session).

| Path | Auth | Shell | Title source | Notes |
|------|------|-------|--------------|-------|
| `/` | No | `session` | `meta.landing.title` | Landing for everyone; the primary action adapts |
| `/curriculum` | No | `session` | `meta.curriculum.title` | Moved from `/`, same data |
| `/paths/:pathId` | No | `session` | Path title | Unchanged address |
| `/sign-in` | No | `public` | `meta.signIn.title` | Keeps `next` |
| `/register` | No | `public` | `meta.register.title` | New address |
| `/sign-up` | No | None | — | `<Navigate replace>` to `/register`, keeping the query string |
| `/check-email`, `/forgot-password` | No | `public` | Own key | Unchanged |
| `/verify-email`, `/reset-password` | No | `public` | Own key | **Frozen**: built by the backend in emails |
| `/privacy`, `/terms` | No | `session` | Own key | Not found until the text is supplied |
| `/dashboard`, `/dashboard/competencies` | Yes | `learning` | Own key | Unchanged |
| `/account` | Yes | `learning` | Own key | Unchanged |
| `/modules/:moduleId` | Yes | `learning` | Module title | Unchanged; lesson links use `#lesson-<id>` |
| `/knowledge-checks/:checkId` | Yes | `learning` | Own key | Unchanged |
| `/knowledge-checks/:checkId/history` | Yes | `learning` | Own key | **New**; read-only review of submitted attempts |
| `/challenges/:challengeId` | Yes | `learning` | Challenge title | Unchanged |
| `/lab/:scenarioId` | Yes | `learning` | Scenario title | Unchanged |
| `*` | No | `session` | `states.notFound` | Links to `/` and `/curriculum` |

Signed-in learners who open `/sign-in` or `/register` see a notice with a link to `/dashboard` in place of the form.

## Shells

All three are built on one `AppFrame`, which owns behavior that MUST exist everywhere (FR-039): the skip link, the `main` landmark with `id="main"`, the offline notice, the session-expiry warning with its sign-in link, route focus handling and the footer slot.

| Shell | Navigation | Footer | Width | Marketing content |
|-------|-----------|--------|-------|-------------------|
| Public | Brand, Curriculum, Sign in, Create account | Full (FR-022) | Sections may be full width | Allowed |
| Learning | Brand, My progress, Curriculum, Account, Sign out | Product name; privacy, terms and contact when available (FR-022a) | Up to `--layout-max` | **Forbidden** (FR-024) |

- While the session is unknown, session-dependent navigation stays empty and keeps its space, so that signed-in learners do not see "Sign in" flash, as they do today.
- Neither shell uses a collapsed menu. At narrow widths the navigation wraps onto more lines, and every link stays visible. The shell header is not sticky, so wrapping takes no reading space.
- "Sign out" stays a visible `button` named "Sign out" at every width (test fixture).
- A failed or "not signed in" session check never shows an error on a public page.

## Link destinations that change

| Where | Today | New |
|-------|-------|-----|
| "Curriculum" navigation link | `/` | `/curriculum` |
| Not-found page link | `/` | `/curriculum`, plus `/` |
| Dashboard "Explore the curriculum" | `/` | `/curriculum` |
| "Create account" links | `/sign-up` | `/register` |
| Brand link, sign-out, account deletion | `/` | `/` (unchanged; now the landing) |
| Competency evidence, knowledge check | `/knowledge-checks/:id` | `/knowledge-checks/:id/history` |
| Competency evidence, challenge | `/challenges/:id` | Unchanged (history is on that page) |
| Laboratory links from a module | `/lab/:id` | Same, with navigation state `{ from: { moduleId, moduleTitle } }` |

## Navigation protocol

These steps apply on every location change handled inside the application.

| Step | Rule |
|------|------|
| Title | `usePageMeta` sets `document.title` to `"<page> · Agentic Academy"`, and the description where provided. Pages with API titles set it once the data arrives, and show the generic route title until then |
| Scroll | New navigation with no fragment scrolls to the top. Back and forward leave restoration to the browser |
| Focus, no fragment | After the page's `h1` exists (or after 3 s, using `main`), focus moves to it. `h1` has `tabindex="-1"`. Not applied on the first page load |
| Focus, with fragment | The fragment protocol below applies |
| Announcement | Moving focus to a titled heading is the announcement. Loading uses the shared `role="status"` state |

## Fragment protocol (FR-026, SC-007)

1. A lesson is `section#lesson-<id>`, and its heading becomes `h2#lesson-<id>-title` to remove the duplicate identifier.
2. Existing link formats do not change: `#lesson-<id>` in feedback, dashboard and "Continue".
3. The module's own contents links become router links, so that they follow this same path.
4. When the location has a fragment and the module has rendered, `useFragmentTarget` scrolls to the target and focuses it (`tabindex="-1"`).
5. Code and diagrams change height as they render, so that the position is re-applied on size changes until the first user scroll, key or pointer input, or for at most 3 s.
6. `html { scroll-padding-top: var(--header-offset) }` keeps targets and focused controls clear of fixed elements (WCAG 2.4.11).
7. An unknown fragment does nothing and raises no error.

## Lesson view protocol (FR-028)

Requests stay exactly as today: `GET /modules/{id}?lesson=<lessonId>`, once per lesson and module visit. Only the trigger changes: a lesson reports when it crosses a band at the vertical center of the viewport, rather than when 25% of its height is visible, which is impossible for lessons taller than four viewports. The same observer provides "current lesson" (`aria-current="location"`) in the module contents.

## Module contents and fixed elements

| Width | Presentation |
|-------|--------------|
| ≥ 1200 px | Sticky side rail, next to the reading column; it covers nothing |
| < 1200 px | Compact sticky bar that opens the contents, only when the viewport is at least 500 px tall; otherwise, it is not sticky (protects 200% zoom) |

## Forbidden

- Adding or moving API calls in order to build navigation. In particular, `GET /modules/{id}` records a view, and MUST be called only when a learner opens that module.
- Moving `/verify-email` or `/reset-password`.
- Adopting a data router only for scroll restoration. `BrowserRouter` stays.
