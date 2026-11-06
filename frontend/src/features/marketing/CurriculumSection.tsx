import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { ErrorState, Loading } from "../../components/states";
import { Badge } from "../../components/ui/Badge";
import { LinkButton } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useCatalog } from "./queries";

export function CurriculumSection() {
  const { t } = useTranslation("marketing");
  const { t: tc } = useTranslation();
  const q = useCatalog();
  const paths = [...(q.data ?? [])].sort((a, b) => a.order - b.order);

  return (
    <section aria-labelledby="landing-curriculum" className="landing-section landing-section-raised">
      <div className="landing-inner stack-lg">
        <div className="stack">
          <h2 id="landing-curriculum">{t("curriculum.title")}</h2>
          <p className="measure muted">{t("curriculum.intro")}</p>
        </div>
        {q.isLoading ? (
          <Loading />
        ) : q.isError || !q.data ? (
          <div className="stack">
            <ErrorState onRetry={() => q.refetch()} />
            <p>
              <Link to="/curriculum">{t("actions.explore")}</Link>
            </p>
          </div>
        ) : (
          <>
            <ol className="plain-list curriculum-list">
              {paths.map((path) => {
                const planned = path.status === "planned";
                return (
                  <Card as="li" key={path.id} className="curriculum-row">
                    <span className="curriculum-step muted">{tc("catalog.roadmapStep", { order: path.order })}</span>
                    <h3>
                      <Link to={`/paths/${path.id}`}>{path.title}</Link>
                    </h3>
                    <p className="row curriculum-meta">
                      <Badge tone={planned ? undefined : "success"}>{tc(planned ? "catalog.planned" : "catalog.available")}</Badge>
                      <span>{tc(`catalog.level.${path.level}`)}</span>
                      <span>{tc("catalog.estimatedHours", { count: path.estimated_hours })}</span>
                      <span>{t("curriculum.competencyCount", { count: path.competencies.length })}</span>
                    </p>
                  </Card>
                );
              })}
            </ol>
            <p>
              <LinkButton variant="secondary" to="/curriculum">
                {t("actions.explore")}
              </LinkButton>
            </p>
          </>
        )}
      </div>
    </section>
  );
}
