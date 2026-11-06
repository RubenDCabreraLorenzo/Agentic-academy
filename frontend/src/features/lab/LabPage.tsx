/** Laboratory trace player (US5; FR-026–FR-032, FR-027a). Replays recordings; no model calls. */
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useReducer, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { get } from "../../api/client";
import { ContentMeta } from "../../components/content/Callouts";
import { ErrorState, Loading } from "../../components/states";
import { CompareView } from "./CompareView";
import {
  effectiveElements,
  initialState,
  reduce,
  rootVariants,
  stateAt,
  variantById,
  type Action,
  type PlayerState,
  type Scenario,
  type TraceElement,
} from "./player";

function ElementBody({ e }: { e: TraceElement }) {
  const { t } = useTranslation();
  switch (e.kind) {
    case "execution_event":
      return (
        <>
          <strong>{e.event}</strong>
          {e.summary && <p style={{ margin: "4px 0 0" }}>{e.summary}</p>}
          {e.payload && Object.keys(e.payload).length > 0 && <pre className="lab-pre">{JSON.stringify(e.payload, null, 2)}</pre>}
        </>
      );
    case "tool_call":
      return (
        <>
          <strong>
            {e.tool}({JSON.stringify(e.arguments ?? {})})
          </strong>{" "}
          <span className="badge">{t(`lab.permission.${e.permission}`)}</span>{" "}
          {e.approval && e.approval !== "not_required" && <span className="badge warning">{t(`lab.approval.${e.approval}`)}</span>}
          {e.error ? (
            <pre className="lab-pre" style={{ color: "var(--danger)" }}>{e.error}</pre>
          ) : (
            <pre className="lab-pre">{JSON.stringify(e.result, null, 2)}</pre>
          )}
        </>
      );
    case "state_transition":
      return (
        <>
          <strong>{t("lab.changed", { keys: (e.changed_keys ?? []).join(", ") })}</strong>
        </>
      );
    case "decision_summary":
      return (
        <>
          <span className="badge">{t("lab.educational")}</span>
          <p style={{ margin: "4px 0 0" }}>{e.text}</p>
          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
            {t("lab.authoredBy", { author: e.author, date: e.reviewed_on })}
          </p>
        </>
      );
  }
}

export default function LabPage() {
  const { scenarioId = "" } = useParams();
  const q = useQuery({ queryKey: ["lab", scenarioId], queryFn: () => get<Scenario>(`/lab/scenarios/${scenarioId}`) });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  return <Player scenario={q.data} />;
}

