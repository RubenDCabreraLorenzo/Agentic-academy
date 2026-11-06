# Feature Specification: Agentic Academy MVP

**Feature Branch**: `claude/gifted-davinci-t1hlbh`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Agentic Academy — a web application that helps developers learn Agentic AI
engineering through a structured, progressive and practical learning experience. MVP: structured
learning dashboard, at least one complete introductory learning path, modules with text, code
examples and practical exercises, basic knowledge assessments, persistent learning progress and a
basic practical laboratory experience. No technology stack or architecture at this stage."

## Glossary

- **Learning path**: An ordered sequence of modules with defined objectives, prerequisites and a
  level (foundational, intermediate, advanced).
- **Module**: A unit of study inside a path. Contains lessons, code examples, diagrams, a knowledge
  check and, for major modules, at least one practical challenge.
- **Learning objective**: A specific, observable statement of what the learner will be able to do
  after the module (e.g. "Explain the difference between a workflow and an agent").
- **Competency**: A named capability (e.g. "Design a tool schema") with a level. Competencies are
  demonstrated through assessments and challenges, never through reading alone.
- **Knowledge check**: A short assessment that evaluates conceptual understanding.
- **Challenge**: A practical exercise with a problem statement, expected outcome, instructions,
  evaluation criteria, hints and feedback.
- **Laboratory scenario**: An interactive, inspectable agent execution used to explore how agents
  behave (steps, tool calls, state, traces).
- **Learner**: The person using the platform to learn.
- **Content maintainer**: The person who authors, reviews and updates educational content.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Study a module of the introductory learning path (Priority: P1)

A developer with basic programming experience opens Agentic Academy, chooses the introductory path
"Foundations of Agentic AI Engineering", sees what they will learn, what they are expected to know
already and how the path is structured, and studies the first module: technical explanations, code
examples, architecture diagrams and links to reference documentation. The module states why each
design decision is made and labels each technique as established, emerging or experimental.

**Why this priority**: Without readable, accurate and structured content there is no learning
platform. This is the smallest slice that already delivers educational value (Constitution I, III).

**Independent Test**: Load the introductory path, open any module and verify that objectives,
prerequisites, explanations, code examples, at least one diagram and reference links are presented
and readable on desktop and mobile widths, without any other capability being available.

**Acceptance Scenarios**:

1. **Given** a learner on the path page, **When** they view it, **Then** they see the path title,
   level, learning objectives, prerequisites, expected competencies, estimated effort and the
   ordered list of modules.
2. **Given** a learner opens a module, **When** the module loads, **Then** they see its objectives,
   prerequisites, lesson content, code examples, diagrams and reference links, in that structure.
3. **Given** a code example in a module, **When** the learner views it, **Then** it is shown with
   syntax highlighting, the language label, a copy action and any explanatory annotations, and
   long lines remain readable without breaking the page layout.
4. **Given** a lesson that describes a vendor-specific feature, **When** the learner reads it,
   **Then** the content explicitly identifies the vendor or framework and its limitations
   (Constitution VI).
5. **Given** a technique presented in a lesson, **When** the learner reads it, **Then** it carries a
   maturity label: established, emerging or experimental.
6. **Given** a learner on a module, **When** they use the navigation, **Then** they can move to the
   previous or next module and back to the path overview with a consistent layout across modules.

---

### User Story 2 - Validate understanding with knowledge checks (Priority: P1)

After studying a module, the learner answers a short knowledge check. They receive immediate,
explanatory feedback for each answer and learn whether they reached the passing threshold. If not,
they can review the related content and retry.

**Why this priority**: The constitution requires progress to reflect demonstrated learning rather
than content consumption (Constitution VII). Knowledge checks are the minimum evidence mechanism.

**Independent Test**: Complete a module's knowledge check with a set of correct and incorrect
answers and verify the score, the per-question feedback, the pass/fail result and the retry flow.

**Acceptance Scenarios**:

