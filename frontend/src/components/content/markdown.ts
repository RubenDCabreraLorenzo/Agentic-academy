/**
 * Lesson Markdown → segments (contracts/content-schema.md "Lesson Markdown directives").
 * Plain Markdown is rendered with markdown-it and sanitized with DOMPurify; fenced code, Mermaid
 * diagrams and ::: directives become dedicated components.
 */
import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";

export type Segment =
  | { kind: "html"; html: string }
  | { kind: "code"; language: string; title?: string; annotate: boolean; code: string }
  | { kind: "diagram"; source: string; alt: string }
  | { kind: "directive"; name: string; attrs: Record<string, string>; segments: Segment[] };

const ATTR = /(\w+)="([^"]*)"/g;
const ANCHOR = /\s*\{#([a-z0-9]+(?:-[a-z0-9]+)*)\}\s*$/;

function attrs(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of text.matchAll(ATTR)) out[m[1] as string] = m[2] as string;
  return out;
}

const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

// Heading anchors: "## Title {#anchor}" → <h2 id="anchor">Title</h2> (feedback links, FR-018).
md.core.ruler.push("heading_anchors", (state) => {
  const tokens = state.tokens;
  for (let i = 0; i < tokens.length; i++) {
    const open = tokens[i];
    const inline = tokens[i + 1];
    if (open?.type !== "heading_open" || !inline) continue;
    const m = ANCHOR.exec(inline.content);
    if (!m) continue;
    open.attrSet("id", m[1] as string);
    inline.content = inline.content.replace(ANCHOR, "");
    const last = inline.children?.[inline.children.length - 1];
    if (last && last.type === "text") last.content = last.content.replace(ANCHOR, "");
  }
});

// External links open safely.
const defaultLinkOpen = md.renderer.rules.link_open ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options));
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const href = tokens[idx]?.attrGet("href") ?? "";
  if (/^https?:\/\//.test(href)) {
    tokens[idx]?.attrSet("rel", "noopener noreferrer");
    tokens[idx]?.attrSet("target", "_blank");
  }
  return defaultLinkOpen(tokens, idx, options, env, self);
};

export function renderInline(markdown: string): string {
  return DOMPurify.sanitize(md.renderInline(markdown), { ADD_ATTR: ["target"] });
}

export function renderHtml(markdown: string): string {
  return DOMPurify.sanitize(md.render(markdown), { ADD_ATTR: ["target"] });
}

function splitFences(text: string): Segment[] {
  const out: Segment[] = [];
  const lines = text.split("\n");
  let buffer: string[] = [];
  const flush = () => {
    const chunk = buffer.join("\n");
    if (chunk.trim()) out.push({ kind: "html", html: renderHtml(chunk) });
    buffer = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] as string;
    const fence = /^```(.*)$/.exec(line);
    if (!fence) {
      buffer.push(line);
      continue;
    }
    flush();
    const info = (fence[1] ?? "").trim();
    const body: string[] = [];
    i++;
    while (i < lines.length && !/^```\s*$/.test(lines[i] as string)) body.push(lines[i++] as string);
    const language = info.split(/\s+/, 1)[0] ?? "";
    const a = attrs(info);
    if (language === "mermaid") out.push({ kind: "diagram", source: body.join("\n"), alt: a.alt ?? "" });
    else
      out.push({
        kind: "code",
        language: language || "text",
        title: a.title,
        annotate: /\bannotate\b/.test(info),
        code: body.join("\n"),
      });
  }
  flush();
  return out;
}

export function parseLesson(markdown: string): Segment[] {
  const out: Segment[] = [];
  const lines = markdown.split("\n");
  let buffer: string[] = [];
  const flush = () => {
    out.push(...splitFences(buffer.join("\n")));
    buffer = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] as string;
    const open = /^:::(\w+)(?:\{(.*)\})?\s*$/.exec(line.trim());
    if (!open) {
      buffer.push(line);
      continue;
    }
    flush();
    const name = open[1] as string;
    const a = attrs(open[2] ?? "");
    const inner: string[] = [];
    // Inline-only directives (no closing marker), e.g. :::deprecated{ref="x"}
    if (name === "deprecated") {
      out.push({ kind: "directive", name, attrs: a, segments: [] });
      continue;
    }
    i++;
    while (i < lines.length && (lines[i] as string).trim() !== ":::") inner.push(lines[i++] as string);
    out.push({ kind: "directive", name, attrs: a, segments: splitFences(inner.join("\n")) });
  }
  flush();
  return out;
}

/** Lines ending with a "# note: …" comment become numbered annotations below the code. */
export function extractAnnotations(code: string): { code: string; notes: { line: number; text: string }[] } {
  const notes: { line: number; text: string }[] = [];
  const cleaned = code.split("\n").map((line, index) => {
    const m = /^(.*?)\s*#\s*note:\s*(.+)$/.exec(line);
    if (!m) return line;
    notes.push({ line: index + 1, text: m[2] as string });
    return m[1] as string;
  });
  return { code: cleaned.join("\n"), notes };
}
