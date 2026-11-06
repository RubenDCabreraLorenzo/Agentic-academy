/** Shared loading, empty, error and offline states (FR-052). */
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export function Loading({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <p role="status" aria-live="polite" className="muted">
      {label ?? t("states.loading")}
    </p>
  );
}

export function EmptyState({ children }: { children?: React.ReactNode }) {
  const { t } = useTranslation();
  return <p className="muted">{children ?? t("states.empty")}</p>;
}

export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div role="alert" className="alert error stack">
      <strong>{title ?? t("states.errorTitle")}</strong>
      <p>{message ?? t("states.errorBody")}</p>
      {onRetry && (
        <button type="button" className="btn secondary" onClick={onRetry}>
          {t("states.retry")}
        </button>
      )}
    </div>
  );
}

export function useOnline(): boolean {
  const [online, setOnline] = useState(() => (typeof navigator === "undefined" ? true : navigator.onLine));
  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);
  return online;
}

export function OfflineBanner() {
  const { t } = useTranslation();
  const online = useOnline();
  if (online) return null;
  return (
    <div role="status" className="alert warning">
      {t("states.offline")}
    </div>
  );
}
