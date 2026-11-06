/** Inline icon set kept in the repository. Decorative by default; pass `label` when an icon carries meaning alone. */
const PATHS = {
  check: "M5 12.5l4.5 4.5L19 7.5",
  cross: "M6 6l12 12M18 6L6 18",
  warning: "M12 4l9 16H3zM12 10v4.5M12 17.5v.5",
  info: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v5.5M12 7.5v.5",
  danger: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7.5V13M12 16.5v.5",
  external: "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
  arrowLeft: "M19 12H5M11 6l-6 6 6 6",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  arrowUp: "M12 19V5M6 11l6-6 6 6",
  arrowDown: "M12 5v14M6 13l6 6 6-6",
  traceEvent: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3.5 2",
  traceTool: "M14.5 6.5a4 4 0 0 0-5.3 5l-5.2 5.2 2.8 2.8 5.2-5.2a4 4 0 0 0 5-5.3l-2.6 2.6-2.3-.5-.5-2.3z",
  traceState: "M4 7h13M13 3l4 4-4 4M20 17H7M11 13l-4 4 4 4",
  traceSummary: "M5 4h14v12H9l-4 4zM9 8.5h6M9 12h4",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, label, className }: { name: IconName; label?: string; className?: string }) {
  return (
    <svg
      className={className ? `icon ${className}` : "icon"}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
