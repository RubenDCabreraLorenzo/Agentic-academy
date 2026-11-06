/** A surface. The caller chooses the element and any heading level inside it. */
import type { ElementType, HTMLAttributes } from "react";

export function Card({ as: Element = "div", className, ...rest }: HTMLAttributes<HTMLElement> & { as?: ElementType }) {
  return <Element className={className ? `card ${className}` : "card"} {...rest} />;
}
