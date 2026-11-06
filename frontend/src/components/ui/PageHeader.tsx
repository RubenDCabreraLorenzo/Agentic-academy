/** Page title block. The heading is the focus target after navigation (routes contract). */
import type { ReactNode } from "react";
import { usePageMeta } from "../../app/navigation/usePageMeta";

export function PageHeader({
  title,
  summary,
  description,
  children,
}: {
  title: string;
  summary?: ReactNode;
  description?: string;
  children?: ReactNode;
}) {
  usePageMeta({ title, description });
  return (
    <header className="page-header">
      <h1 tabIndex={-1}>{title}</h1>
      {summary && <p>{summary}</p>}
      {children}
    </header>
  );
}
