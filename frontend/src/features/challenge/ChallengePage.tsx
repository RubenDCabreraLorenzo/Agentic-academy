/** Code challenge page (US4; FR-021–FR-024, FR-022c, FR-045b). */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { ApiError, get, NetworkError, post, put } from "../../api/client";
import { loadDraft, saveDraft } from "../../app/drafts";
import { useMe } from "../../app/session";
import { ContentMeta } from "../../components/content/Callouts";
import { InlineMarkdown } from "../../components/content/Markdown";
import { ErrorState, Loading } from "../../components/states";
import { formatDate } from "../../i18n";
import { Editor } from "./Editor";

interface Criterion {
  id: string;
  description: string;
  mandatory: boolean;
}

interface Challenge {
  id: string;
  version: string;
  last_reviewed: string;
  deprecation?: { reason: string; replacement?: string | null; since: string } | null;
  title: string;
  module_id: string;
  scenario_markdown: string;
  problem_markdown: string;
  expected_outcome_markdown: string;
  instructions_markdown: string;
  criteria: Criterion[];
  competencies: { id: string; title: string }[];
  files: Record<string, string>;
  starter_files: Record<string, string>;
  tests: Record<string, string>;
  hints_revealed: string[];
  hints_total: number;
  attempts: number;
  passed: boolean;
  reference_explanation_markdown: string | null;
  evaluation_enabled: boolean;
}

interface CriterionResult {
  criterion_id: string;
  description: string;
  mandatory: boolean;
  met: boolean;
  feedback_markdown: string | null;
  tests: { id: string; title: string; outcome: string; message: string | null }[];
}

interface Submission {
  submission_id: string;
  kind: "visible_run" | "submission";
  attempt_number: number | null;
  status: "queued" | "running" | "passed" | "failed" | "stopped" | "error" | "cancelled";
  queue_position: number | null;
  delayed: boolean;
  stop_reason: string | null;
  criteria_results: CriterionResult[];
  output_excerpt: string;
  queued_at: string | null;
  finished_at: string | null;
  competencies_demonstrated?: string[];
}

const ACTIVE = new Set(["queued", "running"]);

