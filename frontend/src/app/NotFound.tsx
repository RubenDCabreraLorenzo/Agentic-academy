import { useTranslation } from "react-i18next";
import { Link } from "react-router";

export function NotFound() {
  const { t } = useTranslation();
  return (
    <section className="stack">
      <h1>{t("states.notFound")}</h1>
      <Link to="/">{t("app.nav.catalog")}</Link>
    </section>
  );
}
