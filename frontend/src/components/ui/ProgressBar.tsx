/** Progress indicator with a name, a value and a text equivalent. */
import type { CSSProperties } from "react";

export function ProgressBar({ label, value, max, valueText }: { label: string; value: number; max: number; valueText?: string }) {
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  return (
    <div className="progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-valuetext={valueText}>
      {/* eslint-disable-next-line no-restricted-syntax -- value computed from data (tokens contract, rule 1) */}
      <span style={{ "--progress": ratio } as CSSProperties} />
    </div>
  );
}