1. **Given** a learner on a module, **When** they open its knowledge check, **Then** they see the
   number of questions, the passing threshold and the learning objectives being assessed.
2. **Given** a learner submits an answer, **When** the answer is evaluated, **Then** they see
   whether it is correct and an explanation of why, including a reference to the relevant lesson
   section.
3. **Given** a learner finishes the knowledge check with a score at or above the threshold,
   **When** results are shown, **Then** the check is marked as passed and the associated
   objectives are marked as demonstrated.
4. **Given** a learner finishes below the threshold, **When** results are shown, **Then** the check
   is marked as not passed, the weak objectives are identified, links to the related content are
   offered and the learner can retry.
5. **Given** a learner retries a knowledge check, **When** they start again, **Then** the questions
   are presented again (order may vary) and the best result is kept.

---

### User Story 3 - Track progress on the learning dashboard (Priority: P2)

A returning learner opens the dashboard and immediately sees where they left off, how far they are
in each path, which competencies they have demonstrated and which objectives remain incomplete.
Progress survives closing the browser and returning on another day.

**Why this priority**: Persistent, visible, competency-based progress is an explicit MVP goal and a
constitutional requirement (Constitution III, VII; UX standard on understandable progress).

**Independent Test**: Complete part of a path, end the session, return later and verify that the
dashboard shows the same progress, a "continue" entry point and the list of demonstrated and pending
competencies and objectives, all from a single screen.

**Acceptance Scenarios**:

1. **Given** a learner with progress, **When** they open the dashboard, **Then** they see, on one
   screen, the active path, percentage of competencies demonstrated, the next recommended step and
   a summary of completed and pending modules.
2. **Given** a learner who passed a knowledge check and completed a challenge in a module,
   **When** they view the dashboard, **Then** the module is shown as completed and its competencies
   as demonstrated.
3. **Given** a learner who only read a module's lessons, **When** they view the dashboard, **Then**
   the module is shown as "in progress" (content viewed) and its competencies as not yet
   demonstrated.
4. **Given** a learner returns after closing the application, **When** they open the dashboard,
   **Then** all previously recorded progress is present and a "continue where you left off" action
   takes them to their last position.
5. **Given** a learner on the dashboard, **When** they open the competency view, **Then** they see
   each competency of the path with its level (foundational, intermediate, advanced), its status and
   the evidence that demonstrated it (knowledge check or challenge).
6. **Given** a new learner with no progress, **When** they open the dashboard, **Then** they see a
   welcome state that explains the curriculum and invites them to start the introductory path.

---

### User Story 4 - Complete a practical challenge (Priority: P2)

At the end of a major module the learner takes on a practical challenge based on a realistic
engineering scenario (e.g. "design the tool definitions for a support-ticket triage agent"). The
challenge states the problem, the expected outcome, instructions and evaluation criteria. The
learner submits their solution, receives actionable feedback against each criterion and can request
progressive hints.

**Why this priority**: Hands-on practice is a core principle (Constitution II), but the content and
assessments of stories 1–3 already deliver a usable learning experience on their own.

**Independent Test**: Open a challenge, request hints, submit a solution that meets some criteria
and fails others, and verify the per-criterion feedback, the result and the resubmission flow.

**Acceptance Scenarios**:

1. **Given** a learner opens a challenge, **When** it loads, **Then** they see the scenario, the
   problem statement, the expected outcome, step-by-step instructions, the evaluation criteria and
   the objectives/competencies it validates.
2. **Given** a learner is stuck, **When** they request a hint, **Then** hints are revealed one at a
   time, from general to specific, and the number of hints used is recorded.
3. **Given** a learner submits a solution, **When** it is evaluated, **Then** they receive a result
   per evaluation criterion (met / not met) with actionable feedback explaining what to change.
4. **Given** a solution meets all mandatory criteria, **When** the result is shown, **Then** the
   challenge is marked as completed and the related competencies as demonstrated.
