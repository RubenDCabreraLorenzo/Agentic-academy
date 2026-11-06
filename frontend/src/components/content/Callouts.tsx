/** Maturity labels (FR-010), vendor notes (FR-011), deprecation notices (FR-049), content metadata. */
import { useTranslation } from "react-i18next";
import { formatDate } from "../../i18n";

export type Maturity = "established" | "emerging" | "experimental";

export function MaturityBadge({ level }: { level: Maturity }) {
  const { t } = useTranslation();
  return <span className={`badge maturity-${level}`}>{t(`content.maturity.${level}`)}</span>;
}

export function MaturityCallout({ level, children }: { level: Maturity; children: React.ReactNode }) {
  const { t } = useTranslation();
  return (
    <aside className={`callout maturity-${level}`} aria-label={t(`content.maturity.${level}`)}>
      <span className="callout-title">{t(`content.maturity.${level}`)}</span>
      {children}
    </aside>
  );
}

export function VendorNote({ name, children }: { name: string; children: React.ReactNode }) {
  const { t } = useTranslation();
  return (
    <aside className="callout vendor" aria-label={t("content.vendor", { name })}>
      <span className="callout-title">{t("content.vendor", { name })}</span>
      {children}
    </aside>
  );
}

export interface DeprecationInfo {
  reason: string;
  replacement?: string | null;
  since: string;
}

export function DeprecationNotice({ deprecation, subject }: { deprecation: DeprecationInfo; subject?: string }) {
  const { t } = useTranslation();
  return (
    <aside className="callout deprecated" role="note">
      <span className="callout-title">
        {t("content.deprecated")}
        {subject ? `: ${subject}` : ""} · {formatDate(deprecation.since)}
      </span>
      <p style={{ margin: 0 }}>{deprecation.reason}</p>
      {deprecation.replacement && <p style={{ margin: 0 }}>{t("content.deprecatedReplacement", { replacement: deprecation.replacement })}</p>}
    </aside>
  );
}

export function ContentMeta({
  version,
  lastReviewed,
  deprecation,
}: {
  version: string;
  lastReviewed: string;
  deprecation?: DeprecationInfo | null;
}) {
  const { t } = useTranslation();
  return (
    <div className="stack">
      <p className="muted" style={{ fontSize: "0.85rem", margin: 0 }}>
        {t("content.version", { version })} · {t("content.lastReviewed", { date: formatDate(lastReviewed) })}
      </p>
      {deprecation && <DeprecationNotice deprecation={deprecation} />}
    </div>
  );
}
