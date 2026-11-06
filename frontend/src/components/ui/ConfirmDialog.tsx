/**
 * Modal confirmation on the native dialog element: focus moves in, Escape cancels, and focus returns
 * to the opener. A typed confirmation keeps the action disabled until it matches exactly.
 */
import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Button, type ButtonVariant } from "./Button";
import { Field } from "./Field";

export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  cancelLabel,
  tone = "primary",
  typedConfirmation,
  error,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  tone?: Extract<ButtonVariant, "primary" | "danger">;
  typedConfirmation?: { label: string; value: string } | undefined;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);
  const initialFocusRef = useRef<HTMLDivElement>(null);
  const [typed, setTyped] = useState("");
  const id = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      openerRef.current = document.activeElement as HTMLElement | null;
      setTyped("");
      dialog.showModal();
      initialFocusRef.current?.querySelector<HTMLElement>("input, button")?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
      openerRef.current?.focus?.();
    }
  }, [open]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (typedConfirmation && typed !== typedConfirmation.value) return;
    onConfirm();
  };

  return (
    <dialog
      ref={dialogRef}
      className="dialog"
      role="alertdialog"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-body`}
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
    >
      {open && (
        <form className="stack" onSubmit={submit}>
          <h2 id={`${id}-title`}>{title}</h2>
          <div id={`${id}-body`} className="stack">
            {children}
          </div>
          {error && (
            <p role="alert" className="field-error">
              {error}
            </p>
          )}
          <div ref={initialFocusRef} className="stack">
            {typedConfirmation && (
              <Field label={typedConfirmation.label} type="text" autoComplete="off" value={typed} onChange={(e) => setTyped(e.target.value)} />
            )}
            <div className="row">
              <Button variant={tone} type="submit" disabled={!!typedConfirmation && typed !== typedConfirmation.value}>
                {confirmLabel}
              </Button>
              <Button variant="secondary" onClick={onCancel}>
                {cancelLabel}
              </Button>
            </div>
          </div>
        </form>
      )}
    </dialog>
  );
}
