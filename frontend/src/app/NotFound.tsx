import { useTranslation } from "react-i18next";
import { Link } from "react-router";

export function NotFound() {
  const { t } = useTranslation();
  return (
    <section className="stack">
      <h1>{t("states.notFound")}</h1>
      <p className="row">
        <Link to="/">{t("states.notFoundHome")}</Link>
        <Link to="/curriculum">{t("app.nav.catalog")}</Link>
      </p>
    </section>
  );
}
