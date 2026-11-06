/** Multi-file code editor (CodeMirror 6) with keyboard-accessible file tabs. */
import { python } from "@codemirror/lang-python";
import CodeMirror from "@uiw/react-codemirror";
import { useId, type KeyboardEvent } from "react";

export function Editor({
  files,
  active,
  onSelect,
  onChange,
  readOnlyFiles = [],
  label,
}: {
  files: Record<string, string>;
  active: string;
  onSelect: (name: string) => void;
  onChange: (name: string, value: string) => void;
  readOnlyFiles?: string[];
  label: string;
}) {
  const id = useId();
  const names = Object.keys(files);
  const onKey = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const next = names[(index + (e.key === "ArrowRight" ? 1 : names.length - 1)) % names.length];
    if (next) {
      onSelect(next);
      document.getElementById(`${id}-tab-${next}`)?.focus();
    }
  };
  return (
    <div className="editor">
      <div role="tablist" aria-label={label} className="row">
        {names.map((name, i) => (
          <button
            key={name}
            id={`${id}-tab-${name}`}
            role="tab"
            type="button"
            aria-selected={name === active}
            aria-controls={`${id}-panel`}
            tabIndex={name === active ? 0 : -1}
            className={name === active ? "btn" : "btn secondary"}
            onClick={() => onSelect(name)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {name}
            {readOnlyFiles.includes(name) ? " (read-only)" : ""}
          </button>
        ))}
      </div>
      <div id={`${id}-panel`} role="tabpanel" aria-labelledby={`${id}-tab-${active}`} style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
        <CodeMirror
          value={files[active] ?? ""}
          height="360px"
          extensions={[python()]}
          readOnly={readOnlyFiles.includes(active)}
          onChange={(value) => onChange(active, value)}
          basicSetup={{ lineNumbers: true, foldGutter: false, tabSize: 4 }}
          aria-label={`${active} — ${label}`}
        />
      </div>
    </div>
  );
}
