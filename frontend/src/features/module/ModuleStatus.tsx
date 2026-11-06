/** Module status and practice entry points (FR-037; increment-1 label from /health). */
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useHealth } from "../../app/session";
import { Badge } from "../../components/ui/Badge";
import { LinkButton } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { ModuleDetail } from "../catalog/types";

export function ModuleStatusBadge({ status }: { status: ModuleDetail["status"] }) {
  const { t } = useTranslation();
  return <Badge tone={status === "completed" ? "success" : status === "in_progress" ? "warning" : undefined}>{t(`path.moduleStatus.${status}`)}</Badge>;
}

export function PracticeSection({ module }: { module: ModuleDetail }) {
  const { t } = useTranslation();
  const health = useHealth();
  const challengesEnabled = health.data?.challenges_enabled ?? false;
  return (
    <Card as="section" aria-labelledby="practice" className="stack">
      <h2 id="practice">{t("module.practice")}</h2>
      <div className="row">
        <ModuleStatusBadge status={module.status} />
        {module.status !== "completed" && !challengesEnabled && module.challenges.length > 0 && (
          <span className="muted">{t("module.challengeLater")}</span>
        )}
      </div>
      {module.knowledge_check_id && (
        <div className="stack">
          <h3>{t("module.knowledgeCheck")}</h3>
          <LinkButton to={`/knowledge-checks/${module.knowledge_check_id}`}>{t("module.startCheck")}</LinkButton>
          {module.objectives_demonstrated && <p className="muted">{t("check.competencyPending")}</p>}
        </div>
      )}
      {module.challenges.length > 0 && (
        <div className="stack">
          <h3>{t("module.challenge")}</h3>
          <ul>
            {module.challenges.map((c) => (
              <li key={c.id}>{challengesEnabled ? <Link to={`/challenges/${c.id}`}>{c.title}</Link> : <span>{c.title}</span>}</li>
            ))}
          </ul>
        </div>
      )}
      {module.lab_scenarios.length > 0 && (
        <div className="stack">
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
    </Card>
  );
}
