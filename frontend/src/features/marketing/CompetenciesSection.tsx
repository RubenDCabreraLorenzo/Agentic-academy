import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { Loading } from "../../components/states";
import { availablePaths, useCatalog } from "./queries";

export function CompetenciesSection() {
  const { t } = useTranslation("marketing");
  const q = useCatalog();
  const competencies = [...new Map(availablePaths(q.data).flatMap((p) => p.competencies).map((c) => [c.id, c])).values()];

  return (
    <section aria-labelledby="landing-competencies" className="landing-section">
      <div className="landing-inner stack-lg">
        <div className="stack">
          <h2 id="landing-competencies">{t("competencies.title")}</h2>
          <p className="measure muted">{t("competencies.intro")}</p>
        </div>
        {q.isLoading ? (
          <Loading />
        ) : q.isError ? (
          <p>
            <Link to="/curriculum">{t("actions.explore")}</Link>
          </p>
        ) : competencies.length === 0 ? (
          <p className="muted">{t("competencies.empty")}</p>
        ) : (
          <ul className="plain-list competency-list">
            {competencies.map((c) => (
              <li key={c.id}>{c.title}</li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
