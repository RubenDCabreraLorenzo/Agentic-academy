/** Path overview (US1 scenario 1; FR-003b entry-prerequisite self-assessment). */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { get } from "../../api/client";
import { useMe } from "../../app/session";
import { ContentMeta } from "../../components/content/Callouts";
import { ErrorState, Loading } from "../../components/states";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import type { PathDetail } from "./types";

const SELF_KEY = "academy:self-assessment:";

function readChecks(pathId: string): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(SELF_KEY + pathId) ?? "{}") as Record<string, boolean>;
  } catch {
    return {};
  }
}

function SelfAssessment({ path }: { path: PathDetail }) {
  const { t } = useTranslation();
  const [checks, setChecks] = useState(() => readChecks(path.id));
  const toggle = (label: string) => {
    const next = { ...checks, [label]: !checks[label] };
    setChecks(next);
    try {
      localStorage.setItem(SELF_KEY + path.id, JSON.stringify(next));
    } catch {
      /* local-only convenience */
    }
  };
  if (!path.entry_prerequisites.length) return null;
  return (
    <Card as="section" aria-labelledby="entry-prereqs" className="stack">
      <h2 id="entry-prereqs">{t("path.entryPrereqs")}</h2>
      <p className="muted">{t("path.entryPrereqsIntro")}</p>
      <ul className="plain-list">
        {path.entry_prerequisites.map((p) => (
          <li key={p.label} className="row">
            <label className="option">
              <input type="checkbox" checked={!!checks[p.label]} onChange={() => toggle(p.label)} />
              <span>{p.label}</span>
            </label>
            <a href={p.resource_url} target="_blank" rel="noopener noreferrer">
              {t("path.learnMore")}
              <span className="sr-only">: {p.label}</span>
            </a>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export default function PathPage() {
  const { t } = useTranslation();
  const { pathId = "" } = useParams();
  const { data: me } = useMe();
  const q = useQuery({ queryKey: ["path", pathId, !!me], queryFn: () => get<PathDetail>(`/paths/${pathId}`) });

  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const path = q.data;

  return (
    <article className="stack-lg">
      <header className="stack">
        <p className="row">
          <Badge>{t(`catalog.level.${path.level}`)}</Badge>
          <Badge tone={path.status === "planned" ? undefined : "success"}>{path.status === "planned" ? t("catalog.planned") : t("catalog.available")}</Badge>
          <span className="muted">{t("catalog.estimatedHours", { count: path.estimated_hours })}</span>
        </p>
        <h1>{path.title}</h1>
        <p className="measure">{path.summary}</p>
        <ContentMeta version={path.version} lastReviewed={path.last_reviewed} deprecation={path.deprecation} />
        {path.status === "planned" && <Alert tone="info">{t("path.plannedNotice")}</Alert>}
      </header>

      <section aria-labelledby="objectives" className="stack">
        <h2 id="objectives">{t("path.objectives")}</h2>
        <ul className="measure">
          {path.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </section>

      {path.status === "available" && <SelfAssessment path={path} />}

      <section aria-labelledby="competencies" className="stack">
        <h2 id="competencies">{t("catalog.competencies")}</h2>
        <ul className="row plain-list">
          {path.competencies.map((c) => (
            <li key={c.id}>
              <Badge className="badge-wrap">{c.title}</Badge>
            </li>
          ))}
        </ul>
      </section>

      {path.status === "available" && (
        <section aria-labelledby="modules" className="stack">
          <h2 id="modules">{t("path.modules")}</h2>
          {!me && (
            <Alert tone="info">
              {t("path.signInToStudy")} <Link to={`/sign-in?next=/paths/${path.id}`}>{t("app.nav.signIn")}</Link>
            </Alert>
          )}
          <ol className="module-list">
            {path.modules.map((m) => (
              <li key={m.id}>
                <div className="row">
                  <Link to={`/modules/${m.id}`}>{m.title}</Link>
                  {m.status && <Badge>{t(`path.moduleStatus.${m.status}`)}</Badge>}
                </div>
                <div className="muted">{m.summary}</div>
              </li>
            ))}
          </ol>
        </section>
      )}
    </article>
  );
}
