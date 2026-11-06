/** Path overview (US1 scenario 1; FR-003b entry-prerequisite self-assessment). */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { get } from "../../api/client";
import { useMe } from "../../app/session";
import { ContentMeta } from "../../components/content/Callouts";
import { ErrorState, Loading } from "../../components/states";
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
    <section aria-labelledby="entry-prereqs" className="card stack">
      <h2 id="entry-prereqs" style={{ marginTop: 0 }}>
        {t("path.entryPrereqs")}
      </h2>
      <p className="muted">{t("path.entryPrereqsIntro")}</p>
      <ul style={{ listStyle: "none", padding: 0 }}>
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
    </section>
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
    <article className="stack">
      <p className="row">
        <span className="badge">{t(`catalog.level.${path.level}`)}</span>
        <span className="badge">{path.status === "planned" ? t("catalog.planned") : t("catalog.available")}</span>
        <span className="muted">{t("catalog.estimatedHours", { count: path.estimated_hours })}</span>
      </p>
      <h1>{path.title}</h1>
      <p className="reading">{path.summary}</p>
      <ContentMeta version={path.version} lastReviewed={path.last_reviewed} deprecation={path.deprecation} />
      {path.status === "planned" && <p className="alert info">{t("path.plannedNotice")}</p>}

      <section aria-labelledby="objectives">
        <h2 id="objectives">{t("path.objectives")}</h2>
        <ul className="reading">
          {path.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </section>

      {path.status === "available" && <SelfAssessment path={path} />}

      <section aria-labelledby="competencies">
        <h2 id="competencies">{t("catalog.competencies")}</h2>
        <ul className="row" style={{ listStyle: "none", padding: 0 }}>
          {path.competencies.map((c) => (
            <li key={c.id} className="badge">
              {c.title}
            </li>
          ))}
        </ul>
      </section>

      {path.status === "available" && (
        <section aria-labelledby="modules">
          <h2 id="modules">{t("path.modules")}</h2>
          {!me && (
            <p className="alert info">
              {t("path.signInToStudy")} <Link to={`/sign-in?next=/paths/${path.id}`}>{t("app.nav.signIn")}</Link>
            </p>
          )}
          <ol className="module-list">
            {path.modules.map((m) => (
              <li key={m.id}>
                <Link to={`/modules/${m.id}`}>{m.title}</Link>
                {m.status && <span className="badge" style={{ marginLeft: 8 }}>{t(`path.moduleStatus.${m.status}`)}</span>}
                <div className="muted">{m.summary}</div>
              </li>
            ))}
          </ol>
        </section>
      )}
    </article>
  );
}
