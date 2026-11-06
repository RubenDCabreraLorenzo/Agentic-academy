import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { LegalLinks, PublisherDetails } from "./LegalLinks";

export function PublicFooter() {
  const { t } = useTranslation();
  return (
    <div className="footer-layout">
      <div>
        <p className="footer-product">{t("app.name")}</p>
        <p>{t("app.footer")}</p>
        <PublisherDetails />
      </div>
      <nav aria-label={t("ui.footerNav")} className="footer-links">
        <Link to="/curriculum">{t("app.nav.catalog")}</Link>
        <Link to="/register">{t("app.nav.signUp")}</Link>
        <Link to="/sign-in">{t("app.nav.signIn")}</Link>
        <LegalLinks />
      </nav>
    </div>
  );
}
