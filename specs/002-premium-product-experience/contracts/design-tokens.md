# Contract: Design tokens and styling rules

**Consumers**: every screen and shared component. **Requirements**: FR-001–FR-011, FR-047–FR-049, SC-003, SC-010.
Initial values come from the [spec](../spec.md#design-token-contract). Decisions: [research](../research.md) R1, R3–R7.

## Stylesheet structure

Plain CSS in `frontend/src/styles/`, ordered by cascade layers declared once in `index.css`:

```css
@layer reset, tokens, base, layout, components, content, screens;
```

| File | Layer | Holds | May contain raw color values |
|------|-------|-------|------------------------------|
| `tokens.css` | `tokens` | All custom properties below | **Yes, only here** |
| `reset.css`, `base.css` | `reset`, `base` | Elements, typography, focus, reduced motion, forced colors | No |
| `layout.css` | `layout` | Shells, page grids, reading column | No |
| `components.css` | `components` | Shared components | No |
| `content.css` | `content` | Lesson rendering, code, diagrams, callouts | No |
| `screens.css` | `screens` | Layout that belongs to one screen; no new visual values | No |

## Token names

Names are stable. Values may be refined, but only with the contrast test passing.

**Color** (values in the spec unless listed here): `--surface-canvas`, `--surface-1`, `--surface-2`, `--surface-3`, `--text-primary`, `--text-muted`,
`--accent`, `--on-accent`, `--accent-secondary`, `--border-subtle`, `--border-control`, `--focus-ring`, `--success`, `--warning`, `--danger`, `--on-danger`.

**Syntax** (new; used by lesson code, the editor and showcases, always on `--surface-1`, `--surface-2` or `--surface-3`):

| Token | Value | Lowest measured contrast (on `--surface-3`) |
|-------|-------|---------------------------------------------|
| `--syntax-foreground` | `#EDEFF3` | 12.51 |
| `--syntax-comment` | `#9AA5B4` | 5.77 |
| `--syntax-keyword` | `#C4B1FF` | 7.60 |
| `--syntax-string` | `#7EE0A8` | 9.00 |
| `--syntax-function` | `#8FB4FF` | 6.96 |
| `--syntax-constant` | `#F2C14E` | 8.58 |
| `--syntax-parameter` | `#F0A87C` | 7.27 |
| `--syntax-punctuation` | `#B4BBC6` | 7.45 |
| `--syntax-selection` | `#2D3A55` | Background only; `--syntax-foreground` must keep 4.5:1 on it |

Each surface of the code highlighter is mapped from these through its own prefix (`--code-token-*`), so that only `tokens.css` holds values.

**Type**: `--font-sans`, `--font-mono`; `--text-display`, `--text-page`, `--text-section`, `--text-subsection`, `--text-prose`, `--text-ui`, `--text-small`, `--text-code`; `--leading-tight`, `--leading-prose`, `--leading-ui`.

**Space**: `--space-1` (4 px) through `--space-9` (96 px), following the spec's scale. **Radius**: `--radius-control`, `--radius-surface`, `--radius-full`.

**Elevation**: `--shadow-overlay`. **Motion**: `--motion-fast` (120 ms), `--motion-base` (200 ms). **Layout**: `--layout-max` (1200 px), `--measure-prose` (70ch), `--header-offset` (scroll offset of fixed elements).

## Required pairings

The contrast test (see below) MUST cover at least these:

| Foreground | Backgrounds | Minimum |
|------------|-------------|---------|
| `--text-primary`, `--text-muted`, `--accent`, `--accent-secondary`, `--success`, `--warning`, `--danger`, all `--syntax-*` text | Every `--surface-*` they may sit on | 4.5:1 |
| `--on-accent` | `--accent` | 4.5:1 |
| `--on-danger` | `--danger` | 4.5:1 |
| `--border-control`, `--focus-ring` | Every `--surface-*` | 3:1 |
| `--focus-ring` | `--accent`, `--danger` | Not required, because rule 3 applies |

## Rules

1. Screens and components MUST NOT use raw color values outside `tokens.css`, and MUST NOT use inline `style` attributes, except a value computed from data, passed as a custom property (for example `--progress` on the progress indicator).
2. `--border-subtle` MUST NOT be the only boundary of a control or the only sign of a state.
3. The focus indicator is `outline: 2px solid var(--focus-ring)` with a 2 px offset, so that a gap of the surrounding surface separates it from filled controls. It MUST NOT be removed.
4. `--accent` means interactive. `--accent-secondary` is for laboratory and showcase highlights, and is never a status or the only link style.
5. Status colors are never the only signal (FR-049).
6. Gradients and decorative effects are allowed only in `.public-hero` and `.public-showcase` (FR-010), never behind body text, code or forms.
7. Motion uses only `--motion-*`, and only on `transform`, `opacity` and color properties. Under `prefers-reduced-motion: reduce`, durations become 0 and `scroll-behavior` is `auto`.
8. Under `forced-colors: active`, focus, boundaries and statuses stay visible, using system colors where borders would otherwise vanish.
9. No rule may depend on `prefers-color-scheme`. The dark identity is unconditional (FR-003). `index.html` sets `color-scheme: dark` and the canvas color before stylesheets load.

## Typography

| Family | Package | File used | Size |
|--------|---------|-----------|------|
| Geist Variable (`--font-sans`) | `@fontsource-variable/geist` (OFL-1.1) | Latin, weight axis, normal | 29.4 KB |
| Geist Variable, italic | Same | Latin, weight axis, italic; loaded only when used | 31.0 KB |
| Geist Mono Variable (`--font-mono`) | `@fontsource-variable/geist-mono` (OFL-1.1) | Latin, weight axis, normal | 23.1 KB |

- `@font-face` rules are written in `tokens.css` and point to the package files, so that the build serves them from the application origin.
- `font-display: swap`, with system fallbacks and metric overrides on the fallback to limit layout shift.
- The final choice is confirmed in visual review (spec "Typography"). Changing family only changes these rules.

## Automated checks

| Check | Fails when | Tool |
|-------|-----------|------|
| Contrast of required pairings | Any pair falls under its minimum | Unit test reading `tokens.css` |
| Raw values | A color value appears outside `tokens.css`; a `prefers-color-scheme` rule appears anywhere | Unit test scanning `src/styles` and `src/**/*.tsx` |
| Inline styles | A JSX `style` attribute appears outside the allow-list | Lint rule (`no-restricted-syntax`) |
| Canvas in `index.html` | The head color differs from `--surface-canvas` | Unit test |
