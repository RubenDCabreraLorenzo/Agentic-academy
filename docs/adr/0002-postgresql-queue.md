# ADR 0002: PostgreSQL as the submission queue

**Status**: Accepted · **Date**: 2026-11-06

## Context

Challenge submissions must be queued for the runner with retries, leases and visibility of queue position (runner protocol §1).

## Decision

Use a `submission_job` table claimed with `FOR UPDATE SKIP LOCKED` through `SECURITY DEFINER` functions; no Redis or broker.

## Consequences

One fewer service; adequate for ≤ 10 simultaneous submissions. Revisit only if queue throughput becomes a measured bottleneck.