5. **Given** a solution does not meet all mandatory criteria, **When** the result is shown,
   **Then** the learner can revise and resubmit, and previous submissions remain reviewable.
6. Challenges are evaluated by
   [NEEDS CLARIFICATION: How are practical challenges evaluated in the MVP? (A) automatic
   evaluation of submitted code against tests in a sandbox, (B) structured submissions such as
   configuration, tool schemas, design choices or execution-trace analysis evaluated automatically
   against defined criteria, or (C) self-assessment against a rubric with a reference solution?]

---

### User Story 5 - Explore an agent run in the basic laboratory (Priority: P3)

The learner opens the laboratory from a module and runs a predefined scenario (e.g. a research agent
that uses a search tool and a calculator). They step through the execution: the input, each
reasoning/decision step, each tool invocation with its arguments and result, the evolving state and
the final answer. They can switch between two orchestration patterns on the same task (e.g. a fixed
workflow vs. an agent loop) and compare the resulting traces. Scenarios include failure cases such
as a failing tool, a hallucinated tool argument or a prompt-injection attempt.

**Why this priority**: The laboratory is part of the MVP, but in a minimal form. It deepens
understanding of execution flows, tool use and failures, yet the platform delivers value without it.

**Independent Test**: Open a laboratory scenario, step forward and backward through its execution,
inspect a tool call and the state at each step, switch orchestration pattern and verify the
comparison view, including one failure scenario.

**Acceptance Scenarios**:

1. **Given** a learner opens a laboratory scenario, **When** it loads, **Then** they see the task,
   the available tools with their declared permissions, the orchestration pattern and the learning
   objective of the scenario.
2. **Given** a scenario is running or replaying, **When** the learner steps through it, **Then** each
   step shows its type (model decision, tool call, tool result, state update, final answer), its
   inputs and outputs and the state at that point.
3. **Given** a long-running execution, **When** it is in progress, **Then** the learner sees its
   current status and progress, and can stop it.
4. **Given** a scenario supports two orchestration patterns, **When** the learner selects compare,
   **Then** both traces are shown side by side with differences in steps, tool calls and outcome
   highlighted.
5. **Given** a failure scenario (tool error, invalid tool argument, prompt injection, excessive
   autonomy), **When** the learner inspects it, **Then** the failing step is highlighted and an
   explanation describes the risk and the mitigation (Constitution V).
6. **Given** a scenario includes a potentially destructive tool action, **When** the agent reaches
   it, **Then** the execution pauses and requires explicit learner approval before continuing,
   demonstrating human oversight.
7. Laboratory executions are
   [NEEDS CLARIFICATION: Does the MVP laboratory call real language models? (A) No — it replays
   curated, pre-recorded executions that the learner can step through and modify only within
   predefined options, (B) Yes, using a model access key supplied by the learner (bring your own
   key), (C) Yes, using platform-provided model access with usage limits.]

---

### User Story 6 - Explore the curriculum and prerequisites (Priority: P3)

A learner wants to understand the full curriculum before committing. They browse the catalog of
learning paths, see each path's level, prerequisites, competencies and status (available or
planned), and understand the recommended order from LLM foundations to production deployment.

**Why this priority**: It orients learners and makes the progressive structure visible, but in the
MVP only one path is fully available, so its value is mainly informational.

**Independent Test**: Open the catalog and verify every path shows level, prerequisites, competencies
and availability, and that planned paths cannot be started but can be inspected.

**Acceptance Scenarios**:

1. **Given** a learner opens the catalog, **When** it loads, **Then** paths are grouped or ordered
   by level and the recommended order is visible.
2. **Given** a planned (not yet available) path, **When** the learner views it, **Then** they see its
   description, prerequisites and competencies, and it is clearly marked as not yet available.
3. **Given** a path with prerequisites the learner has not demonstrated, **When** they open it,
   **Then** they see which prerequisites are missing and a link to where they are taught, and they
   can still choose to proceed.

---

### User Story 7 - Maintain educational content safely (Priority: P3)

