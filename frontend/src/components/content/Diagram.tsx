/**
 * Mermaid diagram rendered client-side; the alt text is the accessible name and caption (FR-014).
 * Mermaid calculates derived colors, so it receives resolved token values rather than var() references.
 */
import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

function themeVariables() {
  const styles = getComputedStyle(document.documentElement);
  const token = (name: string) => styles.getPropertyValue(`--${name}`).trim();
  const text = token("text-primary");
  const raised = token("surface-3");
  const surface = token("surface-2");
  const border = token("border-control");
  const line = token("text-muted");
  return {
    background: surface,
    primaryColor: raised,
    primaryTextColor: text,
    primaryBorderColor: border,
    lineColor: line,
    secondaryColor: surface,
    secondaryTextColor: text,
    secondaryBorderColor: border,
    tertiaryColor: token("surface-1"),
    tertiaryTextColor: text,
    tertiaryBorderColor: border,
    textColor: text,
    titleColor: text,
    nodeTextColor: text,
    edgeLabelBackground: surface,
    clusterBkg: token("surface-1"),
    clusterBorder: border,
    noteBkgColor: raised,
    noteTextColor: text,
    noteBorderColor: border,
    actorBkg: raised,
    actorTextColor: text,
    actorBorder: border,
    signalColor: line,
    signalTextColor: text,
    labelTextColor: text,
    loopTextColor: text,
    fontFamily: styles.fontFamily,
  };
}

export function Diagram({ source, alt }: { source: string; alt: string }) {
  const { t } = useTranslation();
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    import("mermaid")
      .then(async ({ default: mermaid }) => {
        // Never start a render for a cancelled effect: two at once with one identifier can both hang.
        if (cancelled) return;
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "base", themeVariables: themeVariables() });
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
