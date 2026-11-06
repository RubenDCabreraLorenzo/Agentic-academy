/**
 * Multi-file code editor (CodeMirror 6) with keyboard-accessible file tabs. Its theme takes every value
 * from tokens, so that it follows the product theme. The editable element carries the accessible name:
 * a prop on the outer component would only reach its wrapper.
 */
import { python } from "@codemirror/lang-python";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";
import CodeMirror from "@uiw/react-codemirror";
import { useId, useMemo, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";

const editorTheme = EditorView.theme(
  {
    "&": { backgroundColor: "var(--surface-2)", color: "var(--syntax-foreground)", fontSize: "var(--text-code)" },
    "&.cm-focused": { outline: "2px solid var(--focus-ring)", outlineOffset: "2px" },
    ".cm-content": { fontFamily: "var(--font-mono)", caretColor: "var(--text-primary)" },
    ".cm-scroller": { fontFamily: "var(--font-mono)", lineHeight: "var(--leading-ui)" },
    ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--text-primary)" },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": {
      backgroundColor: "var(--syntax-selection)",
    },
    ".cm-activeLine": { backgroundColor: "var(--surface-3)" },
    ".cm-gutters": { backgroundColor: "var(--surface-1)", color: "var(--text-muted)", borderRight: "1px solid var(--border-subtle)" },
    ".cm-activeLineGutter": { backgroundColor: "var(--surface-3)", color: "var(--text-primary)" },
    ".cm-matchingBracket, &.cm-focused .cm-matchingBracket": { backgroundColor: "var(--syntax-selection)", color: "var(--syntax-foreground)" },
    ".cm-nonmatchingBracket": { color: "var(--danger)" },
  },
  { dark: true },
);

const syntax = syntaxHighlighting(
  HighlightStyle.define([
    { tag: tags.comment, color: "var(--syntax-comment)" },
    { tag: [tags.keyword, tags.modifier, tags.controlKeyword, tags.operatorKeyword, tags.definitionKeyword], color: "var(--syntax-keyword)" },
    { tag: [tags.string, tags.special(tags.string), tags.regexp], color: "var(--syntax-string)" },
    { tag: [tags.function(tags.variableName), tags.function(tags.propertyName), tags.definition(tags.function(tags.variableName))], color: "var(--syntax-function)" },
    { tag: [tags.number, tags.bool, tags.null, tags.atom, tags.self, tags.constant(tags.name)], color: "var(--syntax-constant)" },
    { tag: [tags.className, tags.typeName, tags.namespace], color: "var(--syntax-parameter)" },
    { tag: [tags.punctuation, tags.operator, tags.bracket], color: "var(--syntax-punctuation)" },
    { tag: [tags.name, tags.variableName, tags.propertyName], color: "var(--syntax-foreground)" },
  ]),
);

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
  const { t } = useTranslation();
  const id = useId();
  const names = Object.keys(files);
  const extensions = useMemo(
    () => [python(), editorTheme, syntax, EditorView.contentAttributes.of({ "aria-label": `${active} — ${label}`, tabindex: "0" })],
    [active, label],
  );
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
      <div role="tablist" aria-label={label} className="tabs-list">
        {names.map((name, i) => (
          <button
            key={name}
            id={`${id}-tab-${name}`}
            role="tab"
            type="button"
            aria-selected={name === active}
            aria-controls={`${id}-panel`}
            tabIndex={name === active ? 0 : -1}
            className="tab"
            onClick={() => onSelect(name)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {name}
            {readOnlyFiles.includes(name) ? ` ${t("challenge.readOnly")}` : ""}
          </button>
        ))}
      </div>
      <div id={`${id}-panel`} role="tabpanel" aria-labelledby={`${id}-tab-${active}`} className="editor-panel">
        <CodeMirror
          value={files[active] ?? ""}
          height="360px"
          theme="none"
          extensions={extensions}
          readOnly={readOnlyFiles.includes(active)}
          onChange={(value) => onChange(active, value)}
          basicSetup={{ lineNumbers: true, foldGutter: false, tabSize: 4 }}
        />
      </div>
    </div>
  );
}
