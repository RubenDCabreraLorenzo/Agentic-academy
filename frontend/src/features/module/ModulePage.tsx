/** Module page (US1; FR-006, FR-007, FR-015, NFR-012 reading mode). */
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { get } from "../../api/client";
import { useFragmentTarget } from "../../app/navigation/useFragmentTarget";
import { usePageMeta } from "../../app/navigation/usePageMeta";
import { ContentMeta } from "../../components/content/Callouts";
import { ErrorState, Loading } from "../../components/states";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Breadcrumb } from "../../components/ui/Breadcrumb";
import type { ModuleDetail } from "../catalog/types";
import { LessonView } from "./LessonView";
import { ModuleStatusBadge, PracticeSection } from "./ModuleStatus";

export default function ModulePage() {
  const { t } = useTranslation();
  const { moduleId = "" } = useParams();
  const q = useQuery({ queryKey: ["module", moduleId], queryFn: () => get<ModuleDetail>(`/modules/${moduleId}`) });
  const seen = useRef(new Set<string>());
  usePageMeta({ title: q.data?.title ?? t("meta.module.title") });
  useFragmentTarget(!!q.data);

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
    <article className="stack-lg">
      <Breadcrumb items={[{ label: m.path_title ?? t("module.backToPath"), to: `/paths/${m.path_id}` }]} />
      <header className="stack reading">
        <h1>{m.title}</h1>
        <p>{m.summary}</p>
        <div className="row">
          <ModuleStatusBadge status={m.status} />
        </div>
        <ContentMeta version={m.version} lastReviewed={m.last_reviewed} deprecation={m.deprecation} />
      </header>

      {m.missing_prerequisites.length > 0 && (
        <Alert tone="warning" role="note" className="reading">
          <div className="stack">
            <p>{t("module.missingPrereqs")}</p>
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
        </Alert>
      )}

      <section aria-labelledby="objectives" className="reading stack">
        <h2 id="objectives">{t("module.objectives")}</h2>
        <ul>
          {m.objectives.map((o) => (
            <li key={o.id}>{o.statement}</li>
          ))}
        </ul>
      </section>

      <nav aria-labelledby="toc" className="reading stack">
        <h2 id="toc">{t("module.contents")}</h2>
        <ol>
          {m.lessons.map((l) => (
            <li key={l.id}>
              <Link to={`#lesson-${l.id}`}>{l.title}</Link>
            </li>
          ))}
        </ol>
      </nav>

      {m.lessons.map((lesson) => (
        <LessonView key={lesson.id} lesson={lesson} deprecations={m.deprecations} onVisible={onLessonVisible} />
      ))}

      <section aria-labelledby="refs" className="reading stack">
        <h2 id="refs">{t("module.references")}</h2>
        <ul>
          {m.references.map((r) => (
            <li key={r.url}>
              <span className="row">
                <a href={r.url} target="_blank" rel="noopener noreferrer">
                  {r.title}
                </a>
                {r.vendor && <Badge>{t("content.vendor", { name: r.vendor })}</Badge>}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <PracticeSection module={m} />

      <nav aria-label={t("module.contents")} className="row row-between">
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