A content maintainer updates a module (fixes an example, marks a model or API as deprecated, adds a
question) and publishes a new content version. Learners' existing progress remains consistent and
deprecated material is clearly identified.

**Why this priority**: Required by the Educational Content Governance standard, but the learner
experience can be validated before it exists in a polished form.

**Independent Test**: Publish a new version of a module that changes a knowledge check and marks an
example as deprecated; verify that learners who already passed keep their result, that the
deprecation notice is visible and that the path's prerequisite order is still valid.

**Acceptance Scenarios**:

1. **Given** a module is updated, **When** a new version is published, **Then** the content carries
   a version identifier and a last-reviewed date visible to learners.
2. **Given** an example uses a deprecated API, framework or model, **When** it is marked as
   deprecated, **Then** learners see a notice with the reason and, when available, the replacement.
3. **Given** a learner already demonstrated a competency, **When** the related assessment changes,
   **Then** the demonstrated status is preserved and attributed to the version they completed.
4. **Given** an update would break a prerequisite relationship or reference a missing module,
   **When** the maintainer tries to publish it, **Then** publication is rejected with a clear
   explanation of the inconsistency.

### User Journeys

1. **First visit → first demonstrated competency**: Learner arrives → sees the welcome dashboard →
   opens the catalog or directly the introductory path → reads objectives and prerequisites →
   studies Module 1 → passes its knowledge check → sees the first competency marked as demonstrated
   on the dashboard.
2. **Returning learner**: Learner returns → dashboard shows progress and "continue" → resumes at
   the last lesson → completes the module's challenge → dashboard updates competencies and the next
   recommended step.
3. **Struggling learner**: Learner fails a knowledge check → sees weak objectives → follows links to
   the relevant lesson sections → retries → passes.
4. **Hands-on exploration**: From the "Tools and function calling" module, the learner opens the
   linked laboratory scenario → steps through the trace → inspects a tool call → compares workflow
   vs. agent loop → inspects the prompt-injection failure case → returns to the module.
5. **Path completion**: Learner completes all modules of the introductory path → sees a path
   completion summary with all demonstrated competencies, evidence and the recommended next path.

### Edge Cases

- The learner opens a module whose prerequisites are not demonstrated: the platform warns and links
  to the prerequisite, but does not block access.
- The learner submits a knowledge check with unanswered questions: they are told which questions
  are missing before submission; unanswered questions count as incorrect only if they confirm.
- The learner loses connectivity while answering or submitting: answers in progress are not lost
  and the submission can be retried; no partial or duplicated results are recorded.
- The learner uses the platform in two browser tabs or devices at the same time: progress is merged
  without losing any demonstrated competency; the most advanced state wins.
- Content is updated while a learner is in the middle of a module or knowledge check: the learner
  finishes the version they started.
- A module, path or laboratory scenario fails to load: the learner sees a clear error state with a
  retry action, and the rest of the application remains usable.
- An external AI service (if used by the laboratory or challenge feedback) is unavailable, slow or
  returns an error: the learner sees a clear status, the application does not fail uncontrollably,
  and any learning content not depending on it remains usable.
- A laboratory execution exceeds its time or step budget: it is stopped, the partial trace is kept
  and the reason is explained.
- A learner submits content that attempts prompt injection or contains secrets: it is handled
  safely, secrets are never echoed back or logged, and the learner is informed when relevant.
- Very long code examples or traces on small screens remain readable through horizontal scrolling
  inside the code/trace area without breaking the page layout.
- A learner resets progress on a path: they are asked for confirmation, since the action is
  irreversible.
- A learner who completed all available content: the dashboard shows completion and the planned
  paths as upcoming.

## Requirements *(mandatory)*

### Functional Requirements

**Curriculum and learning paths**

- **FR-001**: The system MUST present a catalog of learning paths, each with title, description,
  level (foundational, intermediate, advanced), learning objectives, prerequisites, competencies,
  estimated effort and availability status (available or planned).
