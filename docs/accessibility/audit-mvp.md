# Accessibility audit — MVP (WCAG 2.2 AA)

**Date**: 2026-11-06 · **Status**: automated checks complete; **manual audit pending** (requires a
person with keyboard-only and screen-reader testing).

## Automated (axe-core via Playwright, tags wcag2a/2aa/21aa/22aa)

Every end-to-end scenario asserts **zero critical violations** at desktop width and at 360 px:
catalog, path overview, module page, knowledge check (results view), dashboard, challenge page and
laboratory. Result on 2026-11-06: 0 critical violations on all pages.

## Built-in measures

- Skip link, landmark structure, one `h1` per page, focus moved to headings on view changes.
- All controls are native buttons, links, inputs or selects with accessible names; ordering
  questions use move-up/move-down buttons instead of drag and drop; editor file tabs follow the
  ARIA tabs pattern with arrow-key navigation.
- Diagrams expose their text alternative as the accessible name and as a visible caption (FR-014).
- Live regions announce answer feedback, run status and laboratory step position.
- Colors are defined as tokens with light and dark variants; visible focus outline on all controls.
- No horizontal page scroll at 360 px (asserted in e2e); code and traces scroll inside their region.

## Manual audit checklist (pending)

- [ ] Keyboard-only walkthrough of quickstart V1–V7 (including the CodeMirror editor: Esc then Tab to leave).
- [ ] NVDA + Firefox and VoiceOver + Safari on catalog, module, knowledge check, challenge, lab, dashboard.
- [ ] Contrast check of light and dark themes, including Shiki and Mermaid output.
- [ ] 200% zoom and text-spacing overrides.
- [ ] Record serious/moderate axe findings and fixes here.
