# Feature Specification: Premium Product Experience

**Feature Branch**: `002-premium-product-experience` (proposed; not created yet)

**Created**: 2026-11-06

**Status**: Draft — clarifications resolved; awaiting approval before planning

**Input**: User description: "Agentic Academy — Spec 002: Premium Product Experience. Transform the
existing MVP into a polished, premium-quality commercial education platform while preserving its
educational functionality and technical architecture. This is a product experience and visual design
initiative, not an architectural rewrite. Fixed direction: dark-first premium visual identity
(charcoal and graphite surfaces, electric blue or violet accents, strong typography, consistent
tokens); marketing-first public experience with `/` as the commercial landing page, plus
`/curriculum`, `/paths/:pathId`, `/sign-in` and `/register`; a consistent authenticated learning
environment. No invented testimonials, logos, certifications, prices, statistics or claims. No change
to backend architecture, API contracts, database schema, domain model, assessment and challenge
semantics, runner security, content format or content governance. WCAG 2.2 AA is mandatory."

## Clarifications

### Session 2026-11-06

- Q: Is the product dark only, or dark by default with a light alternative? → A: Dark only at launch
  (FR-003). There is no light theme and no theme selector, and the operating-system preference is
  ignored. People who currently get a light theme from their system lose it; this is accepted. Tokens
  are semantic so that a light theme can be added later. Reading comfort (SC-017) is the signal to
  revisit this decision.
- Q: Must public pages be readable by crawlers without running scripts in this release? → A: No
  (FR-021). Public pages have titles, descriptions and a share preview. Generating `/` at build time
  can be added later without rework, and should be reconsidered before public deployment if organic
  search becomes a goal. A rendering server remains excluded by the constraints.
- Q: What legal and publisher information must exist before public registration opens, and who provides
  it? → A: Pages for owner-supplied privacy and terms text, plus publisher identity and contact details
  in the footer. Development can finish with the links hidden, but public launch is blocked until the
  owner supplies them (FR-022, FR-022a, SC-019).
- Q: May the legal pages hold temporary text during development? → A: Yes, decided by the owner on
  2026-11-06. `privacy.md` and `terms.md` hold lorem ipsum, supplied at the owner's request, so that the
  links and pages can be seen. It MUST be replaced with the owner's real text before public launch
  (SC-019). `publisher.json` stays absent: no publisher identity is invented.
- Q: May this initiative fix the API image, which does not start? → A: Yes, as one exception decided by
  the owner on 2026-11-06. Only the start command in `backend/Dockerfile` changes, because the production
  check (quickstart P10) depends on that image. Application code, API contracts, the schema and the
  runner stay untouched, and FR-053 and SC-005 continue to apply to everything else.

## Glossary

- **Visitor**: a person without a session, evaluating the product.
- **Learner**: a person with a session. Same meaning as in Spec 001.
- **Public shell**: the page frame (navigation and footer) for visitors and marketing content.
- **Learning shell**: the page frame for signed-in learners, focused on study and orientation.
- **Design token**: a named visual value with a semantic role, such as "muted text" or "focus ring".
- **Claim register**: the list of factual statements public pages may make, each with its source
  (see "Claim register").

References such as "S001 FR-036" point to [Spec 001](../001-agentic-academy-mvp/spec.md).

## Repository Baseline

Inspected on 2026-11-06 at `3f91342`. Measurements were taken in the running application with the
browser set to a dark color preference, because that is the direction this specification adopts.

### What exists and must be preserved

- Public catalog and path pages; sign-up, email verification, sign-in, password reset and account
  deletion; module pages with lessons, code, diagrams, maturity labels, vendor notes and deprecations.
- Knowledge checks with four question types, immediate feedback and retries; challenges with an
  editor, hints, autosave, drafts, runs, submissions and history.
- Laboratory replay with variants, comparison, failure cases and human approval; dashboard, competency
  view, path completion and path reset.
- Reusable foundations: shared loading, empty, error and offline states; content components; a single
  externalized string file; and a small set of color variables.

### Measured defects a dark-first redesign must resolve

| Finding | Measurement | Requirement at risk |
|---------|-------------|---------------------|
| Code editor keeps a white background while inheriting light page text | Plain code at **1.18:1**; much of the code is effectively invisible | WCAG 1.4.3 |
| Code editor input has no accessible name | Automated audit: serious | WCAG 4.1.2 |
| Code comments in lessons | **3.26:1** | WCAG 1.4.3 |
| Diagram edge labels | **4.43:1** | WCAG 1.4.3 |
| Destructive button text in dark colors | **2.29:1** (not flagged by the automated audit while disabled) | WCAG 1.4.3 |
| Field and card borders | **1.48:1** against their surface; fields rely on them | WCAG 1.4.11 |
| Links to a lesson section do not reach it | Target 3,387 px below; page stays at 0, on direct load and after in-app navigation. Affects "Review in the lesson" (S001 FR-018) and "Continue" | S001 FR-018, FR-038 |
| Each lesson uses one identifier twice (section and heading) | 2 occurrences per lesson | Deep links; assistive-technology references |
| Page title is identical on every screen | "Agentic Academy" on all routes | WCAG 2.4.2 |
| Most navigation does not move focus or announce the new page | Focus remains on the document body (measured from dashboard to module); only the knowledge check moves it | WCAG 2.4.3, 4.1.3 |
| Code highlighting fails in production | Under the production security policy, 0 of 3 code blocks are highlighted, silently; WebAssembly is blocked. Not visible on the development server. Found during planning (research R4) | S001 FR-009 |
| Long lessons never register as viewed at narrow widths | Lesson of 3,786 px at 360 px cannot reach the 25% visible threshold (limit 3,120 px); larger type makes this worse | S001 FR-035, FR-038 |

Automated audit (WCAG A and AA rules, dark preference, 1280 px): 13 serious findings on 2 screens,
module (7) and challenge (5 contrast, 1 name); 0 on catalog, dashboard, knowledge check, laboratory,
competencies and account. The manual audit (S001 T123) has never been run.

### Visual and structural inconsistencies