- **FR-002**: The system MUST present the curriculum roadmap covering, in progressive order: LLM
  foundations, agent fundamentals, tools and function calling, memory and state management, agent
  orchestration and workflows, multi-agent architectures, MCP, RAG and knowledge integration, agent
  evaluation and observability, security and responsible AI, and production deployment.
- **FR-003**: The MVP MUST include one complete, available introductory path, "Foundations of
  Agentic AI Engineering", covering at least: LLM foundations, agent fundamentals, tools and
  function calling, memory and state management, and an introduction to evaluation, observability
  and agentic risks. Paths covering the remaining topics MAY be shown as planned.
- **FR-004**: Each path MUST contain modules in a defined order, and each module MUST declare its
  prerequisites (modules or competencies) and the competencies it develops.
- **FR-005**: The curriculum MUST introduce single-agent concepts before any multi-agent
  architecture content.
- **FR-006**: When a learner opens a module or path whose prerequisites they have not demonstrated,
  the system MUST show which prerequisites are missing and where they are taught, without blocking
  access.

**Modules and content**

- **FR-007**: Each module MUST present learning objectives, prerequisites, lesson content, at least
  one code example, at least one architecture or flow diagram, reference links and a knowledge
  check.
- **FR-008**: Each major module MUST include at least one practical challenge or laboratory
  scenario.
- **FR-009**: Code examples MUST be displayed with syntax highlighting, a language label, a copy
  action and optional annotations, and MUST remain readable on all supported screen sizes.
- **FR-010**: Each technique or practice presented MUST carry a maturity label: established,
  emerging or experimental.
- **FR-011**: Content that describes a vendor-, model- or framework-specific feature MUST identify
  the vendor/framework and its limitations; core concepts MUST be explained independently of any
  vendor.
- **FR-012**: Lessons MUST explain the reasoning behind architectural and engineering decisions,
  not only the steps.
- **FR-013**: The content of the introductory path MUST explicitly address hallucinations, prompt
  injection, excessive autonomy, least-privilege tool access and human oversight.
- **FR-014**: Diagrams MUST have a text alternative that conveys the same information.
- **FR-015**: Learners MUST be able to navigate to the previous and next module and back to the
  path overview from any module, with consistent navigation across all modules.

**Knowledge checks**

- **FR-016**: Each module MUST include a knowledge check with at least 5 questions mapped to the
  module's learning objectives, supporting at least single-choice, multiple-choice and
  ordering/matching question types.
- **FR-017**: Each knowledge check MUST state its passing threshold before the learner starts; the
  default threshold is 70% unless a module defines another.
- **FR-018**: The system MUST give per-question feedback that explains why an answer is correct or
  incorrect and links to the relevant lesson section.
- **FR-019**: When a learner does not pass, the system MUST identify the objectives not demonstrated
  and allow unlimited retries, keeping the best result.
- **FR-020**: Questions SHOULD include scenario-based items that require applying a concept, not
  only recalling a definition.

**Practical challenges**

- **FR-021**: Each challenge MUST define: a realistic scenario, a problem statement, the expected
  outcome, instructions, evaluation criteria (mandatory and optional), the competencies validated,
  at least two progressive hints and a reference explanation shown after completion.
- **FR-022**: The system MUST evaluate challenge submissions against each evaluation criterion and
  give actionable feedback per criterion. The evaluation method is: [NEEDS CLARIFICATION: see
  User Story 4, scenario 6].
- **FR-023**: Learners MUST be able to revise and resubmit a challenge; previous submissions and
  their feedback MUST remain reviewable.
- **FR-024**: The system MUST record the number of hints used and the number of attempts per
  challenge.
- **FR-025**: Challenges within a path MUST increase in complexity from the first to the last
  module.

**Laboratory (minimum viable)**

- **FR-026**: The system MUST provide at least three laboratory scenarios linked to the introductory
  path: (a) a single agent using tools, (b) the same task solved by a fixed workflow and by an agent
  loop for comparison, (c) at least one failure case (tool error, invalid tool argument or prompt
  injection).
