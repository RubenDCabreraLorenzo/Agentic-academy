# ADR 0005: gVisor runner, trust boundaries and accepted risks

**Status**: Accepted · **Date**: 2026-11-06

## Context

Learner code must run with no network, no secrets and no access to other learners' data (FR-022a, NFR-006, SC-011).

## Decision

A separate runner executes each job in a fresh gVisor (`runsc`) container with strict limits (runner protocol §3–§4). The runner database role has no table privileges and may only call hardened `SECURITY DEFINER` functions (claim, fenced complete, heartbeat). Trust zones: browser (untrusted), API host, PostgreSQL, runner host (trusted but exposed), sandbox (untrusted) — runner protocol §0.

Accepted decisions (architecture review, 2026-11-06):
- **D1**: learner code shares the process with the test harness and can write `/out/result.json`, so a determined learner can fake a pass *for their own submission*. Validation (exact test-id set, regular file ≤ 1 MB, exit status) is an integrity check, **not** tamper-proof evaluation. Accepted while no certificates exist; revisit before introducing any.
- **D2**: no hidden tests in the MVP; all tests are visible; reference solutions are used only by the content validator and never mounted in learner runs.

## Consequences

Strong isolation at moderate cost; gVisor is not a VM (limitations in runner protocol §8). Upgrade path: microVMs.