- 64 inline style declarations across 16 screens and components; no shared spacing or type scale.
- No hover or pressed state and no motion rules anywhere in the stylesheet.
- One system font stack; no typographic identity.
- Theme depends on the operating system. Code highlighting and diagrams read that preference
  separately, and the editor ignores it entirely.
- One page frame for all screens, capped at 1100 px, with no full-width layout for marketing content.
- Dialog-like confirmations appear inline and do not manage focus.
- Interface text outside the string file: "Line N", "(read-only)", and the "Main" and "Breadcrumb"
  navigation names (S001 FR-055).

### Technical constraints found

- The production security policy allows fonts, scripts and connections from the application origin only,
  and images from that origin or embedded in the page.
  Third-party font services and hosted assets would be blocked, and an existing test forbids requests
  leaving the origin during laboratory use.
- Inline scripts are not allowed, so a theme cannot be set by a script embedded in the page head.
- Verification and password-reset emails link to `/verify-email` and `/reset-password`; those paths
  are generated by the backend and cannot move.
- Opening a module through the API records a content view, which feeds "continue where you left off".
  Modules therefore cannot be fetched merely to build an index or a menu.
- Automated tests depend on visible text, roles and some structural names, including a "Sign out"
  button used by the shared sign-in step.

## User Scenarios & Testing *(mandatory)*

Workstream coverage: design system → US1; public marketing → US2; curriculum → US5; dashboard → US6;
learning environment → US3, US7, US8; responsive, accessibility and visual quality → US4.

US1 is the foundation of every other story, and delivers value by itself: applied to today's screens,
it resolves the measured contrast failures without changing any flow.

### User Story 1 - Work in one coherent, legible environment (Priority: P1)

A learner moves between lessons, assessments, challenges, the laboratory and the dashboard, and every
screen feels like the same professional product: dark surfaces, the same type hierarchy, spacing,
controls and states. Prose, code, diagrams and the editor all remain comfortable to read.

**Why this priority**: It is the visible core of the initiative and the basis for all other stories.
Today the editor is effectively unreadable under a dark preference.

**Independent Test**: Apply the visual system to the existing screens without changing any flow.
Verify that token contrast thresholds pass everywhere and that all Spec 001 scenarios still pass.

**Acceptance Scenarios**:

1. **Given** any screen, **When** it is inspected, **Then** colors, type, spacing, radii, borders,
   shadows and motion come only from the design tokens.
2. **Given** a person whose operating system prefers light colors, **When** they open the product,
   **Then** prose, code, diagrams and the editor all render in the same theme with no mixed surfaces.
3. **Given** a code example, a diagram or the editor, **When** it is displayed, **Then** every piece of
   text, including comments and edge labels, reaches at least 4.5:1.
4. **Given** any interactive control, **When** it is hovered, pressed, focused or disabled, **Then**
   each state is visually distinct, and the focus indicator reaches at least 3:1 against its
   surroundings.
5. **Given** a status such as passed, failed, planned, or a trace element kind, **When** it is shown,
   **Then** it is conveyed by text or an icon as well as by color.

---

### User Story 2 - Understand the offer and decide to join (Priority: P1)

A developer arrives at `/` and quickly understands that Agentic Academy teaches the engineering of
agentic AI systems through practice. They see how learning works, what is available today, what they
need to know already, and how to register or sign in. Nothing is exaggerated.

**Why this priority**: It is the approved marketing-first entry point and the first impression of the
product. It depends on US1 only for its visual system.

**Independent Test**: As a visitor, open `/` and verify the required sections, calls to action and live
curriculum data. Audit every factual statement against the claim register.

**Acceptance Scenarios**:

1. **Given** a visitor on `/`, **When** the page loads, **Then** the first viewport shows the value
   proposition and calls to action to register and to explore the curriculum, at 360 px as well.
2. **Given** a visitor reading further, **When** they scroll, **Then** they find the learning
   methodology, the curriculum, practical challenges and laboratories, the competencies developed,
   the entry prerequisites, and registration and sign-in entry points.
3. **Given** the curriculum section, **When** it renders, **Then** titles, levels, availability,
   effort and competency counts come from the published catalog, and planned paths are clearly
   not yet available.
4. **Given** the laboratory showcase, **When** it is displayed, **Then** it states that the laboratory
   replays curated recordings and that no language model is called.
5. **Given** the catalog cannot be loaded, **When** the page renders, **Then** all other sections
   remain usable and the curriculum section offers a retry and a link to `/curriculum`.
6. **Given** a signed-in learner on `/`, **When** the page renders, **Then** the primary action leads to
   their dashboard instead of registration.
7. **Given** any public page, **When** it is audited, **Then** it contains no testimonial, customer
   logo, certification, accreditation, price, usage statistic or unsupported claim.
8. **Given** the owner has not yet supplied legal or publisher information, **When** the footer renders,
   **Then** it shows no legal links and no placeholder text; **and given** it has been supplied, **Then**
   the footer shows it and links to the privacy notice and terms.

---

### User Story 3 - Study a lesson for a long session (Priority: P1)

A learner works through a module for an hour. Text is comfortable, code and diagrams integrate
cleanly, they always know where they are in the module, and links from feedback or the dashboard take
them exactly to the right section.

**Why this priority**: Reading is the most frequent activity, and Constitution I puts learning
effectiveness first. Deep links are broken today.

**Independent Test**: Open a module, navigate by its contents and by direct links, and verify position,
reading width, code and diagram behavior at desktop and 360 px, with no flows changed.

**Acceptance Scenarios**:

1. **Given** a link to a lesson section, **When** it is followed, either directly or inside the
   application, **Then** that section is visible, unobscured, and receives focus.
2. **Given** lesson prose on a wide screen, **When** it is read, **Then** the median line is between 65
   and 75 characters, and no line exceeds 90 (S001 NFR-012).
3. **Given** a long module, **When** the learner scrolls, **Then** they can identify the current lesson
   and reach any other lesson, the practice section and the adjacent modules without returning to the
   top.
4. **Given** a lesson of any length at any width, **When** the learner reads it, **Then** the lesson view
   is recorded as it is today and "Continue" returns to it.
