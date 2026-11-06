/** A read-only excerpt of a published challenge, in static markup (FR-017). It shows no results. */
import { useTranslation } from "react-i18next";

export function ChallengeShowcase() {
  const { t } = useTranslation("marketing");
  const criteria = t("excerpts.challenge.quoted.criteria", { returnObjects: true }) as unknown as string[];
  return (
    <section aria-labelledby="landing-challenges" className="landing-section public-showcase">
      <div className="landing-inner showcase-layout">
        <div className="stack">
          <h2 id="landing-challenges">{t("challenges.title")}</h2>
          <p className="muted">{t("challenges.intro")}</p>
        </div>
        <figure className="showcase-panel stack">
          <h3>{t("excerpts.challenge.quoted.title")}</h3>
          <div className="stack">
            <h4>{t("challenges.criteria")}</h4>
            <ul className="stack">
              {criteria.map((criterion) => (
                <li key={criterion}>{criterion}</li>
              ))}
            </ul>
          </div>
          <div className="stack">
            <h4>{t("challenges.code")}</h4>
            <pre className="showcase-code">
              <code>{t("excerpts.challenge.quoted.code")}</code>
            </pre>
          </div>
          <figcaption className="muted text-small">{t("challenges.caption")}</figcaption>
        </figure>
      </div>
    </section>
  );
}
