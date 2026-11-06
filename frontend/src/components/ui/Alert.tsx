/** Inline message: tone is always shown by an icon and by the text, never by color alone. */
import type { HTMLAttributes } from "react";
import { Icon, type IconName } from "./Icon";

export type Tone = "info" | "success" | "warning" | "danger";

const ICONS: Record<Tone, IconName> = { info: "info", success: "check", warning: "warning", danger: "danger" };

export function Alert({ tone = "info", className, children, ...rest }: HTMLAttributes<HTMLDivElement> & { tone?: Tone }) {
  return (
    <div className={["alert", `alert-${tone}`, className].filter(Boolean).join(" ")} {...rest}>
      <Icon name={ICONS[tone]} />
      <div className="alert-body">{children}</div>
    </div>
  );
}
