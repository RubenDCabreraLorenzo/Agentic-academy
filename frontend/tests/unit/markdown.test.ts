import { extractAnnotations, parseLesson, renderHtml } from "../../src/components/content/markdownParser";

describe("parseLesson", () => {
  const source = [
    "## Tokens {#tokens}",
    "",
    "Text with [a link](https://example.com).",
    "",
    ':::maturity{level="established"}',
    "Inside callout.",
    ":::",
    "",
    '```python title="x.py"',
    "print('hi')",
    "```",
    "",
    '```mermaid alt="A diagram"',
    "flowchart LR",
    "```",
  ].join("\n");

  it("splits markdown, directives, code and diagrams", () => {
    const segments = parseLesson(source);
    expect(segments.map((s) => s.kind)).toEqual(["html", "directive", "code", "diagram"]);
    const html = segments[0];
    expect(html?.kind === "html" && html.html).toContain('<h2 id="tokens">Tokens</h2>');
    expect(html?.kind === "html" && html.html).toContain('rel="noopener noreferrer"');
    const directive = segments[1];
    expect(directive?.kind === "directive" && directive.attrs.level).toBe("established");
    const code = segments[2];
    expect(code?.kind === "code" && code.title).toBe("x.py");
    const diagram = segments[3];
    expect(diagram?.kind === "diagram" && diagram.alt).toBe("A diagram");
  });

  it("sanitizes raw HTML", () => {
    expect(renderHtml('<img src=x onerror="alert(1)">hello')).not.toContain("<img");
  });
});

describe("extractAnnotations", () => {
  it("turns note comments into numbered annotations", () => {
    const { code, notes } = extractAnnotations("a = 1  # note: first\nb = 2");
    expect(code).toBe("a = 1\nb = 2");
    expect(notes).toEqual([{ line: 1, text: "first" }]);
  });
});
