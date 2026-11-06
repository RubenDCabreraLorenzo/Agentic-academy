/** Small status label. Never interactive. */
import type { HTMLAttributes } from "react";
import type { Tone } from "./Alert";

export function Badge({ tone, className, ...rest }: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return <span className={["badge", tone && `badge-${tone}`, className].filter(Boolean).join(" ")} {...rest} />;
}
