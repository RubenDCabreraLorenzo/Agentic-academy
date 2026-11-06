/** Showcases show real published content, and fail here when it changes (FR-017, R-15). */
import { readFileSync } from "node:fs";
import path from "node:path";
import marketing from "../../../src/i18n/en/marketing.json";

const root = path.resolve(import.meta.dirname, "../../../..");
const read = (file: string) => readFileSync(path.join(root, file), "utf8").replace(/\r\n/g, "\n");

interface Excerpt {
  sources: string[];
  quoted: Record<string, string | string[]>;
}

const excerpts = (marketing as unknown as { excerpts: Record<string, Excerpt> }).excerpts;

describe.each(Object.entries(excerpts))("the %s excerpt", (_name, excerpt) => {
  it("names its sources, none of them a reference solution", () => {
    expect(excerpt.sources.length).toBeGreaterThan(0);
    for (const source of excerpt.sources) {
      expect(source.startsWith("content/")).toBe(true);
      expect(source).not.toContain("solution/");
    }
  });

  it("quotes only text found in those sources", () => {
    const text = excerpt.sources.map(read).join("\n");
    const quoted = Object.values(excerpt.quoted).flat();
    expect(quoted.length).toBeGreaterThan(0);
    expect(quoted.filter((q) => !text.includes(q))).toEqual([]);
  });
});

it("has both showcases", () => {
  expect(Object.keys(excerpts).sort()).toEqual(["challenge", "lab"]);
});
