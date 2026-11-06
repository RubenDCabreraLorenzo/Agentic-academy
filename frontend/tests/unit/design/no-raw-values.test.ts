/** Colors live only in tokens.css, and nothing follows the system color preference (FR-001, FR-003, SC-010). */
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const frontend = path.resolve(import.meta.dirname, "../../..");
const src = path.join(frontend, "src");

/** Temporary until T047 removes the MVP stylesheet. */
const EXCLUDED = new Set(["tokens.css", "legacy.css"]);

function walk(dir: string, extension: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return walk(full, extension);
    return name.endsWith(extension) ? [full] : [];
  });
}

const RAW_COLOR = /#[0-9a-fA-F]{3,8}\b|\b(?:rgb|hsl)a?\(|:\s*(?:white|black)\b/;

function offenders(files: string[], pattern: RegExp): string[] {
  return files.flatMap((file) =>
    readFileSync(file, "utf8")
      .split("\n")
      .flatMap((line, i) => (pattern.test(line) ? [`${path.relative(frontend, file)}:${i + 1}: ${line.trim()}`] : [])),
  );
}

const stylesheets = walk(path.join(src, "styles"), ".css").filter((f) => !EXCLUDED.has(path.basename(f)));

describe("design system discipline", () => {
  it("has stylesheets to check", () => {
    expect(stylesheets.length).toBeGreaterThan(0);
  });

  it("keeps raw colors out of stylesheets other than tokens.css", () => {
    expect(offenders(stylesheets, RAW_COLOR)).toEqual([]);
  });

  it("keeps raw colors out of components", () => {
    expect(offenders(walk(src, ".tsx"), RAW_COLOR)).toEqual([]);
  });

  it("never follows the system color preference", () => {
    const pattern = /prefers-color-scheme/;
    expect(offenders([...stylesheets, ...walk(src, ".tsx"), ...walk(src, ".ts")], pattern)).toEqual([]);
  });

  it("paints the same canvas color in index.html as the token", () => {
    const html = readFileSync(path.join(frontend, "index.html"), "utf8");
    const tokens = readFileSync(path.join(src, "styles/tokens.css"), "utf8");
    const canvas = tokens.match(/--surface-canvas:\s*(#[0-9a-fA-F]{6})/)?.[1];
    expect(canvas).toBeDefined();
    expect(html).toContain(`background:${canvas}`);
    expect(html).toContain("color-scheme:dark");
  });
});
