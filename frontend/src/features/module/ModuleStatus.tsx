/** Module status and practice entry points (FR-037; increment-1 label from /health). */
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useHealth } from "../../app/session";
import type { ModuleDetail } from "../catalog/types";

export function ModuleStatusBadge({ status }: { status: ModuleDetail["status"] }) {
  const { t } = useTranslation();
  const cls = status === "completed" ? "badge success" : status === "in_progress" ? "badge warning" : "badge";
  return <span className={cls}>{t(`path.moduleStatus.${status}`)}</span>;
}

export function PracticeSection({ module }: { module: ModuleDetail }) {
  const { t } = useTranslation();
  const health = useHealth();
  const challengesEnabled = health.data?.challenges_enabled ?? false;
  return (
    <section aria-labelledby="practice" className="card stack">
      <h2 id="practice" style={{ marginTop: 0 }}>
        {t("module.practice")}
      </h2>
      <div className="row">
        <ModuleStatusBadge status={module.status} />
        {module.status !== "completed" && !challengesEnabled && module.challenges.length > 0 && (
          <span className="muted">{t("module.challengeLater")}</span>
        )}
      </div>
      {module.knowledge_check_id && (
        <div>
          <h3>{t("module.knowledgeCheck")}</h3>
          <Link className="btn" to={`/knowledge-checks/${module.knowledge_check_id}`}>
            {t("module.startCheck")}
          </Link>
          {module.objectives_demonstrated && <p className="muted">{t("check.competencyPending")}</p>}
        </div>
      )}
      {module.challenges.length > 0 && (
        <div>
          <h3>{t("module.challenge")}</h3>
          <ul>
            {module.challenges.map((c) => (
              <li key={c.id}>
                {challengesEnabled ? <Link to={`/challenges/${c.id}`}>{c.title}</Link> : <span>{c.title}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {module.lab_scenarios.length > 0 && (
        <div>
          <h3>{t("module.lab")}</h3>
          <ul>
            {module.lab_scenarios.map((s) => (
              <li key={s.id}>
                <Link to={`/lab/${s.id}`}>{s.title}</Link>
              </li>
            ))}
          </ul>
          <p className="muted">{t("module.labNote")}</p>
        </div>
      )}
    </section>
  );
}