- **FR-027**: The laboratory MUST let learners step forward and backward through an execution and
  inspect each step's type, inputs, outputs and the agent state at that point.
- **FR-028**: The laboratory MUST show, for every scenario, the tools available to the agent and
  their declared permissions.
- **FR-029**: The laboratory MUST show two executions side by side and highlight differences in
  steps, tool calls and outcome.
- **FR-030**: When a scenario reaches a potentially destructive or irreversible tool action, the
  execution MUST pause and require explicit learner approval; rejecting MUST be a valid outcome
  that is explained.
- **FR-031**: The laboratory MUST explain the risk and mitigation of each failure case.
- **FR-032**: Executions in progress MUST show their status and progress and MUST be stoppable;
  executions MUST be bounded by a maximum number of steps and duration.
- **FR-033**: The MVP laboratory execution source is: [NEEDS CLARIFICATION: see User Story 5,
  scenario 7].
- **FR-034**: The MVP MUST NOT include multi-agent execution infrastructure; multi-agent concepts
  MAY appear only as explanatory content or pre-defined traces.

**Progress and assessment**

- **FR-035**: The system MUST persist each learner's progress: content viewed, knowledge check
  results, challenge submissions and results, laboratory scenarios explored, and last position.
- **FR-036**: The system MUST distinguish between "content viewed" and "competency demonstrated".
  A competency is demonstrated only when the learner passes the assessments and completes the
  challenges mapped to it.
- **FR-037**: A module MUST be considered completed only when its knowledge check is passed and its
  mandatory challenge (if any) is completed.
- **FR-038**: The dashboard MUST show on a single screen: active path, progress expressed as
  competencies demonstrated out of total, completed and pending modules, the next recommended step
  and a "continue where you left off" action.
- **FR-039**: The system MUST provide a competency view listing each competency with its level,
  status (not started, in progress, demonstrated) and the evidence that demonstrated it.
- **FR-040**: The system MUST list the learning objectives not yet demonstrated, per module and per
  path.
- **FR-041**: Learners MUST be able to review their completed knowledge checks and challenge
  submissions, including feedback received.
- **FR-042**: Upon completing a path, the system MUST show a completion summary with demonstrated
  competencies, evidence and the recommended next path.
- **FR-043**: Learners MUST be able to reset the progress of a path after explicit confirmation.
- **FR-044**: Every learning outcome and assessment item MUST be traceable to at least one
  competency defined in the curriculum.

**Identity and data**

- **FR-045**: Learner identity and progress persistence MUST work as follows: [NEEDS
  CLARIFICATION: Do learners need an account in the MVP? (A) Yes — sign-in is required and progress
  is stored per account and available on any device, (B) No — progress is stored on the learner's
  device/browser only, without an account, (C) Hybrid — usable without an account with local
  progress, and optional sign-in to keep progress across devices.]
- **FR-046**: The system MUST collect only the personal data needed to provide the learning
  experience and MUST let learners delete their progress and personal data.
- **FR-047**: The system MUST NOT expose secrets, credentials or access keys in any part of the
  learner-facing interface, and MUST NOT write them to logs.

**Content governance**

- **FR-048**: Every path, module, assessment, challenge and laboratory scenario MUST carry a version
  identifier and a last-reviewed date.
- **FR-049**: Content maintainers MUST be able to mark APIs, frameworks, models or examples as
  deprecated, with reason and replacement; learners MUST see that notice wherever the item appears.
- **FR-050**: Publishing content MUST be rejected when it introduces broken prerequisite chains,
  references to missing modules or competencies, or assessment items not mapped to a competency.
- **FR-051**: Learner results MUST be recorded against the content version they completed, and
  content updates MUST NOT remove a competency already demonstrated.

**System states and errors**

- **FR-052**: The system MUST communicate loading, empty, error and offline states clearly, with a
  retry action where applicable.