5. **Given** a maturity label, vendor note or deprecation notice, **When** it appears, **Then** it keeps
   its meaning and is distinguishable by text as well as color.
6. **Given** a wide code block at 360 px, **When** it is displayed, **Then** it scrolls inside its own
   keyboard-reachable region and the page does not scroll sideways.

---

### User Story 4 - Use every screen with any device or assistive technology (Priority: P1)

A person navigating by keyboard, with a screen reader, zoomed to 200%, on a phone, with reduced motion
or with a high-contrast mode can complete the same journeys as anyone else, and always understands
loading, empty, error, offline and success states.

**Why this priority**: WCAG 2.2 AA is mandatory, and visual redesign is the moment accessibility is most
easily lost. It also defines the release gate for all other stories.

**Independent Test**: Run the automated audit on every screen and state at each required width, then
complete the manual keyboard and screen-reader walkthrough, and record the results.

**Acceptance Scenarios**:

1. **Given** in-app navigation, **When** a new page loads, **Then** the document title changes, focus
   moves to a defined starting point and the change is announced.
2. **Given** only a keyboard, **When** a person completes each key journey, **Then** every control is
   reachable and operable, focus order follows the visual order, and focus is never hidden by a fixed
   element.
3. **Given** the code editor, **When** a keyboard user is inside it, **Then** a visible instruction
   explains how to leave it, and doing so works.
4. **Given** a confirmation, such as path reset, account deletion or human approval, **When** it opens,
   **Then** focus moves into it, it can be dismissed without acting, and focus returns afterward.
5. **Given** a reduced-motion preference, **When** any screen is used, **Then** non-essential motion is
   removed and no content depends on animation.
6. **Given** any screen at 320 CSS px wide or at 200% zoom, **When** it is used, **Then** no content or
   function is lost and the page does not scroll sideways, except inside code, tables and traces.
7. **Given** a forced-colors mode, **When** any screen is used, **Then** controls, focus and statuses stay
   perceivable.
8. **Given** a request is loading, empty, fails or succeeds, **When** the state changes, **Then** it uses
   the shared state presentation and is announced, and failures offer a retry where applicable.

---

### User Story 5 - Evaluate the curriculum and a learning path (Priority: P2)

A visitor or learner opens `/curriculum` to see the full roadmap, then a path to understand its
objectives, prerequisites, competencies, effort and modules before committing.

**Why this priority**: It backs up the landing page with detail, but it already works today in a plainer
form and only one of eight paths is available.

**Independent Test**: Signed out and signed in, open `/curriculum` and a path of each status, and verify
the information, status and calls to action.

**Acceptance Scenarios**:

1. **Given** `/curriculum`, **When** it loads, **Then** paths appear in recommended order, grouped by
   level, each with title, summary, level, availability, effort, prerequisites and competencies.
2. **Given** a planned path, **When** it is viewed, **Then** it can be inspected, it clearly cannot be
   started, it does not resemble an available path, and no release date is implied.
3. **Given** an available path and a visitor, **When** they view it, **Then** they see objectives, the
   entry-prerequisite self-assessment, competencies, modules and a call to register or sign in.
4. **Given** an available path and a signed-in learner, **When** they view it, **Then** module statuses
   are shown and the primary action opens the study experience.
5. **Given** a visitor who signs in from a path, **When** sign-in succeeds, **Then** they return to that
   path.
6. **Given** the self-assessment, **When** it is used, **Then** it stays private to the device and never
   counts as progress (S001 FR-003b).

---

### User Story 6 - Get oriented on the dashboard (Priority: P2)

A returning learner opens the dashboard and immediately sees their path, demonstrated competencies, next
step and how to continue. They can review evidence and manage their account.

**Why this priority**: It is the learner's home and must stay honest about demonstrated competency, but
it already satisfies its core data requirements.

**Independent Test**: With a new, a partly progressed and a path-complete learner, verify each dashboard
state, competency evidence and account screens.

**Acceptance Scenarios**:

1. **Given** a learner with progress, **When** they open the dashboard, **Then** the active path,
   competencies demonstrated out of total, next step, "Continue" and a summary of completed and
   pending modules are visible together without scrolling at 1280 × 800.
2. **Given** a new learner, **When** they open the dashboard, **Then** a welcome state explains that
   progress reflects what they demonstrate and invites them to start.
3. **Given** progress figures, **When** they are shown, **Then** they express demonstrated competencies,
   never content consumed, and they carry a text equivalent.
4. **Given** the competency view, **When** a learner opens a knowledge-check evidence link, **Then** they
   review the recorded result and no new attempt starts (S001 FR-041).
5. **Given** path completion, **When** the learner opens the dashboard, **Then** they see the summary with
   competencies, evidence and next path, with no certificate or credential implied.
6. **Given** path reset or account deletion, **When** it is requested, **Then** the existing typed
   confirmation and warning remain in full force.

---

### User Story 7 - Practise with knowledge checks and code challenges (Priority: P2)

A learner answers questions and writes code in an environment designed for concentration, with clear
feedback, without any change to how answers and code are evaluated.

**Why this priority**: These are the evidence mechanisms of the product. The largest legibility risk,
the editor, is already addressed by US1; this story completes the layout and states.

**Independent Test**: Complete a knowledge check with failure and retry, then a challenge with a failing
run, a stopped run and a passing submission; compare results with Spec 001.

**Acceptance Scenarios**:

1. **Given** each of the four question types, **When** it is answered by mouse, touch or keyboard, **Then**
   it behaves as today and has clear selected, disabled and answered states.
2. **Given** an answer is checked, **When** feedback appears, **Then** it is announced, states correct or
   incorrect in text, and includes the explanation and a working lesson link.
3. **Given** a challenge at 1280 px or wider, **When** the learner works on it, **Then** they can see the
   problem context and the editor at the same time, and the problem stays readable.
4. **Given** a challenge at narrow widths, **When** the learner works on it, **Then** context and editor are
   both reachable and the editor stays usable.
5. **Given** a run is queued, running, delayed, stopped, unavailable or finished, **When** its status
   changes, **Then** it is announced and clearly distinguished, and the code remains in the editor.
