/** Highlighting must work without WebAssembly, which the production policy blocks (FR-054, research R4). */
import { highlight, SUPPORTED_LANGUAGES } from "../../../src/components/content/highlighter";

const SAMPLES: Record<string, string> = {
  python: 'def add(a: int, b: int) -> int:\n    """Add."""\n    return a + b  # sum\n',
  json: '{ "name": "tool", "count": 2 }\n',
  bash: 'echo "hello" | grep h\n',
  yaml: "name: tool\ncount: 2\n",
  typescript: "const total: number = 1 + 2;\n",
};

describe("highlight", () => {
  it("does not depend on WebAssembly", async () => {
    const compile = vi.spyOn(WebAssembly, "compile").mockRejectedValue(new Error("blocked by policy"));
    const instantiate = vi.spyOn(WebAssembly, "instantiate").mockRejectedValue(new Error("blocked by policy"));
    await expect(highlight(SAMPLES.python as string, "python")).resolves.toContain('class="shiki');
    expect(compile).not.toHaveBeenCalled();
    expect(instantiate).not.toHaveBeenCalled();
    vi.restoreAllMocks();
  });

  it.each(SUPPORTED_LANGUAGES)("colors %s through CSS variables only", async (language) => {
    const html = await highlight(SAMPLES[language] as string, language);
    expect(html).toContain("var(--code-");
    expect(html).not.toMatch(/color:#[0-9a-fA-F]{3,8}/);
  });

  it("falls back to plain text for an unknown language", async () => {
    const html = await highlight("anything", "cobol");
    expect(html).toContain("anything");
    expect(html).toContain('class="shiki');
  });
});
