/** Contrast of every required token pairing (design tokens contract, SC-003). */
import { readFileSync } from "node:fs";
import path from "node:path";

const css = readFileSync(path.resolve(import.meta.dirname, "../../../src/styles/tokens.css"), "utf8");

function token(name: string): string {
  const match = css.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})\\s*;`));
  if (!match?.[1]) throw new Error(`token --${name} is missing or is not a hex color`);
  return match[1];
}

function luminance(hex: string): number {
  const channel = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

const SURFACES = ["surface-canvas", "surface-1", "surface-2", "surface-3"];
const CODE_SURFACES = ["surface-1", "surface-2", "surface-3"];
const TEXT = ["text-primary", "text-muted", "accent", "accent-secondary", "success", "warning", "danger"];
const SYNTAX = ["foreground", "comment", "keyword", "string", "function", "constant", "parameter", "punctuation"].map((n) => `syntax-${n}`);

const pairs: [string, string, number][] = [
  ...TEXT.flatMap((t) => SURFACES.map((s): [string, string, number] => [t, s, 4.5])),
  ...SYNTAX.flatMap((t) => CODE_SURFACES.map((s): [string, string, number] => [t, s, 4.5])),
  ...["accent", "accent-hover", "accent-pressed"].map((s): [string, string, number] => ["on-accent", s, 4.5]),
  ...["danger", "danger-hover", "danger-pressed"].map((s): [string, string, number] => ["on-danger", s, 4.5]),
  ["syntax-foreground", "syntax-selection", 4.5],
  ...["border-control", "focus-ring"].flatMap((t) => SURFACES.map((s): [string, string, number] => [t, s, 3])),
];

describe("token contrast", () => {
  it.each(pairs)("%s on %s reaches %f:1", (foreground, background, minimum) => {
    expect(contrast(token(foreground), token(background))).toBeGreaterThanOrEqual(minimum);
  });
});
