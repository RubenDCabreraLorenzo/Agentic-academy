/** Single-screen learning dashboard (US3; FR-038, FR-040, FR-042). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { get } from "../../api/client";
import { ErrorState, Loading } from "../../components/states";
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
  return (
    <section className="stack">
      <h1>{t("dashboard.title")}</h1>
      {d.new_learner && (
        <div className="card stack">
          <h2 style={{ marginTop: 0 }}>{t("dashboard.welcomeTitle")}</h2>
          <p>{t("dashboard.welcomeBody")}</p>
          <p>
            <Link className="btn" to={`/paths/${d.active_path.id}`}>
              {t("dashboard.start", { path: d.active_path.title })}
            </Link>{" "}
            <Link to="/">{t("dashboard.exploreCurriculum")}</Link>
          </p>
        </div>
      )}
      <div className="grid">
        <section className="card stack" aria-labelledby="active-path">
          <h2 id="active-path" style={{ marginTop: 0 }}>
            {t("dashboard.activePath")}
          </h2>
          <p style={{ margin: 0 }}>
            <Link to={`/paths/${d.active_path.id}`}>{d.active_path.title}</Link>
          </p>
          <div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>{t("dashboard.competencies", { done: d.competencies_demonstrated, total: d.competencies_total })}</span>
              <span>{formatPercent(ratio)}</span>
            </div>
            <div
              className="progress-bar"
              role="progressbar"
              aria-label={t("dashboard.progressLabel")}
              aria-valuemin={0}
              aria-valuemax={d.competencies_total}
              aria-valuenow={d.competencies_demonstrated}
            >
              <span style={{ width: `${Math.round(ratio * 100)}%` }} />
            </div>
          </div>
          <Link to={`/dashboard/competencies?path=${d.active_path.id}`}>{t("dashboard.viewCompetencies")}</Link>
        </section>

        <section className="card stack" aria-labelledby="next">
          <h2 id="next" style={{ marginTop: 0 }}>
            {t("dashboard.nextStep")}
          </h2>
          {d.next_step ? (
            <p style={{ margin: 0 }}>
              <span className="muted">{t(`dashboard.stepKind.${d.next_step.kind}`)}: </span>
              <Link className="btn" to={nextHref(d.next_step)}>
                {d.next_step.label}
              </Link>
            </p>
          ) : (
            <p>{t("dashboard.allDone")}</p>
          )}
          {d.continue && (
            <p style={{ margin: 0 }}>
              <Link
                to={`/modules/${d.continue.module_id}${d.continue.lesson_id ? `#lesson-${d.continue.lesson_id}` : ""}`}
              >
                {t("dashboard.continue")}
              </Link>
            </p>
          )}
        </section>
      </div>

      {d.path_completed && d.completion_summary && <PathCompletion summary={d.completion_summary} pathTitle={d.active_path.title} />}

      <section aria-labelledby="modules">
        <h2 id="modules">{t("dashboard.modules")}</h2>
        <ol className="module-list">
          {d.modules.map((m) => (
            <li key={m.id}>
              <Link to={`/modules/${m.id}`}>{m.title}</Link> <ModuleStatusBadge status={m.status} />
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="pending">
        <h2 id="pending">{t("dashboard.pendingObjectives")}</h2>
        {d.pending_objectives.length === 0 ? (
          <p className="muted">{t("dashboard.noPending")}</p>
        ) : (
          <ul>
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
