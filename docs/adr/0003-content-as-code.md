# ADR 0003: Educational content as code

**Status**: Accepted · **Date**: 2026-11-06

## Context

Content must be versioned, reviewed and validated (FR-048–FR-051, NFR-009) without an authoring UI (out of scope).

## Decision

Content lives in `content/` as Markdown, YAML and JSON. `academy content validate` enforces content-schema rules in CI; `academy content build` writes immutable, versioned bundles that are never overwritten. Publish = merge.

## Consequences

Git history is the audit trail; maintainers need Git. Every published bundle is retained so results stay bound to their version.
