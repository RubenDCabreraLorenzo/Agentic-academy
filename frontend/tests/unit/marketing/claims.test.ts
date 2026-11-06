/**
 * Public copy against the claim register (FR-015, SC-006). This only assists: reading every sentence
 * against the register, in quickstart P2, remains the gate.
 */
import common from "../../../src/i18n/en/common.json";
import marketing from "../../../src/i18n/en/marketing.json";

const FORBIDDEN: [string, RegExp][] = [
  ["certification", /certif/i],
  ["accreditation", /accredit/i],
  ["testimonial", /testimonial/i],
  ["free", /\bfree\b/i],
  ["price", /\bpric(e|es|ing)\b/i],
  ["currency", /[$€](?!\{)/],
  ["guarantee", /guarantee/i],
  ["video", /\bvideos?\b/i],
  ["AI tutor", /\bai tutor/i],
  ["expert review", /expert[- ]reviewed/i],
  ["trust", /trusted by/i],
  ["tamper-proof", /tamper/i],
  ["compliance", /wcag|compliant/i],
  ["percentage", /\d+\s*%/],
  ["count of people", /\d[\d,.]*\+?\s+(users|learners|students|customers|engineers|developers|companies|teams)\b/i],
];

/** Sections of the shared strings that anyone can read without an account. */
const PUBLIC_KEYS = ["app", "meta", "ui", "legal", "states", "auth", "content", "catalog", "path"] as const;

/**
 * Terms that are not claims in these exact places. Each entry needs a reason.
 * "auth.errors.*" entries would go here, for instance, if a message ever used a listed word.
 */
const ALLOWED: { path: string; term: string; reason: string }[] = [];

function strings(value: unknown, path: string): { path: string; text: string }[] {
  if (typeof value === "string") return [{ path, text: value }];
  if (Array.isArray(value)) return value.flatMap((v, i) => strings(v, `${path}[${i}]`));
  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([k, v]) => strings(v, path ? `${path}.${k}` : k));
  }
  return [];
}

const scanned = [
  ...strings(marketing, "marketing"),
  ...PUBLIC_KEYS.flatMap((key) => strings((common as Record<string, unknown>)[key], key)),
];

describe("public copy", () => {
  it("has strings to scan", () => {
    expect(scanned.length).toBeGreaterThan(50);
  });

  it("detects a forbidden term", () => {
    const matches = (text: string) => FORBIDDEN.filter(([, pattern]) => pattern.test(text)).map(([term]) => term);
    expect(matches("Free for 10,000 developers, 99% certified")).toEqual(["certification", "free", "percentage", "count of people"]);
    expect(matches("Study, check your understanding and build code.")).toEqual([]);
    expect(matches("About {{count}} hours")).toEqual([]);
  });

  it("uses no forbidden term", () => {
    const found = scanned.flatMap(({ path, text }) =>
      FORBIDDEN.filter(([term, pattern]) => pattern.test(text) && !ALLOWED.some((a) => a.path === path && a.term === term)).map(
        ([term]) => `${path} (${term}): ${text}`,
      ),
    );
    expect(found).toEqual([]);
  });

  it("states that the laboratory replays recordings and calls no model", () => {
    const text = (marketing as unknown as { lab: { disclosure: string } }).lab.disclosure;
    expect(text).toMatch(/replay/i);
    expect(text).toMatch(/recording/i);
    expect(text).toMatch(/no language model is called/i);
  });
});
