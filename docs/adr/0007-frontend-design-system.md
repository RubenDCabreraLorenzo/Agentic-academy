# ADR 0007: Frontend design system and code highlighting

**Status**: Accepted · **Date**: 2026-11-06

## Context

Spec 002 turns the MVP into a premium product with a dark visual identity, without changing the backend or adding a UI framework without a concrete need (FR-011). The MVP used one stylesheet, 64 inline style declarations, and themes tied to the operating system. Measurements also showed that code highlighting failed silently under the production security policy: `script-src 'self'` blocks compiling WebAssembly, so 0 of 3 code blocks were highlighted. The development server applies no such policy, which hid it.

## Decision

- **Styling**: plain CSS with custom properties and cascade layers. No build-time CSS tool, because it would add a second vocabulary and make token discipline harder to check.
- **Components**: a small set of our own over native elements (`dialog`, `button`, form controls). No component library: the platform covers focus trapping, Escape and semantics for what we need.
- **Fonts**: Geist and Geist Mono, self-hosted from `@fontsource-variable` packages (OFL-1.1), because the policy has `font-src 'self'` and the laboratory must make no external requests.
- **Theme**: dark only, as decided by the product owner. There is no `prefers-color-scheme` rule. Token names are semantic, so a light theme can be added later.
- **Code highlighting**: Shiki's JavaScript regex engine with a CSS-variable theme and only the languages we support.

## Alternatives rejected

- **Adding `'wasm-unsafe-eval'` to the policy**: it fixes highlighting, but weakens a security control to solve a styling concern.
- **Highlighting at content build**: the build is Python, and lessons stay as Markdown (Spec 001 R2).

## Consequences

- The security policy and `nginx.conf` stay unchanged. The JavaScript engine gave output identical to WebAssembly on all 11 code blocks published at the time; the comparison must be repeated if lessons add other languages.
- `tokens.css` is the only place with color values, enforced by tests and lint.
- Development results are not valid evidence for production behavior, so a test runs against the real nginx image (`csp.spec.ts`).
- Geist's wide zero means `ch` is misleading: `--measure-prose` is 50ch, and must be measured again if the family changes (Spec 002 research R20).
- Evidence: [Spec 002 research](../../specs/002-premium-product-experience/research.md), R1–R4, R7.
