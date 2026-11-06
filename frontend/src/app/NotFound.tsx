import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { usePageMeta } from "./navigation/usePageMeta";

export function NotFound() {
  const { t } = useTranslation();
  usePageMeta({ title: t("states.notFound") });
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
