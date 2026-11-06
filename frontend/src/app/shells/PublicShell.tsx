/** Public shell's navigation. Its footer is in `PublicFooter`. */
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

export function PublicNav() {
  const { t } = useTranslation();
  return (
    <>
      <NavLink to="/curriculum" className="app-nav-link">
        {t("app.nav.catalog")}
      </NavLink>
      <NavLink to="/sign-in" className="app-nav-link">
        {t("app.nav.signIn")}
      </NavLink>
      <NavLink to="/register" className="app-nav-link">
        {t("app.nav.signUp")}
      </NavLink>
    </>
  );
}
