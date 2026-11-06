/** Action and link buttons: native elements, one vocabulary of variants. */
import type { ButtonHTMLAttributes } from "react";
import { Link, type LinkProps } from "react-router";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

function classes(variant: ButtonVariant, className?: string): string {
  return ["btn", `btn-${variant}`, className].filter(Boolean).join(" ");
}

export function Button({
  variant = "primary",
  className,
  type = "button",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button type={type} className={classes(variant, className)} {...rest} />;
}

export function LinkButton({ variant = "primary", className, ...rest }: LinkProps & { variant?: ButtonVariant }) {
  return <Link className={classes(variant, className)} {...rest} />;
}