6. **Given** a result, **When** it is displayed, **Then** per-criterion results, messages and output keep
   their meaning, and no copy describes evaluation as tamper-proof or as a credential.

---

### User Story 8 - Explore an execution in the laboratory (Priority: P3)

A learner replays an agent execution, inspects tools, state and failures, compares patterns and decides
on a human approval, in the same visual system as the rest of the product.

**Why this priority**: It is differentiating but guided practice only; it never counts as evidence and
already works functionally.

**Independent Test**: Replay all three scenarios at desktop and 360 px, including comparison, failures and
both approval branches, and verify that no request leaves the application origin.

**Acceptance Scenarios**:

1. **Given** a trace, **When** it is displayed, **Then** the four element kinds are distinguishable by text
   and icon as well as color, and the current step is unambiguous.
2. **Given** a decision summary, **When** it is displayed, **Then** it is visibly labeled as an educational
   explanation, distinct from recorded execution data (S001 FR-027a).
3. **Given** the replay controls, **When** they are used, **Then** the learner can step, pause, resume,
   restart and jump to any step they are allowed to reach (S001 FR-032).
4. **Given** a pending human approval, **When** the learner steps or jumps, **Then** they cannot pass it
   without deciding (S001 FR-030).
5. **Given** the learner arrived from a module, **When** they finish, **Then** they can return to that
   module; otherwise they can return to the dashboard.
6. **Given** a comparison at narrow widths, **When** it is displayed, **Then** both executions, their counts
   and their unique steps remain understandable.

### Edge Cases

- JavaScript fails or is disabled on a public page: a readable message and the product name appear
  instead of a blank page. The full page content is not required in this case.
- The catalog returns only planned paths or an empty list: the landing page and `/curriculum` do not imply
  available content, and show a clear empty state.
- A session expires while the learner uses any shell: the existing warning, sign-in link and preservation
  of unsent work continue to apply in every shell.
- The session check fails or returns "not signed in" on a public page: the visitor sees the normal public
  page with no error.
- A signed-in learner opens `/register` or `/sign-in`: they are offered their dashboard and are not forced to
  create another account.
- An old link to `/sign-up`, including its query string, is opened: it redirects to `/register` and keeps
  the query string.
- Fragment links target a lesson while content is still loading: the page reaches the target after the
  content renders, including when later code or diagrams change its height.
- A fragment refers to a section that no longer exists: the module opens at the top with no error.
- A fixed header would cover a focused element or a fragment target: the target remains fully visible.
- Very long titles, tool arguments, unbroken identifiers or user emails: they wrap or scroll in place, and do
  not break layouts.
- Self-hosted fonts fail or load slowly: text stays visible in a fallback font with no invisible period and
  with minimal layout shift.
- A diagram fails to render: its source and text alternative stay readable in the dark theme.
- A learner prints a lesson or uses reader tools: content order stays logical; a print-specific design is
  not required.
- Offline during a public page visit: the offline notice appears, and already loaded content remains usable.

## Requirements *(mandatory)*

### Functional Requirements

#### Shared design system (public and authenticated)

- **FR-001**: All screens MUST use one design system whose visual values come from named semantic tokens. The
  initial token set is defined under "Design Token Contract".
- **FR-002**: Every token color pairing used for text or essential interface graphics MUST meet the thresholds
  of the contract, including code, diagrams and the editor.
- **FR-003**: The product MUST present only the dark visual identity at launch, on every device and regardless of the
  operating-system preference. It MUST NOT offer a theme selector. Tokens MUST be semantic, so that a light theme can be
  added later without changing screens.
- **FR-004**: Prose, code highlighting, diagrams and the editor MUST always use the same active theme. None may
  read the operating-system preference independently of the product theme.
- **FR-005**: The system MUST provide shared components for at least: action and link buttons, form fields with
  errors, alerts, badges, cards, progress indicators, tabs, confirmation dialogs, breadcrumbs, page headers,
  and loading, empty, error and offline states.
- **FR-006**: Existing shared components (states and content rendering) MUST be evolved rather than duplicated.
- **FR-007**: Screens MUST NOT contain page-specific visual values. Inline visual declarations are allowed only
  for values computed from data, such as a progress width.
- **FR-008**: All new interface text MUST use the existing string infrastructure, and the hard-coded strings in
  the baseline MUST move to it (S001 FR-055). Dates and numbers MUST keep using locale-aware formatting.
- **FR-009**: Fonts and visual assets MUST be served from the application origin and carry licenses that permit
  commercial use. No visual feature may require a request to a third party.
- **FR-010**: Decoration MUST NOT reduce legibility. Gradients and effects are limited to the public shell's hero
  and showcase areas, and are forbidden behind body text, code, forms and assessments.
- **FR-011**: The design system MUST NOT adopt a UI framework or component library unless a concrete need is
  documented with its justification. None is required by this specification.

#### Public experience

- **FR-012**: `/` MUST be a public landing page containing, in this order or a reviewed equivalent: value proposition
  with calls to action; learning methodology; curriculum and learning paths; practical challenges and interactive
  laboratories; skills and competencies; entry prerequisites; a closing call to action; and a footer.
- **FR-013**: The value proposition MUST communicate engineering of agentic AI systems through practical learning.
  It MAY contrast this with passive consumption, but MUST NOT imply that the product offers video content.
- **FR-014**: Primary calls to action MUST lead to `/register` and `/curriculum`. Sign-in MUST be available from the
  public navigation. A signed-in learner MUST instead be offered their dashboard.
- **FR-015**: Every factual statement on public pages MUST be traceable to the claim register. Testimonials, customer
  logos, certifications, accreditation, prices, usage statistics, outcomes and dates for planned paths are forbidden.
- **FR-016**: Curriculum data on the landing page MUST come from the public catalog and path data rather than fixed
  copy, so that counts and availability cannot drift from published content.
- **FR-017**: Showcases of challenges and laboratories MUST be read-only excerpts or depictions of real published
  content, with a text alternative. They MUST NOT depict capabilities the product lacks or imply live model calls.
