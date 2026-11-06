/** Renders lesson Markdown with directives, highlighted code and diagrams. */
import { useMemo } from "react";
import { CodeBlock } from "./CodeBlock";
import { DeprecationNotice, MaturityCallout, VendorNote, type DeprecationInfo, type Maturity } from "./Callouts";
import { Diagram } from "./Diagram";
import { parseLesson, type Segment } from "./markdown";

function SegmentView({
  segment,
  deprecations,
}: {
  segment: Segment;
  deprecations: Record<string, DeprecationInfo>;
}) {
  switch (segment.kind) {
    case "html":
      return <div dangerouslySetInnerHTML={{ __html: segment.html }} />;
    case "code":
      return <CodeBlock code={segment.code} language={segment.language} title={segment.title} annotate={segment.annotate} />;
    case "diagram":
      return <Diagram source={segment.source} alt={segment.alt} />;
    case "directive": {
      const inner = segment.segments.map((s, i) => <SegmentView key={i} segment={s} deprecations={deprecations} />);
      if (segment.name === "maturity")
        return <MaturityCallout level={(segment.attrs.level ?? "emerging") as Maturity}>{inner}</MaturityCallout>;
      if (segment.name === "vendor") return <VendorNote name={segment.attrs.name ?? ""}>{inner}</VendorNote>;
      if (segment.name === "deprecated") {
        const ref = segment.attrs.ref ?? "";
        const info = deprecations[ref];
        return info ? <DeprecationNotice deprecation={info} subject={ref} /> : null;
      }
      return <div>{inner}</div>;
    }
  }
}

export function Markdown({
  source,
  deprecations = {},
}: {
  source: string;
  deprecations?: Record<string, DeprecationInfo>;
}) {
  const segments = useMemo(() => parseLesson(source), [source]);
  return (
    <div className="markdown">
      {segments.map((s, i) => (
        <SegmentView key={i} segment={s} deprecations={deprecations} />
      ))}
    </div>
  );
}

export function InlineMarkdown({ source }: { source: string }) {
  const segments = useMemo(() => parseLesson(source), [source]);
  return (
    <>
      {segments.map((s, i) => (
        <SegmentView key={i} segment={s} deprecations={{}} />
      ))}
    </>
  );
}
