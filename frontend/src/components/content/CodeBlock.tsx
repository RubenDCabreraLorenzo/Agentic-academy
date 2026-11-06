/** Highlighted code with language label, copy action and annotations (FR-009, FR-054). */
import { useEffect, useId, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../ui/Button";
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
    import("./highlighter")
      .then(({ highlight }) => highlight(clean, language))
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
        <Button variant="ghost" onClick={copy} aria-live="polite">
          {copied ? t("content.copied") : t("content.copy")}
        </Button>
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
        <ol className="code-notes">
          {notes.map((n) => (
            <li key={n.line}>
              <strong>{t("content.line", { n: n.line })}</strong> {n.text}
            </li>
          ))}
        </ol>
      )}
    </figure>
  );
}