- **FR-018**: `/curriculum` MUST present the full roadmap from the existing catalog, with all data required by S001
  FR-001, recommended order and clear availability. It MUST be public.
- **FR-019**: `/paths/:pathId` MUST present all data shown today, adapted to each audience as in US5. Planned paths MUST
  be inspectable and not startable.
- **FR-020**: `/register` MUST replace `/sign-up` as the registration route, with no change to validation, no-enumeration
  behavior or the email-verification flow. `/sign-up` MUST redirect to `/register` and keep its query string.
- **FR-021**: Public pages MUST each have a descriptive title and description, and the product MUST provide a share preview
  (title, description and image) served from the application origin. Content readable by crawlers without running scripts
  is not required in this release, and the share preview MAY be one product-level preview for all routes.
- **FR-022**: The public footer MUST identify the product and link to the curriculum, registration and sign-in. Once the owner
  supplies them, it MUST also show the publisher identity and contact details and link to the privacy notice and terms.
- **FR-022a**: `/privacy` and `/terms` MUST present owner-supplied text. That text and the publisher details MUST NOT be generated,
  inferred or filled with placeholders. Until supplied, their links MUST stay hidden and those routes MUST show the not-found
  page. When supplied, registration MUST also link to both, with no acceptance being recorded,
  and the learning shell's footer MUST link to both and show the contact details.

#### Authenticated learning experience

- **FR-023**: The learning shell MUST provide consistent access to the dashboard, curriculum and account, and a sign-out
  action, on every authenticated screen.
- **FR-024**: Module pages MUST NOT show promotional or unrelated elements while a learner reads (S001 NFR-012). The
  learning shell MUST contain no marketing content.
- **FR-025**: Module pages MUST provide orientation: current lesson, access to all lessons, practice and adjacent modules,
  and the path overview. Per-lesson completion marks MUST NOT be shown, because that data is not available.
- **FR-026**: Links to a lesson section MUST bring that section into view, unobscured and focused, on direct load and on
  in-app navigation.
- **FR-027**: Each lesson MUST have unique identifiers, and existing link formats MUST keep working.
- **FR-028**: Lesson views MUST be recorded for a lesson of any height at any supported width, without changing the data recorded
  or the request sent, and only for lessons the learner has actually reached, whether by scrolling or by following a link.
- **FR-029**: Long prose MUST use a reading measure whose median line is 65–75 characters, and no line may exceed 90 (S001 NFR-012).
  Code, diagrams and tables MAY use a wider column.
- **FR-030**: The dashboard MUST keep all data of S001 FR-038 and FR-040 and, for a learner with progress, MUST show active path,
  competency progress, next step, "Continue" and a summary of completed and pending modules together at 1280 × 800. Progress MUST express demonstrated competencies only.
- **FR-031**: Competency evidence MUST open a review of the recorded result rather than starting or resuming an attempt, using
  existing attempt history (S001 FR-041).
- **FR-032**: Knowledge-check presentation MUST keep question order, immediate feedback, answer locking, threshold,
  unanswered-question confirmation, retries and best-score behavior unchanged.
- **FR-033**: Challenge layouts MUST allow problem context and editor to be seen together at 1280 px or wider, and both to remain
  reachable at narrow widths. Autosave, drafts, hints, reset, runs, submissions, history and reference explanation
  behavior MUST NOT change.
- **FR-034**: The editor MUST have an accessible name and a visible instruction for leaving it by keyboard.
- **FR-035**: Laboratory presentation MUST keep the four element kinds, educational labeling, failure explanations, comparison and
  approval behavior. Replay controls MUST offer every reachable step and MUST NOT allow passing an undecided approval.
- **FR-036**: The laboratory MUST offer a return to the module the learner came from when known, and to the dashboard otherwise.
- **FR-037**: Laboratory, challenge and knowledge-check entries MUST remain reachable from their modules. Global indexes of challenges
  or laboratories are out of scope (see "Requirements That Would Need Architecture Changes").

#### Routes and navigation

- **FR-038**: Routes MUST follow the "Route Map". Every route that exists today MUST remain valid or redirect.
- **FR-039**: Public and learning shells MAY differ, but MUST share the design system and MUST both provide the skip link, offline
  notice and session-expiry warning.
- **FR-040**: `/curriculum` and `/paths/:pathId` MUST use the shell that matches the person's session, with the same content
  rules.
- **FR-041**: Links that currently mean "go to the catalog" MUST point to `/curriculum`. Sign-out and account deletion MUST land on
  `/`. Existing sign-in return behavior MUST be preserved.
- **FR-042**: Every route MUST have a unique, descriptive document title.
- **FR-043**: In-app navigation MUST move focus to a defined starting point, announce the page, and reset the scroll position unless a
  fragment target or browser history restoration applies.

#### Accessibility, responsiveness and states

- **FR-044**: All screens and states MUST meet WCAG 2.2 AA for both audiences, including keyboard operation, visible focus, focus not
  obscured, contrast, target size of at least 24 × 24 CSS px, semantic structure, consistent help and navigation, and screen-reader
  compatibility.
- **FR-045**: Primary controls on touch widths SHOULD be at least 44 × 44 CSS px.
- **FR-046**: Screens MUST work from 320 CSS px to 2560 CSS px and at 200% zoom with no horizontal page scroll, except inside code,
  tables and traces, each of which MUST be keyboard scrollable.
- **FR-047**: Non-essential motion MUST respect reduced-motion preferences. Any animation MUST last no more than 200 ms and MUST NOT
  flash. Automatic replay in the laboratory MUST stay user-initiated and pausable.
- **FR-048**: Controls, focus and statuses MUST remain perceivable in forced-colors mode.
- **FR-049**: Status MUST NOT be conveyed by color alone.
- **FR-050**: Confirmations MUST manage focus: move it in on open, allow dismissal, and return it on close. Their typed
  confirmations and warnings MUST NOT be weakened.
- **FR-051**: Every data view MUST define loading, empty, error and success presentations through shared components, with status changes
  announced, and retry where applicable (S001 FR-052).

#### Preservation

