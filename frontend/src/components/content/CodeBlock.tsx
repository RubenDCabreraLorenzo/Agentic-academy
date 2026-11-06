/** Highlighted code with language label, copy action and annotations (FR-009). */
import { useEffect, useId, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { extractAnnotations } from "./markdownParser";

const LANG_NAMES: Record<string, string> = { python: "Python", json: "JSON", bash: "Bash", text: "Text", yaml: "YAML", typescript: "TypeScript" };

export function CodeBlock({
  code,
  language,
  title,
  annotate = false,
}: {
  code: string;
  language: string;
  title?: string;
  annotate?: boolean;
}) {
  const { t } = useTranslation();
  const labelId = useId();
  const { code: clean, notes } = useMemo(
    () => (annotate ? extractAnnotations(code) : { code, notes: [] }),
    [code, annotate],
  );
  const [html, setHtml] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    import("shiki")
      .then(({ codeToHtml }) =>
        codeToHtml(clean, {
          lang: language in LANG_NAMES ? language : "text",
          themes: { light: "github-light", dark: "github-dark" },
          defaultColor: false,
        }),
      )
      .then((out) => !cancelled && setHtml(out))
      .catch(() => !cancelled && setHtml(null));
    return () => {
      cancelled = true;
    };
  }, [clean, language]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(clean);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  const name = LANG_NAMES[language] ?? language;
  return (
    <figure className="code-block" aria-labelledby={labelId}>
      <header>
        <span id={labelId}>{title ? `${title} · ${name}` : t("content.codeLabel", { language: name })}</span>
        <button type="button" className="linklike" onClick={copy} aria-live="polite">
          {copied ? t("content.copied") : t("content.copy")}
        </button>
      </header>
      <div className="code-scroll" tabIndex={0} role="region" aria-labelledby={labelId}>
        {html ? (
          // Shiki output is generated locally from escaped code; it contains no learner HTML.
          <div dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <pre>
            <code>{clean}</code>
          </pre>
        )}
      </div>
      {notes.length > 0 && (
        <ol className="muted" style={{ margin: 0, padding: "8px 12px 8px 32px", fontSize: "0.9rem" }}>
          {notes.map((n) => (
            <li key={n.line}>
              <strong>Line {n.line}:</strong> {n.text}
            </li>
          ))}
        </ol>
      )}
    </figure>
  );
}
