# ADR 0004: First-party accounts with server sessions

**Status**: Accepted · **Date**: 2026-11-06

## Context

Accounts are required (FR-045) and learner data must stay minimal and private (NFR-007).

## Decision

Email + password with Argon2id, opaque server-side session tokens stored hashed, `HttpOnly; Secure; SameSite=Lax` cookies, double-submit CSRF token, single-use hashed tokens for verification and reset, rate limiting. Email through an `EmailSender` port. Initial policy values approved in review D4.

## Consequences

No identity vendor; we own password security. SPA and API share one origin (reverse proxy / Vite proxy).
