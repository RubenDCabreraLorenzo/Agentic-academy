/**
 * Two simultaneous renders with one identifier left diagrams on their placeholder forever, on 10 of 25
 * loads under the development server, with no error. A cancelled effect must not start a render.
 * Repeated loads are covered end to end in premium/us3-lesson-links.spec.ts.
 */
import { render, screen } from "@testing-library/react";
import { Diagram } from "../../../src/components/content/Diagram";
import "../../../src/i18n";

const mermaid = vi.hoisted(() => ({ initialize: vi.fn(), render: vi.fn() }));
vi.mock("mermaid", () => ({ default: mermaid }));

describe("Diagram", () => {
  beforeEach(() => vi.clearAllMocks());

  it("does not render after it has been removed", async () => {
    const { unmount } = render(<Diagram source="graph TD; A-->B" alt="A leads to B" />);
    unmount();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(mermaid.render).not.toHaveBeenCalled();
  });

  it("shows the source when rendering fails", async () => {
    mermaid.render.mockRejectedValueOnce(new Error("bad diagram"));
    render(<Diagram source="not a diagram" alt="Broken" />);
    expect(await screen.findByText("not a diagram")).toBeInTheDocument();
  });
});
