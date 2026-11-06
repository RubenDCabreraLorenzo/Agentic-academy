/** Mermaid diagram rendered client-side; the alt text is the accessible name and caption (FR-014). */
import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

export function Diagram({ source, alt }: { source: string; alt: string }) {
  const { t } = useTranslation();
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    import("mermaid")
      .then(async ({ default: mermaid }) => {
        const dark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "default" });
        const { svg: out } = await mermaid.render(`mmd${id}`, source);
        if (!cancelled) setSvg(out);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [id, source]);

  return (
    <figure className="diagram">
      {svg ? (
        // Mermaid runs with securityLevel "strict" on maintainer-authored, reviewed content.
        <div role="img" aria-label={alt} dangerouslySetInnerHTML={{ __html: svg }} />
      ) : failed ? (
        <pre aria-label={alt}>{source}</pre>
      ) : (
        <div role="img" aria-label={alt} className="muted">
          {t("content.diagram")}…
        </div>
      )}
      <figcaption>{alt}</figcaption>
    </figure>
  );
}
