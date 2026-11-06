/** Public catalog and roadmap (US6; FR-001, FR-002). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { get } from "../../api/client";
import { ErrorState, Loading } from "../../components/states";
import type { Level, PathSummary } from "./types";

const LEVELS: Level[] = ["foundational", "intermediate", "advanced"];

function PathCard({ path, titles }: { path: PathSummary; titles: Record<string, string> }) {
  const { t } = useTranslation();
  const planned = path.status === "planned";
  return (
    <li className="card stack" style={{ listStyle: "none" }}>
      <p className="row" style={{ margin: 0 }}>
        <span className="muted">{t("catalog.roadmapStep", { order: path.order })}</span>
        <span className={planned ? "badge" : "badge success"}>{planned ? t("catalog.planned") : t("catalog.available")}</span>
      </p>
      <h3 style={{ margin: 0 }}>
        <Link to={`/paths/${path.id}`}>{path.title}</Link>
      </h3>
      <p style={{ margin: 0 }}>{path.summary}</p>
      <p className="muted" style={{ margin: 0 }}>
        {t("catalog.estimatedHours", { count: path.estimated_hours })}
      </p>
      <div>
        <strong>{t("catalog.prerequisites")}: </strong>
        {path.prerequisite_paths.length
          ? path.prerequisite_paths.map((p) => titles[p] ?? p).join(", ")
          : t("catalog.noPrerequisites")}
      </div>
      <div>
        <strong>{t("catalog.competencies")}: </strong>
        {path.competencies.map((c) => c.title).join(", ")}
      </div>
      <Link className={planned ? "btn secondary" : "btn"} to={`/paths/${path.id}`} aria-label={`${planned ? t("catalog.inspect") : t("catalog.start")}: ${path.title}`}>
        {planned ? t("catalog.inspect") : t("catalog.start")}
      </Link>
    </li>
  );
}

export default function CatalogPage() {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["catalog"], queryFn: () => get<PathSummary[]>("/catalog") });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const titles = Object.fromEntries(q.data.map((p) => [p.id, p.title]));
  return (
    <section className="stack">
      <h1>{t("catalog.title")}</h1>
      <p className="reading">{t("catalog.intro")}</p>
      {LEVELS.map((level) => {
        const paths = q.data.filter((p) => p.level === level);
        if (!paths.length) return null;
        return (
          <section key={level} aria-labelledby={`level-${level}`}>
            <h2 id={`level-${level}`}>{t(`catalog.level.${level}`)}</h2>
            <ul className="grid" style={{ padding: 0 }}>
              {paths.map((p) => (
                <PathCard key={p.id} path={p} titles={titles} />
              ))}
            </ul>
          </section>
        );
      })}
    </section>
  );
}