- **FR-052**: All capabilities and scenarios of Spec 001 MUST remain available, except where "Conflicts With Spec 001" records an explicit
  replacement.
- **FR-053**: This initiative MUST NOT change backend architecture, API contracts, database schema, the educational domain model,
  assessment or challenge evaluation semantics, the runner security model, content format or content governance.
- **FR-054**: Code examples MUST be syntax highlighted in the production build under the existing security policy, without weakening
  that policy (S001 FR-009).

### Route Map

| Route | Access | Today | This specification |
|-------|--------|-------|--------------------|
| `/` | Public | Catalog | **Marketing landing** |
| `/curriculum` | Public | Does not exist | **Catalog moves here** |
| `/paths/:pathId` | Public | Path page | Keeps route; redesigned |
| `/sign-in` | Public | Sign-in | Keeps route and return behavior |
| `/register` | Public | Does not exist | **Registration moves here** |
| `/sign-up` | Public | Registration | **Redirects to `/register`** |
| `/check-email`, `/forgot-password` | Public | Exist | Keep routes; redesigned |
| `/verify-email`, `/reset-password` | Public | Exist; linked from emails | **Must not move** |
| `/privacy`, `/terms` | Public | Do not exist | **New**; owner-supplied text; not found until supplied (FR-022a) |
| `/dashboard`, `/dashboard/competencies`, `/account` | Learner | Exist | Keep routes; redesigned |
| `/modules/:moduleId` | Learner | Exists | Keeps route and lesson link format |
| `/knowledge-checks/:checkId` | Learner | Exists | Keeps route |
| `/knowledge-checks/:checkId/history` | Learner | Does not exist | **New**; read-only review of past attempts (FR-031) |
| `/challenges/:challengeId` | Learner | Exists | Keeps route |
| `/lab/:scenarioId` | Learner | Exists | Keeps route |
| Any other | Public | Not found | Redesigned; links to `/` and `/curriculum` |

### Design Token Contract

These are initial values. Later design work may refine them, but each change must re-verify the thresholds.
Ratios were calculated against all four surfaces for this specification, and have not yet been validated in rendered screens.

**Semantic colors**

| Token | Value | Use | Contrast measured against surfaces |
|-------|-------|-----|------------------------------------|
| `surface-canvas` | `#0E1014` | Page background | — |
| `surface-1` | `#15181E` | Cards, shell | — |
| `surface-2` | `#1C2027` | Raised, code, fields | — |
| `surface-3` | `#252A33` | Hover, selected | — |
| `text-primary` | `#EDEFF3` | Body and headings | 12.51–16.54 |
| `text-muted` | `#A9B0BC` | Secondary text | 6.60–8.73 |
| `accent` | `#6E9BFF` | Electric blue: links, primary action, focus-adjacent emphasis | 5.35–7.07 |
| `on-accent` | `#0A0F1F` | Text on accent | 7.08 on accent |
| `accent-secondary` | `#B69CFF` | Violet: laboratory and showcase highlights; never a status | 6.30–8.33 |
| `border-subtle` | `#2E343E` | Decorative separators only | 1.15–1.52 (not relied on) |
| `border-control` | `#6B7482` | Field and control boundaries | 3.05–4.03 |
| `focus-ring` | `#9CC0FF` | Focus indicator, always with a gap from the control | 7.82–10.33 |
| `success` | `#4FD18B` | Passed, demonstrated | 7.43–9.82 |
| `warning` | `#F2C14E` | In progress, caution | 8.58–11.35 |
| `danger` | `#FF8F85` | Failed, destructive | 6.53–8.63 |
| `on-danger` | `#1F0705` | Text on destructive actions | 8.73 on danger |

**Thresholds**: normal text ≥ 4.5:1; large text and essential interface graphics ≥ 3:1. These apply to code tokens, diagrams and the
editor. A primary action sits 1.46:1 from the focus color, so the focus ring MUST be separated from it by a visible gap.

**Typography**: one self-hosted, openly licensed sans-serif family for interface and prose, and one monospaced family for code; a
separate display family is allowed only for public headlines. Fallback stacks are mandatory. Final families are chosen in design work.

| Role | Size | Line height |
|------|------|-------------|
| Display (public only) | 2.75–4 rem | 1.05–1.15 |
| Page title | 2–2.75 rem | 1.15–1.2 |
| Section title | 1.5–1.875 rem | 1.25 |
| Subsection title | 1.25 rem | 1.35 |
| Lesson prose | 1.0625–1.125 rem | ≥ 1.6 |
| Interface text | 1 rem | ≥ 1.5 |
| Small text | 0.875 rem minimum | ≥ 1.45 |
| Code | 0.875–0.9375 rem | ≥ 1.5 |

**Spacing**: 4, 8, 12, 16, 24, 32, 48, 64, 96 px. **Radius**: 6 px controls, 10 px surfaces, full for badges. **Elevation**: conveyed by surface
tokens and borders first; one shadow token for overlays. **Motion**: 120–200 ms, removed under reduced motion. **Layout**: content up to 1200 px;
public sections may run full width behind that content; breakpoints at 600, 900 and 1200 px.

### Claim Register

Public statements MUST be supported by this table, or the table must be updated with a source first.

| Allowed statement | Source | Condition |
|-------------------|--------|-----------|
| Number of modules, effort and competencies of a path | Published catalog and path data | Read live, never fixed copy |
| One path available; others planned, with no dates | Published catalog | Read live |
| Progress reflects demonstrated competencies, not content read | S001 FR-036 | — |
| Each module includes a knowledge check and at least one code challenge | S001 FR-007, FR-008; validated in content | — |
| Code is evaluated automatically against tests, with feedback per criterion | S001 FR-022 | Do not call it tamper-proof (S001 D1) |
| Challenge code runs isolated, without network | S001 FR-022a | Production runner must use the required runtime |
| Laboratory replays curated recordings; no language model is called | S001 FR-033 | This must be stated wherever the laboratory is promoted |
| Laboratory covers tools, patterns, failures and human approval | S001 FR-026–FR-031 | Practice only; not evidence |
| Vendor-neutral foundations; vendor notes identified as such | Constitution VI, S001 FR-011 | — |
| Entry prerequisites | Published path data | Read live |
| Publisher identity, contact details, privacy notice and terms | Supplied by the owner | Published only as supplied |

