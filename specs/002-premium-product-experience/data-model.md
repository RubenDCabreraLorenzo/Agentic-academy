# Data Model: Premium Product Experience

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-06

**This feature changes no persisted data.** There are no database migrations, API schema changes or content format changes (FR-053, SC-005). The items below are frontend-only models, and exist so that later tasks and tests refer to them consistently.

## 1. Unchanged data

| Source | Used for | Constraint |
|--------|----------|------------|
| `GET /catalog`, `GET /paths/{id}` (public) | Landing, curriculum, path pages | Types stay generated from Spec 001's `openapi.yaml` |
| `GET /me`, `GET /me/dashboard`, `GET /me/competencies` | Shell choice, dashboard | No change |
| `GET /modules/{id}` | Module page only | **Records a view**; never call it to build navigation |
| `GET /knowledge-checks/{id}/attempts/history` | New attempt review | Returns no question prompts |
| `GET /lab/scenarios/{id}` | Laboratory | `module_ids` is empty in published scenarios, so it cannot be used for the return link |
| `academy:draft:*`, `academy:self-assessment:*` (browser storage) | Drafts and self-assessment | Keys and formats do not change; no new storage key is introduced (dark only means no theme preference) |

## 2. Route definition

Extends the existing `RouteDef` in `frontend/src/app/routes.ts`.

| Field | Type | Rules |
|-------|------|-------|
| `path` | string | Unique; see [routes contract](./contracts/routes-and-shells.md) |
| `auth` | boolean | Existing; `true` wraps the route in `RequireAuth` |
| `shell` | `public` \| `learning` \| `session` | New; `session` resolves from `useMe` |
| `load` | lazy page loader | Existing; authentication pages also become lazy, to protect the landing page's size |
| `titleKey` | string key | New; generic title until the page provides a specific one |

## 3. Page metadata

`{ title: string; description?: string }`, set through `usePageMeta`.

- The resulting document title is unique per route, and includes the content title where one exists (FR-042).
- Set once per page render with data. Leaving a page does not need a reset, since the next page sets its own.

## 4. Laboratory navigation origin

Passed as router location state from a module's laboratory links.

| Field | Type | Rules |
|-------|------|-------|
| `from.moduleId` | string | Target of the return link |
| `from.moduleTitle` | string | Link text |

Absent on a direct visit, in which case the link goes to `/dashboard`. It lives only in browser history and is never sent to the API.

## 5. Laboratory player state

The existing `PlayerState` is unchanged. New derived value:

`maxReachableIndex(scenario, state)`: the index of the first `approval_request` with no decided branch in the current variant, or else the last element's index.

Transitions affected:

| Action | Today | New |
|--------|-------|-----|
| `jump` | Clamped to the last element; can cross an approval | Clamped to `maxReachableIndex` |
| `next`, `prev`, `play`, `pause`, `restart`, `decide`, `select` | — | Unchanged |

## 6. Legal documents and publisher

| Item | Fields | State |
|------|--------|-------|
| Legal document | `kind` (`privacy` \| `terms`), `markdown` | `available` if its file exists at build time, otherwise `unavailable` |
| Publisher | `name`, `contact_email`, optional `address`, `registration` | Same |

There are no partial states: a missing file means no link and a not-found route. Files and validation: [public content contract](./contracts/public-content.md).

## 7. Showcase excerpt

| Field | Type | Rules |
|-------|------|-------|
| `source` | repository path | Must exist; never a `solution/` directory |
| `strings` | list of strings | Each must appear in the source file (unit test) |

## 8. View state matrix

Every data view defines these presentations (FR-051), which also form the visual reference set (SC-011).

| View | Loading | Empty | Error with retry | Success variants |
|------|---------|-------|------------------|------------------|
| Landing, curriculum section | Skeleton inside the section | No paths | Section only | Available and planned paths |
| Curriculum | Yes | No paths | Yes | Grouped by level |
| Path | Yes | — | Yes, and unknown path | Available as visitor and as learner; planned |
| Dashboard | Yes | No paths | Yes | New learner, in progress, completed |
| Competencies | Yes | No competencies | Yes | Not started, in progress, demonstrated |
| Module | Yes | — | Yes | Missing prerequisites, deprecation |
| Knowledge check | Yes | — | Yes | Question, correct, incorrect, unanswered confirmation, passed, not passed |
| Attempt review | Yes | No attempts | Yes | Passed and not passed |
| Challenge | Yes | No history | Yes | Queued, running, delayed, passed, failed, stopped, error, unavailable |
| Laboratory | Yes | — | Yes | Playing, awaiting approval, failure, comparison |
| Authentication forms | Pending action | — | Yes | Submitted notices |
| Legal page | Yes | — | Yes | Rendered; not found when absent |

## 9. Relationships

```text
Token ──► Shared component ──► Screen ──► Shell ──► AppFrame
                                  │
Route definition ─────────────────┘ (shell, title, load)
Claim register ──► marketing strings ──► Landing ◄── catalog and path data
Legal files (optional) ──► Footer, /privacy, /terms, /register links
```
