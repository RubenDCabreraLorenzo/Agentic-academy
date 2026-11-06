/** Public catalog and roadmap (US6; FR-001, FR-002). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { get } from "../../api/client";
import { ErrorState, Loading } from "../../components/states";
import { Badge } from "../../components/ui/Badge";
import { LinkButton } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { Level, PathSummary } from "./types";

const LEVELS: Level[] = ["foundational", "intermediate", "advanced"];

function PathCard({ path, titles }: { path: PathSummary; titles: Record<string, string> }) {
  const { t } = useTranslation();
  const planned = path.status === "planned";
  return (
    <Card as="li" className="stack">
      <p className="row">
        <span className="muted">{t("catalog.roadmapStep", { order: path.order })}</span>
        <Badge tone={planned ? undefined : "success"}>{planned ? t("catalog.planned") : t("catalog.available")}</Badge>
      </p>
      <h3>
        <Link to={`/paths/${path.id}`}>{path.title}</Link>
      </h3>
      <p>{path.summary}</p>
      <p className="muted">{t("catalog.estimatedHours", { count: path.estimated_hours })}</p>
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
      <LinkButton variant={planned ? "secondary" : "primary"} to={`/paths/${path.id}`} aria-label={`${planned ? t("catalog.inspect") : t("catalog.start")}: ${path.title}`}>
        {planned ? t("catalog.inspect") : t("catalog.start")}
      </LinkButton>
    </Card>
  );
}

export default function CatalogPage() {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["catalog"], queryFn: () => get<PathSummary[]>("/catalog") });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const titles = Object.fromEntries(q.data.map((p) => [p.id, p.title]));
  return (
    <section className="stack-lg">
      <div className="stack">
        <h1>{t("catalog.title")}</h1>
        <p className="measure">{t("catalog.intro")}</p>
      </div>
      {LEVELS.map((level) => {
        const paths = q.data.filter((p) => p.level === level);
        if (!paths.length) return null;
        return (
          <section key={level} aria-labelledby={`level-${level}`} className="stack">
            <h2 id={`level-${level}`}>{t(`catalog.level.${level}`)}</h2>
            <ul className="grid plain-list">
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
