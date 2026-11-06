/**
 * SC-012: what `/` transfers on first load, compressed, must not exceed 300 KB, and it must not load the
 * editor, diagram, highlighter or Markdown code. Builds with a manifest into a separate folder, then walks
 * only static imports from the entry and the landing page: anything imported dynamically loads later.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, rmSync } from "node:fs";
import path from "node:path";
import { gzipSync } from "node:zlib";

const LIMIT_KB = 300;
const OUT = "dist-size";
const ENTRY = "index.html";
const LANDING = "src/features/marketing/LandingPage.tsx";
const FORBIDDEN = /codemirror|mermaid|shiki|lezer|Markdown|highlighter|Diagram|Editor/i;
// Variable fonts: the browser fetches only the subsets a page uses, and the landing page is Latin text.
const FONTS = /^geist(-mono)?-latin-wght-normal.*\.woff2$/;

const frontend = path.resolve(import.meta.dirname, "..");
const vite = path.join(frontend, "node_modules/vite/bin/vite.js");
execFileSync(process.execPath, [vite, "build", "--manifest", "--outDir", OUT, "--emptyOutDir", "--logLevel", "warn"], {
  cwd: frontend,
  stdio: "inherit",
});

const dist = path.join(frontend, OUT);
const manifest = JSON.parse(readFileSync(path.join(dist, ".vite/manifest.json"), "utf8"));

const seen = new Set();
const files = new Set();
function walk(key) {
  if (seen.has(key)) return;
  seen.add(key);
  const chunk = manifest[key];
  if (!chunk) throw new Error(`Not in the manifest: ${key}`);
  files.add(chunk.file);
  (chunk.css ?? []).forEach((f) => files.add(f));
  (chunk.imports ?? []).forEach(walk);
}
walk(ENTRY);
walk(LANDING);

const heavy = [...seen, ...files].filter((name) => FORBIDDEN.test(name));
const gzipped = (file) => gzipSync(readFileSync(path.join(dist, file))).length;
const code = [...files].map((file) => [file, gzipped(file)]);
const fonts = readdirSync(path.join(dist, "assets"))
  .filter((name) => FONTS.test(name))
  .map((name) => [`assets/${name}`, readFileSync(path.join(dist, "assets", name)).length]);

const rows = [[ENTRY, gzipped(ENTRY)], ...code, ...fonts];
const total = rows.reduce((sum, [, size]) => sum + size, 0);
for (const [file, size] of rows) console.log(`${(size / 1024).toFixed(1).padStart(8)} KB  ${file}`);
console.log(`${(total / 1024).toFixed(1).padStart(8)} KB  total (limit ${LIMIT_KB} KB)`);
rmSync(dist, { recursive: true, force: true });

let failed = false;
if (fonts.length !== 2) {
  console.error(`Expected the two Latin font files, found ${fonts.length}.`);
  failed = true;
}
if (heavy.length) {
  console.error(`The landing page loads heavy code: ${heavy.join(", ")}`);
  failed = true;
}
if (total > LIMIT_KB * 1024) {
  console.error(`The landing page is over the limit.`);
  failed = true;
}
process.exit(failed ? 1 : 0);
