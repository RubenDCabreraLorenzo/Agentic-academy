import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { post } from "../api/client";
import { OfflineBanner } from "../components/states";
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
        <nav aria-label="Main">
          <Link to="/" className="brand">
            {t("app.name")}
          </Link>
          <NavLink to="/" end className="nav-link">
            {t("app.nav.catalog")}
          </NavLink>
          {me ? (
            <>
              <NavLink to="/dashboard" className="nav-link">
                {t("app.nav.dashboard")}
              </NavLink>
              <NavLink to="/account" className="nav-link">
                {t("app.nav.account")}
              </NavLink>
              <button type="button" className="linklike" onClick={signOut}>
                {t("app.nav.signOut")}
              </button>
            </>
          ) : (
            <>
              <NavLink to="/sign-in" className="nav-link">
                {t("app.nav.signIn")}
              </NavLink>
              <NavLink to="/sign-up" className="nav-link">
                {t("app.nav.signUp")}
              </NavLink>
            </>
          )}
        </nav>
      </header>
      <main id="main" tabIndex={-1}>
        <OfflineBanner />
        {expired && !me && (
          <div role="alert" className="alert warning stack">
            <p style={{ margin: 0 }}>{t("auth.reauth")}</p>
            <Link
              className="btn secondary"
              to={`/sign-in?next=${encodeURIComponent(location.pathname)}`}
              onClick={() => setExpired(false)}
            >
              {t("app.nav.signIn")}
            </Link>
          </div>
        )}
        <Outlet />
      </main>
      <footer className="app-footer">{t("app.footer")}</footer>
    </>
  );
}
