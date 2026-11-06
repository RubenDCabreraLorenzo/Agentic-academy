/**
 * What every shell shares (FR-039; routes contract). It stays mounted when the shell changes, so that
 * route focus and the session-expiry warning survive the move from a learning page to sign-in.
 */
import { useCallback, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router";
import { OfflineBanner } from "../../components/states";
import { Alert } from "../../components/ui/Alert";
import { LinkButton } from "../../components/ui/Button";
import { ErrorBoundary } from "../ErrorBoundary";
import { RouteFocus } from "../navigation/RouteFocus";
import { useAuthExpiryListener, useMe } from "../session";

export function AppFrame({ nav, footer, children }: { nav: ReactNode; footer: ReactNode; children: ReactNode }) {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const { pathname } = useLocation();
  const [expired, setExpired] = useState(false);

  useAuthExpiryListener(
    useCallback(() => {
      setExpired(true);
    }, []),
  );

  return (
    <>
      <RouteFocus />
      <a className="skip-link" href="#main">
        {t("app.skipToContent")}
      </a>
      <header className="app-header">
        <nav aria-label={t("ui.mainNav")} className="app-nav">
          <Link to="/" className="app-brand">
            {t("app.name")}
          </Link>
          {nav}
        </nav>
      </header>
      <main id="main" tabIndex={-1} className="stack">
        <OfflineBanner />
        {expired && !me && (
          <Alert tone="warning" role="alert">
            <div className="stack">
              <p>{t("auth.reauth")}</p>
              <LinkButton variant="secondary" to={`/sign-in?next=${encodeURIComponent(pathname)}`} onClick={() => setExpired(false)}>
                {t("app.nav.signIn")}
              </LinkButton>
            </div>
          </Alert>
        )}
        {/* Keyed, so that leaving a page that failed clears the error. */}
        <ErrorBoundary key={pathname}>{children}</ErrorBoundary>
      </main>
      <footer className="app-footer">{footer}</footer>
    </>
  );
}
