/** Module page (US1; FR-006, FR-007, FR-015, NFR-012 reading mode). */
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { get } from "../../api/client";
import { ContentMeta } from "../../components/content/Callouts";
import { ErrorState, Loading } from "../../components/states";
import type { ModuleDetail } from "../catalog/types";
import { LessonView } from "./LessonView";
import { ModuleStatusBadge, PracticeSection } from "./ModuleStatus";

export default function ModulePage() {
  const { t } = useTranslation();
  const { moduleId = "" } = useParams();
  const q = useQuery({ queryKey: ["module", moduleId], queryFn: () => get<ModuleDetail>(`/modules/${moduleId}`) });
  const seen = useRef(new Set<string>());

  const onLessonVisible = useCallback(
    (lessonId: string) => {
      if (seen.current.has(lessonId)) return;
      seen.current.add(lessonId);
      void get(`/modules/${moduleId}?lesson=${encodeURIComponent(lessonId)}`).catch(() => seen.current.delete(lessonId));
    },
    [moduleId],
  );

  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const m = q.data;

  return (
    <article className="stack">
      <nav aria-label="Breadcrumb">
        <Link to={`/paths/${m.path_id}`}>{m.path_title ?? t("module.backToPath")}</Link>
      </nav>
      <header className="stack reading">
        <h1>{m.title}</h1>
        <p>{m.summary}</p>
        <div className="row">
          <ModuleStatusBadge status={m.status} />
        </div>
        <ContentMeta version={m.version} lastReviewed={m.last_reviewed} deprecation={m.deprecation} />
      </header>

      {m.missing_prerequisites.length > 0 && (
        <div className="alert warning reading" role="note">
          <p style={{ marginTop: 0 }}>{t("module.missingPrereqs")}</p>
          <ul>
            {m.missing_prerequisites.map((p) => (
              <li key={p.id}>
                {p.title}
                {p.taught_in_module && (
                  <>
                    {" — "}
                    <Link to={`/modules/${p.taught_in_module}`}>{t("module.taughtIn", { module: p.taught_in_module })}</Link>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <section aria-labelledby="objectives" className="reading">
        <h2 id="objectives">{t("module.objectives")}</h2>
        <ul>
          {m.objectives.map((o) => (
            <li key={o.id}>{o.statement}</li>
          ))}
        </ul>
      </section>

      <nav aria-labelledby="toc" className="reading">
        <h2 id="toc">{t("module.contents")}</h2>
        <ol>
          {m.lessons.map((l) => (
            <li key={l.id}>
              <a href={`#lesson-${l.id}`}>{l.title}</a>
            </li>
          ))}
        </ol>
      </nav>

      {m.lessons.map((lesson) => (
        <LessonView key={lesson.id} lesson={lesson} deprecations={m.deprecations} onVisible={onLessonVisible} />
      ))}

      <section aria-labelledby="refs" className="reading">
        <h2 id="refs">{t("module.references")}</h2>
        <ul>
          {m.references.map((r) => (
            <li key={r.url}>
              <a href={r.url} target="_blank" rel="noopener noreferrer">
                {r.title}
              </a>
              {r.vendor && <span className="badge" style={{ marginLeft: 8 }}>{t("content.vendor", { name: r.vendor })}</span>}
            </li>
          ))}
        </ul>
      </section>

      <PracticeSection module={m} />

      <nav aria-label={t("module.contents")} className="row" style={{ justifyContent: "space-between" }}>
        {m.previous_module_id ? (
          <Link to={`/modules/${m.previous_module_id}`}>← {t("module.previous")}</Link>
        ) : (
          <span />
        )}
        <Link to={`/paths/${m.path_id}`}>{t("module.backToPath")}</Link>
        {m.next_module_id ? <Link to={`/modules/${m.next_module_id}`}>{t("module.next")} →</Link> : <span />}
      </nav>
    </article>
  );
}
