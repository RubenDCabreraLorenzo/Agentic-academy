/** Shared components: names, states and keyboard behavior (UI components contract). */
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { MemoryRouter } from "react-router";
import { Alert } from "../../../src/components/ui/Alert";
import { Breadcrumb } from "../../../src/components/ui/Breadcrumb";
import { Button, LinkButton } from "../../../src/components/ui/Button";
import { ConfirmDialog } from "../../../src/components/ui/ConfirmDialog";
import { Field } from "../../../src/components/ui/Field";
import { ProgressBar } from "../../../src/components/ui/ProgressBar";
import { Tabs } from "../../../src/components/ui/Tabs";
import "../../../src/i18n";

beforeAll(() => {
  // jsdom does not implement the modal dialog methods.
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute("open");
  };
});

describe("Button", () => {
  it("is a native button that defaults to type button, with its variant", () => {
    render(<Button variant="danger">Delete</Button>);
    const button = screen.getByRole("button", { name: "Delete" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveClass("btn", "btn-danger");
  });

  it("LinkButton is a real link", () => {
    render(
      <MemoryRouter>
        <LinkButton to="/x" variant="secondary">
          Go
        </LinkButton>
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Go" })).toHaveAttribute("href", "/x");
  });
});

describe("Field", () => {
  it("names the input with its label and links hint and error", () => {
    render(<Field label="Email" hint="Your work address" error="Required" name="email" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Your work address Required");
  });

  it("is not invalid without an error", () => {
    render(<Field label="Email" name="email" />);
    expect(screen.getByLabelText("Email")).not.toHaveAttribute("aria-invalid");
  });
});

describe("Alert", () => {
  it("passes the role and shows its content with a decorative icon", () => {
    render(
      <Alert tone="danger" role="alert">
        Failed
      </Alert>,
    );
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Failed");
    expect(alert.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });
});

describe("ProgressBar", () => {
  it("exposes its name, value and text equivalent", () => {
    render(<ProgressBar label="Competencies" value={3} max={10} valueText="3 of 10" />);
    const bar = screen.getByRole("progressbar", { name: "Competencies" });
    expect(bar).toHaveAttribute("aria-valuenow", "3");
    expect(bar).toHaveAttribute("aria-valuemax", "10");
    expect(bar).toHaveAttribute("aria-valuetext", "3 of 10");
  });

  it("does not divide by zero", () => {
    render(<ProgressBar label="Empty" value={0} max={0} />);
    expect(screen.getByRole("progressbar", { name: "Empty" })).toBeInTheDocument();
  });
});

describe("Tabs", () => {
  function Example() {
    const [active, setActive] = useState("a");
    return (
      <Tabs label="Files" tabs={[{ id: "a", label: "a.py" }, { id: "b", label: "b.py" }, { id: "c", label: "c.py" }]} active={active} onSelect={setActive}>
        <p>Panel {active}</p>
      </Tabs>
    );
  }

  it("uses arrow keys, wraps around and keeps one tab stop", async () => {
    const user = userEvent.setup();
    render(<Example />);
    const first = screen.getByRole("tab", { name: "a.py" });
    expect(first).toHaveAttribute("aria-selected", "true");
    expect(first).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "b.py" })).toHaveAttribute("tabindex", "-1");

    first.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "b.py" })).toHaveFocus();
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Panel b");

    await user.keyboard("{ArrowLeft}{ArrowLeft}");
    expect(screen.getByRole("tab", { name: "c.py" })).toHaveFocus();
  });
});

describe("ConfirmDialog", () => {
  function Example({ typed }: { typed?: string }) {
    const [open, setOpen] = useState(false);
    const [done, setDone] = useState(false);
    return (
      <>
        <button type="button" onClick={() => setOpen(true)}>
          Open
        </button>
        {done && <p>Confirmed</p>}
        <ConfirmDialog
          open={open}
          title="Delete everything?"
          confirmLabel="Delete"
          cancelLabel="Cancel"
          tone="danger"
          typedConfirmation={typed ? { label: `Type ${typed}`, value: typed } : undefined}
          onConfirm={() => {
            setDone(true);
            setOpen(false);
          }}
          onCancel={() => setOpen(false)}
        >
          <p>This cannot be undone.</p>
        </ConfirmDialog>
      </>
    );
  }

  it("is an alertdialog named by its title and described by its body", async () => {
    render(<Example />);
    await userEvent.click(screen.getByRole("button", { name: "Open" }));
    const dialog = screen.getByRole("alertdialog", { name: "Delete everything?" });
    expect(dialog).toHaveAccessibleDescription("This cannot be undone.");
  });

  it("cancels on Escape and returns focus to the opener", async () => {
    const user = userEvent.setup();
    render(<Example />);
    const opener = screen.getByRole("button", { name: "Open" });
    await user.click(opener);
    fireEvent(screen.getByRole("alertdialog"), new Event("cancel", { cancelable: true }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
    expect(screen.queryByText("Confirmed")).not.toBeInTheDocument();
  });

  it("keeps the action disabled until the typed confirmation matches", async () => {
    const user = userEvent.setup();
    render(<Example typed="RESET" />);
    await user.click(screen.getByRole("button", { name: "Open" }));
    const action = screen.getByRole("button", { name: "Delete" });
    expect(action).toBeDisabled();
    await user.type(screen.getByLabelText("Type RESET"), "RESE");
    expect(action).toBeDisabled();
    await user.type(screen.getByLabelText("Type RESET"), "T");
    expect(action).toBeEnabled();
    await user.click(action);
    expect(screen.getByText("Confirmed")).toBeInTheDocument();
  });
});

describe("Breadcrumb", () => {
  it("is a named navigation with an ordered list", () => {
    render(
      <MemoryRouter>
        <Breadcrumb items={[{ label: "Foundations", to: "/paths/a" }, { label: "Lesson" }]} />
      </MemoryRouter>,
    );
    const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(nav.querySelector("ol")).not.toBeNull();
    expect(screen.getByRole("link", { name: "Foundations" })).toHaveAttribute("href", "/paths/a");
    expect(screen.getByText("Lesson")).toHaveAttribute("aria-current", "page");
  });
});