export default function ChallengePage() {
  const { t } = useTranslation();
  const { challengeId = "" } = useParams();
  const { data: me } = useMe();
  const qc = useQueryClient();
  const learner = me?.id ?? "anon";
  const draftKey = `challenge:${challengeId}`;
  const q = useQuery({ queryKey: ["challenge", challengeId], queryFn: () => get<Challenge>(`/challenges/${challengeId}`) });
  const history = useQuery({
    queryKey: ["submissions", challengeId],
    queryFn: () => get<Submission[]>(`/challenges/${challengeId}/submissions`),
  });
  const [files, setFiles] = useState<Record<string, string> | null>(null);
  const [active, setActive] = useState<string>("");
  const [current, setCurrent] = useState<Submission | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [hints, setHints] = useState<string[]>([]);
  const saveTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!q.data || files) return;
    const draft = loadDraft<Record<string, string>>(learner, draftKey);
    const initial = draft ?? q.data.files;
    setFiles(initial);
    setActive(Object.keys(initial)[0] ?? "");
    setHints(q.data.hints_revealed);
  }, [q.data, files, learner, draftKey]);

  const persist = useCallback(
    (next: Record<string, string>) => {
      saveDraft(learner, draftKey, next);
      window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(() => {
        void put(`/challenges/${challengeId}/workspace`, next).catch(() => undefined);
      }, 1000);
    },
    [learner, draftKey, challengeId],
  );

  // Poll the active submission.
  useEffect(() => {
    if (!current || !ACTIVE.has(current.status)) return;
    const timer = window.setTimeout(async () => {
      try {
        const next = await get<Submission>(`/submissions/${current.submission_id}`);
        setCurrent(next);
        if (!ACTIVE.has(next.status)) {
          void qc.invalidateQueries({ queryKey: ["submissions", challengeId] });
          void qc.invalidateQueries({ queryKey: ["challenge", challengeId] });
          void qc.invalidateQueries({ queryKey: ["module"] });
        }
      } catch {
        /* keep polling on transient errors */
        setCurrent({ ...current });
      }
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [current, challengeId, qc]);

  if (q.isLoading || !files) return q.isError ? <ErrorState onRetry={() => q.refetch()} /> : <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const ch = q.data;
  const testFiles = Object.keys(ch.tests);
  const editorFiles = { ...files, ...Object.fromEntries(testFiles.map((n) => [`tests/${n}`, ch.tests[n] ?? ""])) };
  const busy = !!current && ACTIVE.has(current.status);

  const onChange = (name: string, value: string) => {
    if (name.startsWith("tests/")) return;
    const next = { ...files, [name]: value };
    setFiles(next);
    persist(next);
  };

  const send = async (kind: "visible_run" | "submission") => {
    setNotice(null);
    try {
      const sub = await post<Submission>(`/challenges/${challengeId}/submissions`, {
        submission_id: crypto.randomUUID(),
        kind,
        files,
      });
      setCurrent(sub);
    } catch (e) {
      if (e instanceof ApiError && e.code === "evaluation_unavailable") setNotice(t("challenge.unavailable"));
      else if (e instanceof ApiError && e.code === "run_in_progress") setNotice(t("challenge.inProgress"));
      else if (e instanceof ApiError && e.code === "invalid_submission_files") setNotice(e.detail ?? e.message);
      else if (e instanceof NetworkError) setNotice(t("states.offline"));
      else setNotice(t("states.errorBody"));
    }
  };

  const revealHint = async () => {
    try {
      const h = await post<{ index: number; total: number; markdown: string }>(`/challenges/${challengeId}/hints`);
      setHints([...hints, h.markdown]);
    } catch {
      /* no more hints */
    }
  };

  const reset = () => {
    setFiles(ch.starter_files);
    persist(ch.starter_files);
    setActive(Object.keys(ch.starter_files)[0] ?? "");
  };

  return (
    <article className="stack">
      <nav aria-label="Breadcrumb">
        <Link to={`/modules/${ch.module_id}`}>{t("challenge.backToModule")}</Link>
      </nav>
      <header className="stack reading">
        <h1>{ch.title}</h1>
        <ContentMeta version={ch.version} lastReviewed={ch.last_reviewed} deprecation={ch.deprecation} />
        {ch.passed && <p className="badge success">{t("challenge.completed")}</p>}
      </header>

      <section className="reading" aria-labelledby="scenario">
        <h2 id="scenario">{t("challenge.scenario")}</h2>
        <InlineMarkdown source={ch.scenario_markdown} />
        <h2>{t("challenge.problem")}</h2>
        <InlineMarkdown source={ch.problem_markdown} />
        <h2>{t("challenge.expected")}</h2>
        <InlineMarkdown source={ch.expected_outcome_markdown} />
        <h2>{t("challenge.instructions")}</h2>
        <InlineMarkdown source={ch.instructions_markdown} />
        <h2>{t("challenge.criteria")}</h2>
        <ul>
          {ch.criteria.map((c) => (
            <li key={c.id}>
              {c.description} {!c.mandatory && <span className="badge">{t("challenge.optional")}</span>}
            </li>
          ))}
        </ul>
        <p className="muted">
          {t("challenge.validates")}: {ch.competencies.map((c) => c.title).join(", ")}
        </p>
      </section>

      <section aria-labelledby="hints" className="card stack reading">
        <h2 id="hints" style={{ marginTop: 0 }}>
          {t("challenge.hints")}
        </h2>
        {hints.length === 0 && <p className="muted">{t("challenge.hintsIntro", { total: ch.hints_total })}</p>}
        <ol>
          {hints.map((h, i) => (
            <li key={i}>
              <InlineMarkdown source={h} />
            </li>
          ))}
        </ol>
        {hints.length < ch.hints_total && (
          <button type="button" className="btn secondary" onClick={revealHint}>
            {t("challenge.showHint", { n: hints.length + 1, total: ch.hints_total })}
          </button>
        )}
      </section>

      <section aria-labelledby="code" className="stack">
        <h2 id="code">{t("challenge.code")}</h2>
        <Editor
          files={editorFiles}
          active={active}
          onSelect={setActive}
          onChange={onChange}
          readOnlyFiles={testFiles.map((n) => `tests/${n}`)}
          label={t("challenge.files")}
        />
        <div className="row">
          <button type="button" className="btn secondary" onClick={() => send("visible_run")} disabled={busy || !ch.evaluation_enabled}>
            {t("challenge.runTests")}
          </button>
          <button type="button" className="btn" onClick={() => send("submission")} disabled={busy || !ch.evaluation_enabled}>
            {t("challenge.submit")}
          </button>
          <button type="button" className="linklike" onClick={reset}>
            {t("challenge.reset")}
          </button>
        </div>
        {!ch.evaluation_enabled && <p className="alert info">{t("module.challengeLater")}</p>}
        {notice && (
          <p role="alert" className="alert warning">
            {notice}
          </p>
        )}
      </section>

      {current && <ResultView submission={current} />}

      {ch.passed && ch.reference_explanation_markdown && (
        <section aria-labelledby="reference" className="card reading">
          <h2 id="reference" style={{ marginTop: 0 }}>
            {t("challenge.reference")}
          </h2>
          <InlineMarkdown source={ch.reference_explanation_markdown} />
        </section>
      )}

      <section aria-labelledby="history" className="reading">
        <h2 id="history">{t("challenge.history")}</h2>
        {(history.data ?? []).length === 0 ? (
          <p className="muted">{t("states.empty")}</p>
        ) : (
          <ul>
            {(history.data ?? []).map((s) => (
              <li key={s.submission_id}>
                <button type="button" className="linklike" onClick={() => setCurrent(s)}>
                  {s.kind === "submission" ? t("challenge.submissionN", { n: s.attempt_number ?? "–" }) : t("challenge.testRun")} ·{" "}
                  {t(`challenge.status.${s.status}`)}
                  {s.queued_at ? ` · ${formatDate(s.queued_at)}` : ""}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}

function ResultView({ submission: s }: { submission: Submission }) {
  const { t } = useTranslation();
  const active = ACTIVE.has(s.status);
  return (
    <section aria-labelledby="result" className="card stack" aria-live="polite">
      <h2 id="result" style={{ marginTop: 0 }}>
        {s.kind === "submission" ? t("challenge.resultSubmission") : t("challenge.resultRun")}: {t(`challenge.status.${s.status}`)}
      </h2>
      {active && (
        <p role="status">
          {s.status === "queued" && s.queue_position ? t("challenge.queued", { position: s.queue_position }) : t("challenge.running")}
          {s.delayed && <> {t("challenge.delayed")}</>}
        </p>
      )}
      {s.stop_reason && <p className="alert warning">{t(`challenge.stop.${s.stop_reason}`)}</p>}
      {s.status === "error" && <p className="alert error">{t("challenge.infraError")}</p>}
      {s.criteria_results.map((c) => (
        <div key={c.criterion_id} className={`alert ${c.met ? "success" : "error"}`}>
          <strong>
            {c.met ? "✓" : "✗"} {c.description}
            {!c.mandatory && ` (${t("challenge.optional")})`}
          </strong>
          {c.feedback_markdown && <InlineMarkdown source={c.feedback_markdown} />}
          {c.tests
            .filter((x) => x.outcome !== "passed" && x.message)
            .map((x) => (
              <pre key={x.id} style={{ whiteSpace: "pre-wrap", overflowX: "auto", fontSize: "0.85rem" }}>
                {x.title}: {x.message}
              </pre>
            ))}
        </div>
      ))}
      {s.status === "passed" && s.kind === "submission" && <p className="alert success">{t("challenge.passedNote")}</p>}
      {!active && s.output_excerpt && (
        <details>
          <summary>{t("challenge.output")}</summary>
          <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto", maxHeight: 320 }}>{s.output_excerpt}</pre>
        </details>
      )}
    </section>
  );
}
