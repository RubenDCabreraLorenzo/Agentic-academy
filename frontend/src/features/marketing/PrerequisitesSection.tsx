import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { Loading } from "../../components/states";
import { availablePaths, useCatalog, usePathDetail } from "./queries";

function Body() {
  const { t } = useTranslation("marketing");
  const catalog = useCatalog();
  const first = availablePaths(catalog.data)[0];
  const q = usePathDetail(first?.id);

  if (catalog.isLoading || q.isLoading) return <Loading />;
  if (catalog.isError) {
    return (
      <p>
        <Link to="/curriculum">{t("actions.explore")}</Link>
      </p>
    );
  }
  if (!first) return <p className="muted">{t("prerequisites.empty")}</p>;

  const pathLink = (
    <p>
      <Link to={`/paths/${first.id}`}>{t("prerequisites.viewPath")}</Link>
    </p>
  );
  if (q.isError || !q.data) return pathLink;
  return (
    <>
      <ul className="measure">
        {q.data.entry_prerequisites.map((p) => (
          <li key={p.label}>
            <a href={p.resource_url} target="_blank" rel="noopener noreferrer">
              {p.label}
            </a>
          </li>
        ))}
      </ul>
      {pathLink}
    </>
  );
}

export function PrerequisitesSection() {
  const { t } = useTranslation("marketing");
  return (
    <section aria-labelledby="landing-prerequisites" className="landing-section landing-section-raised">
      <div className="landing-inner stack-lg">
        <div className="stack">
          <h2 id="landing-prerequisites">{t("prerequisites.title")}</h2>
          <p className="measure muted">{t("prerequisites.intro")}</p>
        </div>
        <div className="stack">
          <Body />
        </div>
      </div>
    </section>
  );
}
