/** Side-by-side comparison of two executions (FR-029). */
import { useTranslation } from "react-i18next";
import { compare, effectiveElements, type Scenario } from "./player";

export function CompareView({
  scenario,
  comparison,
}: {
  scenario: Scenario;
  comparison: NonNullable<Scenario["comparisons"]>[number];
}) {
  const { t } = useTranslation();
  const sides = compare(scenario, comparison.left_variant, comparison.right_variant);
  return (
    <section aria-labelledby="compare" className="stack">
      <h2 id="compare">{t("lab.compareTitle")}</h2>
      {comparison.explanation && <p className="reading">{comparison.explanation}</p>}
      <div className="grid">
        {sides.map((side) => (
          <div key={side.variant.id} className="card stack" aria-label={side.variant.label}>
            <h3 style={{ margin: 0 }}>{side.variant.label}</h3>
            <dl className="compare-stats">
              <dt>{t("lab.elements")}</dt>
              <dd>{side.elementCount}</dd>
              <dt>{t("lab.toolCalls")}</dt>
              <dd>{side.toolCallCount}</dd>
              <dt>{t("lab.outcome")}</dt>
              <dd>{side.outcome}</dd>
            </dl>
            <ol className="lab-trace compact">
              {effectiveElements(scenario, side.variant)
                .filter((e) => e.kind !== "decision_summary")
                .map((e) => (
                  <li key={e.id} className={side.uniqueIds.has(e.id) ? "unique" : undefined}>
                    {side.uniqueIds.has(e.id) && <span className="sr-only">{t("lab.onlyHere")}: </span>}
                    {e.kind === "tool_call" ? `${e.tool}()` : e.kind === "execution_event" ? e.event : t(`lab.kind.${e.kind}`)}
                  </li>
                ))}
            </ol>
            <p className="muted" style={{ margin: 0 }}>{t("lab.uniqueLegend", { count: side.uniqueIds.size })}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