- **FR-053**: A failure of any external service MUST NOT prevent access to learning content,
  progress or assessments that do not depend on it.

### Non-Functional Requirements

- **NFR-001 (Accessibility)**: The application MUST meet WCAG 2.2 level AA for all learner-facing
  screens, including keyboard-only navigation, visible focus, sufficient contrast, screen-reader
  labels and text alternatives for diagrams and traces.
- **NFR-002 (Responsiveness)**: All learner-facing screens MUST be usable at widths from 360 px
  (mobile) to large desktop, without horizontal page scrolling (scrolling inside code or trace
  areas is allowed).
- **NFR-003 (Performance)**: Module pages MUST become readable within 2 seconds for 95% of
  page views on a typical broadband connection; knowledge check feedback MUST appear within
  1 second for 95% of answers.
- **NFR-004 (Reliability)**: No recorded progress may be lost due to a closed tab, network
  interruption or application error once the system has confirmed it as saved.
- **NFR-005 (Availability)**: The learning experience SHOULD be available 99.5% of the time per
  month, excluding announced maintenance.
- **NFR-006 (Security)**: Agents in laboratory scenarios MUST run with explicitly defined
  capabilities and least-privilege tool access; learner input to the laboratory or challenges MUST
  be treated as untrusted.
- **NFR-007 (Privacy)**: Data sent to any external model service MUST be limited to what the task
  requires and MUST NOT include learner personal data.
- **NFR-008 (Observability)**: Laboratory executions MUST record a trace of decisions, tool calls
  and failures that is visible to the learner; the platform MUST record operational errors without
  personal data or secrets.
- **NFR-009 (Maintainability)**: Content MUST be stored and versioned separately from application
  behavior so that maintainers can update it without changing platform functionality.
- **NFR-010 (Agnosticism)**: The laboratory and content model MUST allow adding scenarios based on a
  different model provider or agent framework without changing unrelated parts of the platform.
- **NFR-011 (Quality)**: Critical workflows (studying a module, taking a knowledge check, submitting
  a challenge, saving and viewing progress) MUST be covered by automated tests and automated quality
  checks.
- **NFR-012 (Readability)**: Technical content MUST be presented with a readable line length,
  hierarchy of headings and a reading mode free of distractions.

### Key Entities *(include if feature involves data)*

- **Learning Path**: Ordered set of modules; level, objectives, prerequisites, competencies,
  estimated effort, availability, version.
- **Module**: Belongs to a path; order, objectives, prerequisites, lessons, code examples, diagrams,
  references, knowledge check, challenges, laboratory scenarios, version, last-reviewed date.
- **Lesson**: Content unit inside a module; sections, maturity labels, vendor-specific notes,
  deprecation notices.
- **Learning Objective**: Observable outcome; belongs to a module; mapped to one or more
  competencies.
- **Competency**: Named capability with level (foundational, intermediate, advanced); demonstrated
  by assessments and challenges.
- **Knowledge Check / Question**: Assessment with threshold; questions with type, options, correct
  answer, explanation, mapped objective, link to lesson section.
- **Challenge**: Scenario, problem, expected outcome, instructions, evaluation criteria, hints,
  reference explanation, validated competencies.
- **Laboratory Scenario**: Task, tools with declared permissions, orchestration pattern(s), execution
  steps, failure cases, learning objective.
- **Execution Trace / Step**: Ordered steps with type, inputs, outputs, state snapshot, status.
- **Learner**: Person using the platform; identity model pending clarification (FR-045).
- **Progress Record**: Per learner: content viewed, last position, assessment attempts and results,
  challenge submissions and feedback, scenarios explored, competency statuses with evidence and
  content version.
- **Deprecation Notice**: Item affected, reason, replacement, date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time learner can go from landing on the platform to starting the first lesson
  of the introductory path in under 2 minutes, without help.
- **SC-002**: 90% of test learners can state, after looking at the dashboard for 10 seconds, their
  current path, their progress and their next step.
