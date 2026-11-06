# Contract: Educational content files

**Consumers**: content CLI (`academy content validate|build`), backend content loader.
**Producers**: content maintainers (via pull requests). Entities: [data-model.md §1](../data-model.md).

## Layout

```text
content/
├── competencies.yaml                      # all competencies (language-independent ids)
└── en/                                    # one folder per language (FR-055)
    ├── paths/
    │   └── <path-id>/
    │       ├── path.yaml
    │       └── modules/
    │           └── <NN>-<module-id>/
    │               ├── module.yaml
    │               ├── lessons/<NN>-<lesson-id>.md
    │               ├── knowledge-check.yaml
    │               └── challenges/<challenge-id>/
    │                   ├── challenge.yaml
    │                   ├── starter/…            # learner-editable files
    │                   ├── tests/…              # all visible to the learner in the MVP (no hidden tests, review D2)
    │                   └── solution/…           # validator only; never shipped, never mounted in learner runs
    ├── lab/<scenario-id>.json                 # conforms to lab-trace.schema.json
    └── deprecations.yaml
```

## Common header (every YAML file and lesson front matter)

```yaml
id: tools-and-function-calling        # kebab-case, stable, language-independent
version: 1.2.0                        # SemVer
lang: en
last_reviewed: 2026-11-06
deprecation:                          # optional
  reason: "API replaced by …"
  replacement: "…"
  since: 2026-10-01
```

## Lesson Markdown directives

| Directive | Purpose | Requirement |
|-----------|---------|-------------|
| `:::maturity{level="established\|emerging\|experimental"}` … `:::` | Labels a technique | FR-010 |
| `:::vendor{name="…"}` … `:::` | Vendor-specific note incl. limitations | FR-011 |
| `:::deprecated{ref="…"}` | Inline deprecation notice | FR-049 |
| ` ```python title="…" annotate ` | Code example with optional annotations | FR-009 |
| ` ```mermaid alt="…" ` or `![alt](img.svg)` | Diagram; `alt` mandatory | FR-014 |
| `{#anchor-id}` after a heading | Anchor for feedback links | FR-018 |

## Validation rules enforced by `academy content validate` (FR-050)

A build fails (non-zero exit, machine-readable report) when any rule is violated:

1. Every file matches its schema; ids are unique per type; versions are SemVer; `lang` matches folder.
2. Every referenced id (competency, module, path, objective, lesson anchor, test, scenario) exists.
3. Prerequisite graphs are acyclic and prerequisites precede dependants in path order.
4. Modules flagged `multi_agent: true` come after all single-agent modules (FR-005).
5. Every module has ≥ 1 objective, ≥ 1 lesson, ≥ 1 code example, ≥ 1 diagram with alt text,
   ≥ 1 reference, exactly 1 knowledge check (≥ 5 questions) and ≥ 1 challenge (FR-007, FR-008, FR-016).
6. Every question and every challenge criterion maps to an objective/competency (FR-044), and every
   module competency is covered by at least one of the module's challenges, so a knowledge check
   alone can never demonstrate a competency (FR-036).
7. Challenge `difficulty_rank` strictly increases along the path (FR-025); ≥ 2 hints (FR-021);
   every test id belongs to exactly one criterion; the reference solution (kept under
   `solution/`) passes all tests in the sandbox image; the starter code fails at
   least one mandatory criterion.
8. Lab scenarios validate against `lab-trace.schema.json`; every destructive tool call has an
   `approval_request` and both approved/rejected branches; every recording has `recorded_with`;
   decision summaries are labeled `educational_explanation` (FR-027a, FR-030, FR-033a).
9. A version bump is required whenever a file's content changes relative to the previous bundle.
10. No secrets: files are scanned for credential patterns (FR-047).

## Bundle output

`academy content build --lang en` writes:

- `dist/content/en/bundle-<bundle_version>.json` — validated content with Markdown bodies
  (rendered, highlighted and sanitized in the frontend, research R2), challenge tests and starter
  files. Mounted read-only on the API host and on the runner host. Reference solutions are never
  included.

Every published bundle is kept (immutable) so older attempts and submissions can be scored against
their own version (data-model §1.9).