**Explicitly unsupported today**:

- "Certified", "accredited" or any credential: out of scope in S001; evaluation is not tamper-proof (S001 D1).
- "Expert-reviewed": the subject-matter review (S001 T121) is pending.
- "WCAG compliant": the manual audit (S001 T123) is pending, until this specification's gate passes.
- "Free", prices or plans: billing is out of scope, and no commercial terms have been defined.
- Learner counts, satisfaction or employment outcomes, customers, or partners.
- Real-time AI tutoring, live agent execution, or video courses.
- Availability, uptime or production-readiness guarantees: there is no public deployment yet (S001 R12).

### Key Entities

No data entities change. New presentation-only items are the **design tokens**, the **claim register** and the **route map**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Quality gates (release acceptance)**

- **SC-001**: An automated WCAG 2.2 A and AA audit reports 0 critical and 0 serious findings on every route and key state at 360 px and 1280 px
  (baseline: 13 serious findings on 2 screens).
- **SC-002**: A manual walkthrough of every key journey using keyboard only, and with two screen-reader and browser combinations, finishes with 0
  blocking issues, and results are recorded (baseline: never run).
- **SC-003**: 100% of text and essential graphics meet the contrast thresholds, including code, diagrams and the editor (baseline lows: 1.18, 2.29, 3.26,
  4.43 and 1.48).
- **SC-004**: All Spec 001 validation scenarios V1–V7 pass, and every existing automated test passes; test edits are limited to the route and copy
  changes this specification records.
- **SC-005**: A review of the delivered change shows 0 modifications to API contracts, database migrations, backend, runner and content, apart from the start command in `backend/Dockerfile` (see Clarifications).
- **SC-006**: 100% of factual statements on public pages match the claim register, and an audit finds 0 forbidden items.
- **SC-007**: 100% of lesson links reach their target, visible and focused (baseline: 0%).
- **SC-008**: 100% of routes have a unique title, and in-app navigation moves focus to the defined starting point (baseline: 0%).
- **SC-009**: Every route shows no horizontal page scroll at 320, 360, 768, 1024, 1440 and 2560 CSS px and at 200% zoom.
- **SC-010**: Screen-level visual declarations fall from 64 to only those computed from data, and all colors in shared styles come from tokens.
- **SC-011**: An approved visual reference exists for each route at 360 px, 768 px and 1280 px, covering loading, empty, error and success states where they
  apply, and any later visual difference requires explicit approval.

**Performance**

- **SC-012**: The landing page becomes readable within 2 seconds for 95% of views on typical broadband and transfers no more than 300 KB compressed on first
  visit, fonts included, without the code editor or the diagram and code-highlighting engines (baseline application entry: 122 KB, without custom fonts).
- **SC-013**: Module pages stay readable within 2 seconds and knowledge-check feedback within 1 second, for 95% of cases (S001 NFR-003), and text stays visible
  while fonts load.

**Learner and visitor outcomes** (moderated testing with at least 5 developers from the target audience, who have not seen the product)

- **SC-014**: After 30 seconds on the landing page, at least 80% can correctly state what the product teaches, that learning is hands-on, and that one path is
  available today.
- **SC-015**: A first-time visitor goes from `/` to the first lesson in under 3 minutes including account creation and email verification, and a visitor who already
  has an account does so in under 2 minutes (preserves S001 SC-001 and SC-010, now starting from the new landing page).
- **SC-016**: At least 90% can state their current path, progress and next step after 10 seconds on the dashboard (preserves S001 SC-002).
- **SC-017**: After 30 minutes of study, participants rate reading comfort at 4 or more out of 5 on average.
- **SC-018**: Participants rate the product as professional and credible at 4 or more out of 5 on average, and none report a claim they found misleading.

