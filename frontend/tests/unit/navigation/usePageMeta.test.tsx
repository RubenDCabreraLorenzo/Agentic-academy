/** Document title and description (FR-042; routes contract, navigation protocol). */
import { render } from "@testing-library/react";
import { usePageMeta } from "../../../src/app/navigation/usePageMeta";
import "../../../src/i18n";

function Page({ title, description }: { title: string; description?: string }) {
  usePageMeta({ title, description });
  return null;
}

describe("usePageMeta", () => {
  afterEach(() => {
    document.head.querySelector('meta[name="description"]')?.remove();
  });

  it("sets the document title with the product name", () => {
    render(<Page title="Curriculum" />);
    expect(document.title).toBe("Curriculum · Agentic Academy");
  });

  it("updates when the title changes", () => {
    const { rerender } = render(<Page title="One" />);
    rerender(<Page title="Two" />);
    expect(document.title).toBe("Two · Agentic Academy");
  });

  it("creates and then updates the description", () => {
    const { rerender } = render(<Page title="One" description="First" />);
    expect(document.head.querySelector('meta[name="description"]')).toHaveAttribute("content", "First");
    rerender(<Page title="One" description="Second" />);
    expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(1);
    expect(document.head.querySelector('meta[name="description"]')).toHaveAttribute("content", "Second");
  });
});
