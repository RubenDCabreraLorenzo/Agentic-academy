# Agentic Academy Constitution

## Core Principles

### I. Learning First — Education-Driven Development

The primary purpose of this application is to teach Agentic AI engineering through structured,
progressive and practical learning experiences.

- Every feature MUST contribute directly to a measurable learning outcome. Public orientation
  surfaces are the only exception: a page whose purpose is to help a person evaluate the platform
  and begin learning, such as a landing page, MAY contribute indirectly, provided that it (a) gives
  only accurate information about objectives, prerequisites and learning methods, (b) has a
  measurable route to the first learning activity, and (c) adds no promotional content to the
  learning environment.
- Educational content MUST prioritize technical accuracy, conceptual clarity and practical
  applicability.
- The platform MUST explain not only how an agent works, but also why architectural and
  engineering decisions are made.
- The application MUST distinguish between established engineering practices, emerging
  approaches and experimental techniques.
- User experience decisions MUST prioritize learning effectiveness over unnecessary visual
  complexity.

**Rationale**: This is an educational engineering platform, not a generic AI chatbot or a
collection of tutorials.

### II. Hands-on Learning — Learning by Building

Learning MUST be based on practical experimentation and implementation.

- Each major learning module MUST include practical exercises, challenges or implementation
  tasks.
- Users MUST be encouraged to build, configure, execute and evaluate AI agents.
- Practical exercises MUST progressively increase in complexity.
- Whenever feasible, theoretical concepts MUST be accompanied by executable examples.
- Examples MUST include realistic engineering scenarios rather than isolated demonstrations.

**Rationale**: Agentic AI engineering requires practical experience with orchestration, tools,
state, memory, evaluation and failure handling.

### III. Progressive Complexity — Structured Learning Paths

The learning experience MUST follow a coherent progression from foundational concepts to
advanced architectures.

- Learning paths MUST define prerequisites and expected competencies.
- Advanced modules MUST build upon previously introduced concepts.
- The curriculum MUST cover single-agent systems before introducing complex multi-agent
  architectures.
- The platform MUST distinguish foundational, intermediate and advanced competencies.
- Users MUST be able to identify their learning progress and remaining competencies.

**Rationale**: A structured curriculum prevents fragmented learning and reduces unnecessary
cognitive overload.

### IV. Engineering Excellence — Production-Oriented Practices

The application MUST demonstrate professional software engineering practices.

- The codebase MUST follow modularity, separation of concerns and clear architectural
  boundaries.
- All critical business logic MUST be independently testable.
- Automated tests MUST cover critical functionality and regression scenarios.
- Public interfaces and integrations MUST have explicit contracts.
- Code MUST be documented where necessary to explain non-obvious architectural decisions.
- Technical debt MUST be identified and managed rather than silently accumulated.
- Architectural decisions MUST be documented when they materially affect maintainability,
  scalability or extensibility.

**Rationale**: The platform must teach engineering practices that can be transferred to
professional AI development environments.

### V. Responsible AI — Security, Privacy and Human Oversight

The platform MUST demonstrate responsible development and operation of AI agents.

- Agents MUST operate with explicitly defined permissions and capabilities.
- Tool execution MUST follow the principle of least privilege.
- Potentially destructive or irreversible actions MUST require appropriate human
  authorization.
- User secrets, credentials and API keys MUST never be exposed in client-side code or
  application logs.
- External model interactions MUST be designed with privacy and data minimization in mind.
- Agent executions MUST provide sufficient observability to understand their decisions, tool
  calls and failures.
- Educational examples MUST explicitly address hallucinations, prompt injection, excessive
  autonomy and other relevant agentic risks.

**Rationale**: Security and human oversight are fundamental engineering requirements, not
optional features.

### VI. Model and Framework Agnosticism

The platform MUST avoid unnecessary coupling to individual AI providers, models or agent
frameworks.

- Core educational concepts MUST remain independent of specific vendors.
- Provider-specific implementations MUST be isolated behind appropriate abstractions where
  practical.
- Educational material MUST clearly identify vendor-specific features and limitations.
- The architecture MUST allow new models, providers and frameworks to be introduced without
  unnecessary changes to unrelated components.
- Technology choices MUST be justified by educational value, technical suitability and
  maintenance cost.

**Rationale**: Agentic AI is an evolving ecosystem. The platform must remain adaptable as
technologies and standards change.

### VII. Measurable Learning Outcomes

The platform MUST provide evidence of learning progress.

- Each learning path MUST define explicit learning objectives.
- Exercises MUST include clear acceptance criteria.
- Progress tracking MUST reflect completed competencies rather than merely consumed content.
- Assessments MUST evaluate conceptual understanding and practical implementation.
- Practical challenges MUST provide actionable feedback.
- Learning outcomes MUST be traceable to the competencies defined by the curriculum.

**Rationale**: Completing lessons does not necessarily imply the ability to engineer reliable
agentic systems.

## Product and Quality Standards

### User Experience and Accessibility

- The interface MUST be responsive and usable across supported screen sizes.
- Navigation MUST remain consistent across learning modules.
- Accessibility MUST be considered from the beginning of development.
- The application MUST communicate errors and system states clearly.
- Learning progress MUST be understandable without requiring users to navigate multiple
  sections.

### Reliability and Performance

- Critical user workflows MUST handle errors gracefully.
- External AI service failures MUST NOT cause uncontrolled application failures.
- Long-running agent executions MUST provide appropriate execution status and feedback.
- Performance requirements MUST be defined and validated for critical workflows.
- Automated quality checks MUST be integrated into the development lifecycle.

### Educational Content Governance

- Learning content MUST be versioned and maintainable.
- Technical examples MUST be periodically reviewed for compatibility and accuracy.
- Deprecated APIs, frameworks and models MUST be explicitly identified.
- Content updates MUST preserve the consistency of learning paths and prerequisites.

## Governance

- This constitution is the highest-level source of project principles and engineering
  constraints.
- All feature specifications, technical plans and implementation tasks MUST comply with these
  principles.
- Any conflict between a proposed implementation and this constitution MUST be identified
  before implementation.
- Changes to the constitution MUST include a documented rationale.
- New principles MUST be evaluated against the project's educational objectives and long-term
  maintainability.
- The constitution MUST be reviewed whenever fundamental product or architectural objectives
  change.
- Constitution versions MUST follow Semantic Versioning:
  - MAJOR: Incompatible changes to established principles.
  - MINOR: Addition of principles or substantial governance changes.
  - PATCH: Clarifications and non-semantic corrections.

### Amendments

- **1.1.0 (2026-11-06)**, Principle I: added the exception for public orientation surfaces. Rationale:
  the platform needs a public entry point for people deciding whether to study, which can only serve
  learning indirectly. The conditions keep it honest and measurable, and keep marketing out of the
  learning environment. Features that complied with 1.0.0 still comply, hence a MINOR version.

**Version**: 1.1.0 | **Ratified**: 2026-11-06 | **Last Amended**: 2026-11-06
