import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { post } from "../api/client";
import { OfflineBanner } from "../components/states";
import { Alert } from "../components/ui/Alert";
import { Button, LinkButton } from "../components/ui/Button";
import { useAuthExpiryListener, useMe } from "./session";

export function Layout() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [expired, setExpired] = useState(false);

  useAuthExpiryListener(
    useCallback(() => {
      setExpired(true);
    }, []),
  );

  const signOut = async () => {
    try {
      await post("/auth/sign-out");
    } finally {
      qc.clear();
      navigate("/");
    }
  };

  return (
    <>
      <a className="skip-link" href="#main">
        {t("app.skipToContent")}
      </a>
      <header className="app-header">
        <nav aria-label={t("ui.mainNav")} className="app-nav">
          <Link to="/" className="app-brand">
            {t("app.name")}
          </Link>
          <NavLink to="/" end className="app-nav-link">
            {t("app.nav.catalog")}
          </NavLink>
          {me ? (
            <>
              <NavLink to="/dashboard" className="app-nav-link">
                {t("app.nav.dashboard")}
              </NavLink>
              <NavLink to="/account" className="app-nav-link">
                {t("app.nav.account")}
              </NavLink>
              <Button variant="ghost" onClick={signOut}>
                {t("app.nav.signOut")}
              </Button>
            </>
          ) : (
            <>
              <NavLink to="/sign-in" className="app-nav-link">
                {t("app.nav.signIn")}
              </NavLink>
              <NavLink to="/sign-up" className="app-nav-link">
                {t("app.nav.signUp")}
              </NavLink>
            </>
          )}
        </nav>
      </header>
      <main id="main" tabIndex={-1} className="stack">
        <OfflineBanner />
        {expired && !me && (
          <Alert tone="warning" role="alert">
            <div className="stack">
              <p>{t("auth.reauth")}</p>
              <LinkButton
                variant="secondary"
                to={`/sign-in?next=${encodeURIComponent(location.pathname)}`}
                onClick={() => setExpired(false)}
              >
                {t("app.nav.signIn")}
              </LinkButton>
            </div>
          </Alert>
        )}
        <Outlet />
      </main>
      <footer className="app-footer">{t("app.footer")}</footer>
    </>
  );
}
