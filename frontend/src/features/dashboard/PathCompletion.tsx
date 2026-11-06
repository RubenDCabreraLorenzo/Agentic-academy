/** Path completion summary (FR-042). */
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { Alert } from "../../components/ui/Alert";
import type { Dashboard } from "./types";

export function PathCompletion({
  summary,
  pathTitle,
}: {
  summary: NonNullable<Dashboard["completion_summary"]>;
  pathTitle: string;
}) {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="completion">
      <Alert tone="success">
        <div className="stack">
          <h2 id="completion">{t("dashboard.completedTitle", { path: pathTitle })}</h2>
          <p>{t("dashboard.completedBody")}</p>
          <ul>
            {summary.competencies.map((c) => (
              <li key={c.id}>
                {c.title}{" "}
                <span className="muted">
                  ({c.evidence.map((e) => t(`dashboard.evidence.${e.type}`, { version: e.version })).join(", ")})
                </span>
              </li>
            ))}
          </ul>
          {summary.recommended_next_path && (
            <p>
              {t("dashboard.recommendedNext")}{" "}
              <Link to={`/paths/${summary.recommended_next_path.id}`}>{summary.recommended_next_path.title}</Link>
            </p>
          )}
        </div>
      </Alert>
    </section>
  );
}
