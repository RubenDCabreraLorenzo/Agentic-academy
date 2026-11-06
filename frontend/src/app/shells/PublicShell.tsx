/** Public shell: the contents of `AppFrame`'s slots. T078 adds the legal links to the footer. */
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

export function PublicFooter() {
  const { t } = useTranslation();
  return <>{t("app.footer")}</>;
}
