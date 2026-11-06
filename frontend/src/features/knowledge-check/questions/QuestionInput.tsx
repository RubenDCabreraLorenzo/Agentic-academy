/** Accessible inputs for the four question types (FR-016, NFR-001). */
import { useTranslation } from "react-i18next";
import { renderInline } from "../../../components/content/markdownParser";
import type { Answer, Question } from "../types";

interface Props {
  question: Question;
  value: Answer;
  onChange: (value: Answer) => void;
  disabled: boolean;
  legendId: string;
}

function ChoiceInput({ question, value, onChange, disabled, legendId }: Props) {
  const multiple = question.type === "multiple_choice";
  const selected = value.selected ?? [];
  const toggle = (id: string) => {
    if (!multiple) return onChange({ selected: [id] });
    onChange({ selected: selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id] });
  };
  return (
    <div role={multiple ? "group" : "radiogroup"} aria-labelledby={legendId}>
      {(question.options ?? []).map((o) => (
        <label key={o.id} className="option">
          <input
            type={multiple ? "checkbox" : "radio"}
            name={`q-${question.id}`}
            value={o.id}
            checked={selected.includes(o.id)}
            onChange={() => toggle(o.id)}
            disabled={disabled}
          />
          <span dangerouslySetInnerHTML={{ __html: renderInline(o.text) }} />
        </label>
      ))}
    </div>
  );
}

function OrderingInput({ question, value, onChange, disabled, legendId }: Props) {
  const { t } = useTranslation();
  const items = question.items ?? [];
  const order = value.selected?.length === items.length ? value.selected : items.map((i) => i.id);
  const byId = Object.fromEntries(items.map((i) => [i.id, i.text]));
  const move = (index: number, delta: number) => {
    const next = [...order];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target] as string, next[index] as string];
    onChange({ selected: next });
  };
  return (
    <ol className="ordering" aria-labelledby={legendId}>
      {order.map((id, index) => (
        <li key={id}>
          <span>
            <span className="sr-only">{index + 1}. </span>
            {byId[id]}
          </span>
          <span className="row">
            <button type="button" className="btn secondary" onClick={() => move(index, -1)} disabled={disabled || index === 0}>
              ↑ <span className="sr-only">{t("check.moveUp")}: {byId[id]}</span>
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={() => move(index, 1)}
              disabled={disabled || index === order.length - 1}
            >
              ↓ <span className="sr-only">{t("check.moveDown")}: {byId[id]}</span>
            </button>
          </span>
        </li>
      ))}
    </ol>
  );
}

function MatchingInput({ question, value, onChange, disabled }: Props) {
  const { t } = useTranslation();
  const pairs = value.pairs ?? {};
  return (
    <div>
      {(question.left ?? []).map((l) => (
        <div key={l.id} className="matching-row">
          <label htmlFor={`m-${question.id}-${l.id}`} style={{ fontWeight: 400 }}>
            {l.text}
          </label>
          <select
            id={`m-${question.id}-${l.id}`}
            aria-label={t("check.matchWith", { item: l.text })}
            value={pairs[l.id] ?? ""}
            disabled={disabled}
            onChange={(e) => onChange({ pairs: { ...pairs, [l.id]: e.target.value } })}
          >
            <option value="">{t("check.choose")}</option>
            {(question.right ?? []).map((r) => (
              <option key={r.id} value={r.id}>
                {r.text}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}

export function QuestionInput(props: Props) {
  switch (props.question.type) {
    case "single_choice":
    case "multiple_choice":
      return <ChoiceInput {...props} />;
    case "ordering":
      return <OrderingInput {...props} />;
    case "matching":
      return <MatchingInput {...props} />;
  }
}

export function isAnswered(question: Question, value: Answer | undefined): boolean {
  if (!value) return false;
  if (question.type === "matching") return (question.left ?? []).every((l) => !!value.pairs?.[l.id]);
  if (question.type === "ordering") return true;
  return (value.selected ?? []).length > 0;
}

export function initialAnswer(question: Question): Answer {
  return question.type === "ordering" ? { selected: (question.items ?? []).map((i) => i.id) } : {};
}
