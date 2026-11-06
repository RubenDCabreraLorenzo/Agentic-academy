# ADR 0006: Laboratory replays recorded traces

**Status**: Accepted · **Date**: 2026-11-06

## Context

The laboratory must explain agent behavior without runtime model calls (FR-033) and without exposing private model reasoning (FR-027a).

## Decision

Scenarios are JSON documents validated by `lab-trace.schema.json` with four element kinds; decision summaries are authored and reviewed by maintainers. The frontend replays them client-side.

## Consequences

Deterministic, zero runtime cost, vendor-neutral; recordings need periodic review (`recorded_with`, `last_reviewed`).