- **SC-003**: 100% of modules in the introductory path contain objectives, prerequisites, at least
  one code example, at least one diagram with text alternative, a knowledge check mapped to
  competencies and, for major modules, a challenge or laboratory scenario.
- **SC-004**: 100% of assessment items and challenges are traceable to at least one competency.
- **SC-005**: 0 progress records are lost across sessions, device restarts or network interruptions
  in acceptance testing.
- **SC-006**: Learners who complete the introductory path pass an end-of-path assessment at a rate
  of at least 75% on their first or second attempt.
- **SC-007**: At least 80% of learners who receive feedback on a failed challenge attempt rate it as
  "useful to know what to change" in usability testing.
- **SC-008**: At least 70% of learners who start the introductory path complete its first module,
  and at least 40% complete the whole path, in the first beta cohort.
- **SC-009**: All learner-facing screens pass an accessibility audit at WCAG 2.2 AA with no critical
  issues.
- **SC-010**: When an external service the platform depends on is unavailable, 100% of learning
  content, knowledge checks and progress views remain usable.
- **SC-011**: In usability testing, at least 80% of learners can correctly identify, using the
  laboratory, which step of an execution invoked a tool and why a failure case failed.

## MVP Scope

**In scope**

- Learning dashboard with competency-based progress and "continue" entry point.
- Curriculum catalog and roadmap (one available path; remaining paths shown as planned).
- One complete introductory path ("Foundations of Agentic AI Engineering") with modules containing
  lessons, code examples, diagrams, reference links, knowledge checks and challenges.
- Basic knowledge assessments with feedback and retries.
- Persistent progress, competency view and review of past attempts.
- Minimum viable laboratory: at least three inspectable scenarios, step-by-step trace, comparison
  of two orchestration patterns, failure cases and human-approval demonstration.
- Content versioning, review dates and deprecation notices.

**Out of scope**

- Paid subscriptions or billing.
- Social networking features, comments, forums or leaderboards.
- Public user profiles or shareable certificates.
- Enterprise or team administration, instructor dashboards.
- A marketplace for courses or third-party content.
- Complex multi-agent orchestration infrastructure.
- Native mobile applications (the web application must be responsive instead).
- Free-form learner-built agents running arbitrary code or arbitrary tools.
- Content authoring interface inside the application (maintainers may use any versioned workflow).

## Assumptions

- Learners have basic programming knowledge and can read Python code; the introductory path states
  this as a prerequisite and links to external resources for those who lack it.
- Learning content and interface are delivered in English for the MVP; the content model does not
  prevent adding other languages later.
- Learners use a modern desktop or mobile browser with internet connectivity; offline study is not
  required.
- The introductory path contains between 5 and 7 modules, each designed for about 30–90 minutes.
- Knowledge check passing threshold defaults to 70%.
- Content maintainers are members of the project team; there is no public contribution flow in the
  MVP.
- Code examples are illustrative and run in the learner's own environment unless the clarified
  laboratory or challenge evaluation approach provides execution.
- Progress data is retained while the learner keeps it, and is deleted on request.

## Dependencies and Open Questions

**Dependencies**

- Authoring of accurate educational content for the introductory path, its assessments, challenges
  and laboratory scenarios by subject-matter experts, including technical review.
- A defined competency framework (list of competencies with levels) for the introductory path.
- Depending on clarification answers: access to external model services and/or an isolated
  execution environment for code evaluation.

**Open questions (blocking, to be resolved before planning)**

1. Challenge evaluation method (FR-022).
2. Laboratory execution source (FR-033).
3. Learner identity and progress persistence model (FR-045).

**Open questions (non-blocking, assumed defaults above)**

- Should the platform issue a completion certificate in a future release?
- Should the end-of-path assessment be a separate, larger assessment or the aggregation of module
  checks? (Assumed: a separate end-of-path assessment.)
- Which languages, beyond English, should be prioritized after the MVP?