**Public launch gate** (does not block completing this specification's implementation)

- **SC-019**: Public registration does not open until the owner has supplied the real privacy notice and terms, replacing any temporary text, and the publisher identity and contact details, and all are
  published and linked (baseline: none exist).

## Regression Risks

| ID | Risk | Mitigation or check |
|----|------|---------------------|
| R-01 | Moving the catalog breaks the catalog test, navigation and "explore curriculum" links | Update only those tests and links; FR-041 |
| R-02 | Splitting the frame loses the skip link, offline notice or session-expiry warning | FR-039; check in every shell |
| R-03 | Sign-out stops being a button, breaking the shared test sign-in step | Keep the role and name, or change the fixture deliberately in one reviewed step |
| R-04 | Moving verification or reset pages breaks links in sent emails | Route map prohibits it; run V7.1 through real email |
| R-05 | Theme is fixed in the frame but code, diagrams or editor keep reading the operating system | FR-004; test with light and dark preferences |
| R-06 | Fixed headers cover focus or fragment targets, especially at 200% zoom | FR-026, FR-044; test at zoom |
| R-07 | Larger type lengthens lessons, so more of them miss the lesson-view threshold | FR-028; test long lessons at narrow widths |
| R-08 | Giving access to all replay steps lets learners skip an approval, since the current jump action allows it | FR-035; add a test for both branches |
| R-09 | Layout changes disturb autosave, drafts, hint recording or result polling in challenges | Behavior frozen by FR-033; run V4, V7.2 and V7.3 |
| R-10 | Styling changes break answer locking, focus handling or feedback announcements in checks | FR-032; run V2 with a screen reader |
| R-11 | Structural test selectors (code block, question, option, ordering list, result, editor) break | Keep them, or replace them with role-based selectors in the same change |
| R-12 | Fonts and decoration inflate pages and shift layout | SC-012, SC-013; self-hosting with fallback metrics |
| R-13 | The security policy blocks fonts, images or a theme script at production only | Test the production build under the real policy, not only the development server |
| R-14 | Rendered lesson content has elements the new styles miss (tables, nested lists, callouts) | Check against all five modules, not a sample |
| R-15 | Landing copy drifts from published content | FR-016; review showcases at each content release |
| R-16 | Planned paths look available in a more attractive card design | US5 scenario 2; test at each width |
| R-17 | Softer visual treatment weakens warnings for reset, deletion or approval | FR-050; review copy and prominence |
| R-18 | Marketing language leaks into the learning shell or into result messages | FR-024; copy review |
| R-19 | The "Last reviewed" date looks like expert review, although it is the drafting date until S001 T121 finishes | No promotion of the date; complete T121 before public launch |

## Conflicts With Spec 001

Spec 001 is not modified. Where they differ, this specification takes precedence once approved.

| Item | Spec 001 | This specification | Resolution |
|------|----------|--------------------|------------|
| Landing route | S001 T072 makes the catalog the landing route; quickstart V1 opens `/`; a test expects "Curriculum" at `/` | `/` is marketing; catalog at `/curriculum` | **Replaced**; the validation step applies to `/curriculum` |
| Registration route | `/sign-up` | `/register` | **Replaced**, with redirect |
| Theme | Follows the operating system, light and dark | Dark only at launch | **Replaced** |
| Search value | S001 R2 sees little value in search visibility and defers pre-rendering | Marketing-first public site, without crawler-readable content in this release | **Compatible**; pre-rendering stays deferred, to be reconsidered before public deployment |
| Minimum width | S001 NFR-002: 360 px | 320 CSS px to meet WCAG reflow | **Strengthened**; 360 px remains tested |
| Audit gate | S001 SC-007: no critical issues | No critical or serious issues, plus manual audit | **Strengthened** |
| Constitution I | Version 1.0.0 required every feature to contribute directly to a measurable learning outcome | A marketing page is indirect | **Resolved** by constitution 1.1.0, which allows public orientation surfaces under conditions: accurate information (FR-015, SC-006), a measurable route to the first lesson (SC-015), and no promotion in the learning environment (FR-024) |

### Spec 001 gaps found during inspection

| Gap | Evidence | Disposition |
|-----|----------|-------------|
| S001 FR-041: knowledge-check review is not available | History endpoint exists but is unused; evidence links open the live check | **Included** (FR-031), frontend only |
| S001 FR-032: jump to any step | Only steps already reached are offered | **Included** (FR-035) |
| Journey 4: return to the module from the laboratory | Only a dashboard link; scenario files list no modules | **Included** (FR-036), from navigation origin |
| Lesson links and lesson views | See baseline | **Included** (FR-026, FR-028) |
| S001 FR-009: code highlighting in production | See baseline | **Included** (FR-054), frontend only |
| S001 T123: manual accessibility audit | Unchecked | **Included** as a gate (SC-002) |
| S001 US6 scenario 3: missing prerequisites in the catalog | The public catalog has no learner data | **Not included**; needs a contract change |
| S001 T121: subject-matter review | Pending | **Not included**; content work; blocks the related claim |

## Requirements That Would Need Architecture Changes

These are **not** part of this specification. No current requirement depends on them.

| Capability | Why it is not possible today | Handling here |
|------------|------------------------------|---------------|
| Global laboratory or challenge index | No listing exists; collecting them through modules would record false content views | Reached from modules (FR-037) |
| Public trial of a laboratory or challenge | Those endpoints require a session; challenges also consume runner capacity | Read-only showcases (FR-017) |
| Per-lesson completion marks | The API exposes module status only | Module status only (FR-025) |
| Personalized prerequisites in the catalog | The catalog is anonymous | Shown on module pages, as today |
| Server-side rendering of public pages | Adds a server runtime | Out of scope; build-time generation of `/` remains possible later |
| Conversion analytics | No such capability; privacy constraints apply (S001 NFR-007) | Moderated testing (SC-014–SC-018) |
| Newsletter, waitlist, contact form, or "notify me" on planned paths | Requires storage or email flows | Out of scope |
| Recording acceptance of terms or privacy notice | Requires storing new data per account | Links only (FR-022a); if legal advice requires a record, it needs its own specification |
| Resending the verification email | The contract has no dedicated operation | Existing behavior kept |

## Scope

**In scope**: design system; public and learning shells; landing page; curriculum and path pages; pages to present owner-supplied legal text; authentication and account screens; dashboard; modules and lessons;
knowledge checks; challenges; laboratory; route changes and redirects; string updates; accessibility fixes; test updates and visual references.

**Out of scope**: everything under "Requirements That Would Need Architecture Changes"; a light theme or theme selector; writing legal text; billing and pricing; certificates; social features; new learning content; lesson text
changes; Spanish translation; native applications; a marketing content management system; a blog; AI tutoring.

## Technical Constraints

Set by the product owner and repeated here because they bound the plan: React 19, TypeScript, Vite, React Router, TanStack Query, the existing Markdown, diagram and code-editor
integrations, the existing internationalization infrastructure and the existing testing tools remain in place.

## Assumptions

Reasonable defaults; each can be changed during review.

- Electric blue is the primary accent. Violet is reserved for laboratory and showcase highlights, so that interactive meaning stays unambiguous.
- A signed-in learner who opens `/` sees the landing page with a dashboard action and is not redirected. Sign-in continues to land on the dashboard.
- `/curriculum` and `/paths/:pathId` appear in the frame that matches the session, rather than one fixed frame.
- Lessons stay on one module page with section links; no per-lesson route is introduced.
- Public copy is written in English only (S001 FR-054), through the existing string infrastructure.
- The public site does not state the commercial model until the owner defines it. "Commercial" here describes the quality of presentation and does not add billing.
- The text of system emails stays unchanged; their links and destinations do not move.
- Supported browsers stay as in Spec 001 (last 2 versions of major browsers).

## Dependencies

- Owner-supplied privacy notice, terms, publisher identity and contact details, ideally with legal advice. These block public launch, not implementation (SC-019).
- Selection and licensing of the typefaces during design work.
- Review of public copy against the claim register before release.
- Participants for moderated testing, and a person able to run the manual accessibility audit.
- Subject-matter review (S001 T121) before any public launch, though not for this specification's implementation.
