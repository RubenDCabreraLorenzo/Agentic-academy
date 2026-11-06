# ADR 0001: Modular monolith backend

**Status**: Accepted · **Date**: 2026-11-06

## Context

The MVP needs auth, content, assessments, challenges, lab and progress with clear boundaries (Constitution IV) but has a small team and modest scale (research R10).

## Decision

A single FastAPI application (`backend/src/academy`) split into domain modules. Each module owns its models, services and router; modules interact only through service functions, never through each other's tables. Only the runner is a separate deployable unit (ADR 0005).

## Consequences

Simple deployment and transactions; boundaries must be enforced by review and package structure. Alternatives rejected: microservices (operational cost without need).
