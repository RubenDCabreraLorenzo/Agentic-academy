/** Single-screen learning dashboard (US3; FR-038, FR-040, FR-042). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { get } from "../../api/client";
import { ErrorState, Loading } from "../../components/states";
import { LinkButton } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ProgressBar } from "../../components/ui/ProgressBar";
import { formatPercent } from "../../i18n";
import { ModuleStatusBadge } from "../module/ModuleStatus";
import { PathCompletion } from "./PathCompletion";
import { ResetPathDialog } from "./ResetPathDialog";
import type { Dashboard } from "./types";

function nextHref(step: NonNullable<Dashboard["next_step"]>): string {
  switch (step.kind) {
    case "lesson": {
      const [module, anchor] = step.target_id.split("#");
      return `/modules/${module}#${anchor}`;
    }
    case "knowledge_check":
      return `/knowledge-checks/${step.target_id}`;
    case "challenge":
      return `/challenges/${step.target_id}`;
    case "next_path":
      return `/paths/${step.target_id}`;
  }
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["dashboard"], queryFn: () => get<Dashboard>("/me/dashboard") });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const d = q.data;
  if (!d.active_path) {
    return (
      <section className="stack">
        <h1>{t("dashboard.title")}</h1>
        <p>{t("dashboard.noPaths")}</p>
      </section>
    );
  }
  const ratio = d.competencies_total ? d.competencies_demonstrated / d.competencies_total : 0;
  const progressText = t("dashboard.competencies", { done: d.competencies_demonstrated, total: d.competencies_total });
  return (
    <section className="stack-lg">
      <h1>{t("dashboard.title")}</h1>
      {d.new_learner && (
        <Card className="stack">
          <h2>{t("dashboard.welcomeTitle")}</h2>
          <p className="measure">{t("dashboard.welcomeBody")}</p>
          <p className="row">
            <LinkButton to={`/paths/${d.active_path.id}`}>{t("dashboard.start", { path: d.active_path.title })}</LinkButton>
            <Link to="/curriculum">{t("dashboard.exploreCurriculum")}</Link>
          </p>
        </Card>
      )}
      <div className="grid">
        <Card as="section" className="stack" aria-labelledby="active-path">
          <h2 id="active-path">{t("dashboard.activePath")}</h2>
          <p>
            <Link to={`/paths/${d.active_path.id}`}>{d.active_path.title}</Link>
          </p>
          <div className="stack">
            <div className="row row-between">
              <span>{progressText}</span>
              <span>{formatPercent(ratio)}</span>
            </div>
            <ProgressBar label={t("dashboard.progressLabel")} value={d.competencies_demonstrated} max={d.competencies_total} valueText={progressText} />
          </div>
          <Link to={`/dashboard/competencies?path=${d.active_path.id}`}>{t("dashboard.viewCompetencies")}</Link>
        </Card>

        <Card as="section" className="stack" aria-labelledby="next">
          <h2 id="next">{t("dashboard.nextStep")}</h2>
          {d.next_step ? (
            <div className="stack">
              <p className="muted">{t(`dashboard.stepKind.${d.next_step.kind}`)}:</p>
              <LinkButton to={nextHref(d.next_step)}>{d.next_step.label}</LinkButton>
            </div>
          ) : (
            <p>{t("dashboard.allDone")}</p>
          )}
          {d.continue && (
            <p>
              <Link to={`/modules/${d.continue.module_id}${d.continue.lesson_id ? `#lesson-${d.continue.lesson_id}` : ""}`}>{t("dashboard.continue")}</Link>
            </p>
          )}
        </Card>
      </div>

      {d.path_completed && d.completion_summary && <PathCompletion summary={d.completion_summary} pathTitle={d.active_path.title} />}

      <section aria-labelledby="modules" className="stack">
        <h2 id="modules">{t("dashboard.modules")}</h2>
        <ol className="module-list">
          {d.modules.map((m) => (
            <li key={m.id}>
              <span className="row">
                <Link to={`/modules/${m.id}`}>{m.title}</Link> <ModuleStatusBadge status={m.status} />
              </span>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="pending" className="stack">
        <h2 id="pending">{t("dashboard.pendingObjectives")}</h2>
        {d.pending_objectives.length === 0 ? (
          <p className="muted">{t("dashboard.noPending")}</p>
        ) : (
          <ul className="measure">
            {d.pending_objectives.map((o) => (
              <li key={`${o.module_id}-${o.id}`}>
                {o.statement} <span className="muted">— {o.module_title}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ResetPathDialog pathId={d.active_path.id} pathTitle={d.active_path.title} />
    </section>
  );
}