function Player({ scenario }: { scenario: Scenario }) {
  const { t } = useTranslation();
  const [state, dispatch] = useReducer((s: PlayerState, a: Action) => reduce(scenario, s, a), scenario, (sc) => initialState(sc));
  const variant = variantById(scenario, state.variantId);
  const elements = useMemo(() => effectiveElements(scenario, variant), [scenario, variant]);
  const current = elements[state.index];
  const failures = new Map((scenario.failure_cases ?? []).map((f) => [f.element_id, f]));
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    if (!state.playing) return;
    const timer = window.setTimeout(() => dispatch({ type: "next" }), 1200);
    return () => window.clearTimeout(timer);
  }, [state]);

  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${state.index}"]`)?.scrollIntoView?.({ block: "nearest" });
  }, [state.index]);

  return (
    <article className="stack">
      <h1>{scenario.title}</h1>
      <ContentMeta version={scenario.version} lastReviewed={scenario.last_reviewed} />
      <p className="alert info">{t("lab.replayNote")}</p>
      <div className="grid">
        <section className="card stack" aria-labelledby="task">
          <h2 id="task" style={{ marginTop: 0 }}>{t("lab.task")}</h2>
          <p style={{ margin: 0 }}>{scenario.task}</p>
          <p style={{ margin: 0 }}><strong>{t("lab.objective")}:</strong> {scenario.objective}</p>
          <p style={{ margin: 0 }}><strong>{t("lab.pattern")}:</strong> {variant.orchestration_pattern}</p>
          <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
            {t("lab.recordedWith", { model: variant.recorded_with.model, framework: variant.recorded_with.framework, date: variant.recorded_with.date })}
          </p>
        </section>
        <section className="card stack" aria-labelledby="tools">
          <h2 id="tools" style={{ marginTop: 0 }}>{t("lab.tools")}</h2>
          <ul style={{ margin: 0 }}>
            {scenario.tools.map((tool) => (
              <li key={tool.name}>
                <code>{tool.name}</code> <span className="badge">{t(`lab.permission.${tool.permission}`)}</span>
                <div className="muted">{tool.description}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {rootVariants(scenario).length > 1 && (
        <div className="row" role="group" aria-label={t("lab.variants")}>
          {rootVariants(scenario).map((v) => (
            <button
              key={v.id}
              type="button"
              className={v.id === state.variantId ? "btn" : "btn secondary"}
              aria-pressed={v.id === state.variantId}
              onClick={() => dispatch({ type: "select", variantId: v.id })}
            >
              {v.label}
            </button>
          ))}
        </div>
      )}

      <div className="row" role="toolbar" aria-label={t("lab.controls")}>
        <button type="button" className="btn secondary" onClick={() => dispatch({ type: "prev" })} disabled={state.index === 0}>
          ← {t("lab.back")}
        </button>
        {state.playing ? (
          <button type="button" className="btn secondary" onClick={() => dispatch({ type: "pause" })}>{t("lab.pause")}</button>
        ) : (
          <button type="button" className="btn secondary" onClick={() => dispatch({ type: "play" })} disabled={state.awaitingApproval || state.index >= elements.length - 1}>
            {t("lab.play")}
          </button>
        )}
        <button type="button" className="btn" onClick={() => dispatch({ type: "next" })} disabled={state.awaitingApproval || state.index >= elements.length - 1}>
          {t("lab.forward")} →
        </button>
        <button type="button" className="linklike" onClick={() => dispatch({ type: "restart" })}>{t("lab.restart")}</button>
      </div>
      <p role="status" aria-live="polite" className="muted">
        {t("lab.position", { n: state.index + 1, total: elements.length })}
        {current && ` — ${t(`lab.kind.${current.kind}`)}`}
      </p>

      {state.awaitingApproval && current && (
        <div role="alertdialog" aria-labelledby="approval-title" className="alert warning stack">
          <strong id="approval-title">{t("lab.approvalTitle")}</strong>
          <p style={{ margin: 0 }}>{current.summary}</p>
          <div className="row">
            <button type="button" className="btn" onClick={() => dispatch({ type: "decide", decision: "approved" })}>{t("lab.approve")}</button>
            <button type="button" className="btn secondary" onClick={() => dispatch({ type: "decide", decision: "rejected" })}>{t("lab.reject")}</button>
          </div>
        </div>
      )}

      <div className="lab-layout">
        <section aria-labelledby="trace">
          <h2 id="trace">{t("lab.trace")}</h2>
          <ol ref={listRef} className="lab-trace">
            {elements.slice(0, state.index + 1).map((e, i) => (
              <li
                key={e.id}
                data-index={i}
                className={`lab-element kind-${e.kind}${i === state.index ? " current" : ""}${failures.has(e.id) ? " failing" : ""}`}
                aria-current={i === state.index ? "step" : undefined}
              >
                <button type="button" className="linklike lab-kind" onClick={() => dispatch({ type: "jump", index: i })}>
                  {t(`lab.kind.${e.kind}`)}
                </button>
                <ElementBody e={e} />
                {failures.has(e.id) && (
                  <div role="note" className="alert error" style={{ marginTop: 8 }}>
                    <strong>{t("lab.failure", { kind: failures.get(e.id)?.kind.replaceAll("_", " ") })}</strong>
                    <p style={{ margin: "4px 0" }}>
                      <strong>{t("lab.risk")}:</strong> {failures.get(e.id)?.risk}
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>{t("lab.mitigation")}:</strong> {failures.get(e.id)?.mitigation}
                    </p>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>
        <section aria-labelledby="state">
          <h2 id="state">{t("lab.state")}</h2>
          <pre className="lab-pre">{JSON.stringify(stateAt(scenario, state.variantId, state.index), null, 2)}</pre>
        </section>
      </div>

      {(scenario.comparisons ?? []).map((c) => (
        <CompareView key={`${c.left_variant}-${c.right_variant}`} scenario={scenario} comparison={c} />
      ))}

      <p>
        <Link to="/dashboard">{t("dashboard.back")}</Link>
      </p>
    </article>
  );
}
