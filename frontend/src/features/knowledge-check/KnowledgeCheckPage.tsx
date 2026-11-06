/** Knowledge check flow (US2; FR-016–FR-019, FR-045b). */
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { ApiError, NetworkError, post, put } from "../../api/client";
import { clearDraft, loadDraft, saveDraft } from "../../app/drafts";
import { useMe } from "../../app/session";
import { InlineMarkdown } from "../../components/content/Markdown";
import { ErrorState, Loading } from "../../components/states";
import { formatPercent } from "../../i18n";
import { initialAnswer, isAnswered, QuestionInput } from "./questions/QuestionInput";
import type { Answer, Attempt, AttemptResult, Feedback } from "./types";

function lessonHref(link: Feedback["lesson_link"]): string {
  return `/modules/${link.module_id}#lesson-${link.lesson_id}`;
}

function newId(): string {
  return crypto.randomUUID();
}

export default function KnowledgeCheckPage() {
  const { t } = useTranslation();
  const { checkId = "" } = useParams();
  const { data: me } = useMe();
  const qc = useQueryClient();
  const legendId = useId();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [feedback, setFeedback] = useState<Record<string, Feedback>>({});
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const learner = me?.id ?? "anon";
  const draftKey = `check:${checkId}`;

  const starting = useRef(false);
  const start = useCallback(async () => {
    if (starting.current) return;
    starting.current = true;
    setError(null);
    setResult(null);
    setAttempt(null);
    try {
      const a = await post<Attempt>(`/knowledge-checks/${checkId}/attempts`, { attempt_id: newId() });
      setAttempt(a);
      const draft = loadDraft<Record<string, Answer>>(learner, `${draftKey}:${a.attempt_id}`) ?? {};
      const init: Record<string, Answer> = {};
      for (const q of a.questions) init[q.id] = a.saved_answers[q.id] ?? draft[q.id] ?? initialAnswer(q);
      setAnswers(init);
      setFeedback(a.feedback);
      const firstOpen = a.questions.findIndex((q) => !a.feedback[q.id]);
      setIndex(firstOpen === -1 ? a.questions.length - 1 : firstOpen);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("states.errorBody"));
    } finally {
      starting.current = false;
    }
  }, [checkId, learner, draftKey, t]);

  useEffect(() => {
    if (me) void start();
  }, [me, start]);

  useEffect(() => headingRef.current?.focus(), [index, result]);

  if (error) return <ErrorState message={error} onRetry={start} />;
  if (!attempt) return <Loading />;

  const total = attempt.questions.length;
  const question = attempt.questions[index];
  const answeredFeedback = question ? feedback[question.id] : undefined;

  const updateAnswer = (value: Answer) => {
    if (!question) return;
    const next = { ...answers, [question.id]: value };
    setAnswers(next);
    saveDraft(learner, `${draftKey}:${attempt.attempt_id}`, next);
  };

  const check = async () => {
    if (!question) return;
    setBusy(true);
    try {
      const fb = await put<Feedback>(`/attempts/${attempt.attempt_id}/answers/${question.id}`, answers[question.id]);
      setFeedback({ ...feedback, [question.id]: fb });
    } catch (e) {
      if (!(e instanceof NetworkError) && !(e instanceof ApiError && e.status === 401)) setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  };

  const submit = async (confirm: boolean) => {
    setBusy(true);
    try {
      const r = await post<AttemptResult>(`/attempts/${attempt.attempt_id}/submit`, { confirm_unanswered: confirm });
      clearDraft(learner, `${draftKey}:${attempt.attempt_id}`);
      setResult(r);
      setConfirming(false);
      void qc.invalidateQueries({ queryKey: ["module", attempt.module_id] });
    } catch (e) {
      if (e instanceof ApiError && e.code === "unanswered_questions") setConfirming(true);
      else if (!(e instanceof NetworkError)) setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  };

  if (result) {
    return (
      <section className="stack reading" aria-live="polite">
        <h1 ref={headingRef} tabIndex={-1}>
          {result.passed ? t("check.passed") : t("check.notPassed")}
        </h1>
        <p>
          {t("check.score", { score: formatPercent(result.score) })}
          {result.best_score !== null && <> · {t("check.best", { score: formatPercent(result.best_score) })}</>}
        </p>
        {result.passed && result.competencies_demonstrated.length === 0 && (
          <p className="alert info">{t("check.competencyPending")}</p>
        )}
        {result.weak_objectives.length > 0 && (
          <div className="alert warning">
            <h2 style={{ marginTop: 0 }}>{t("check.weakObjectives")}</h2>
            <ul>
              {result.weak_objectives.map((w) => (
                <li key={w.id}>
                  {w.statement} — <Link to={lessonHref(w.lesson_link)}>{t("check.review")}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="row">
          <button type="button" className="btn" onClick={start}>
            {t("check.retry")}
          </button>
          <Link className="btn secondary" to={`/modules/${attempt.module_id}`}>
            {t("check.backToModule")}
          </Link>
        </div>
      </section>
    );
  }

  const unanswered = attempt.questions.filter((q) => !feedback[q.id] && !isAnswered(q, answers[q.id])).length;

  return (
    <section className="stack reading">
      <p>
        <Link to={`/modules/${attempt.module_id}`}>{t("check.backToModule")}</Link>
      </p>
      <h1 ref={headingRef} tabIndex={-1}>
        {t("module.knowledgeCheck")}
      </h1>
      <p>{t("check.intro", { count: total, threshold: formatPercent(attempt.pass_threshold) })}</p>
      <details>
        <summary>{t("check.assesses")}</summary>
        <ul>
          {attempt.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </details>
      {question && (
        <div className="question card stack">
          <fieldset>
            <legend id={legendId}>{t("check.question", { n: index + 1, total })}</legend>
            <InlineMarkdown source={question.prompt_markdown} />
            <QuestionInput
              question={question}
              value={answers[question.id] ?? {}}
              onChange={updateAnswer}
              disabled={!!answeredFeedback || busy}
              legendId={legendId}
            />
          </fieldset>
          {answeredFeedback ? (
            <div role="status" className={`alert ${answeredFeedback.correct ? "success" : "error"}`}>
              <strong>{answeredFeedback.correct ? t("check.correct") : t("check.incorrect")}</strong>
              <InlineMarkdown source={answeredFeedback.explanation_markdown} />
              <Link to={lessonHref(answeredFeedback.lesson_link)}>{t("check.review")}</Link>
            </div>
          ) : (
            <button type="button" className="btn" onClick={check} disabled={busy || !isAnswered(question, answers[question.id])}>
              {t("check.checkAnswer")}
            </button>
          )}
          <div className="row" style={{ justifyContent: "space-between" }}>
            <button type="button" className="btn secondary" onClick={() => setIndex(index - 1)} disabled={index === 0}>
              {t("check.previous")}
            </button>
            {index < total - 1 ? (
              <button type="button" className="btn secondary" onClick={() => setIndex(index + 1)}>
                {t("check.next")}
              </button>
            ) : (
              <button type="button" className="btn" onClick={() => submit(false)} disabled={busy}>
                {t("check.submit")}
              </button>
            )}
          </div>
        </div>
      )}
      {confirming && (
        <div role="alertdialog" aria-labelledby="unanswered-title" className="alert warning stack">
          <strong id="unanswered-title">{t("check.unansweredTitle")}</strong>
          <p>{t("check.unansweredBody", { count: unanswered })}</p>
          <div className="row">
            <button type="button" className="btn" onClick={() => submit(true)}>
              {t("check.submitAnyway")}
            </button>
            <button type="button" className="btn secondary" onClick={() => setConfirming(false)}>
              {t("check.keepAnswering")}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
