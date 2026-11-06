/** A read-only excerpt of a published recording, in static markup (FR-017). Nothing here runs. */
import { useTranslation } from "react-i18next";

export function LabShowcase() {
  const { t } = useTranslation("marketing");
  const quoted = "excerpts.lab.quoted";
  return (
    <section aria-labelledby="landing-labs" className="landing-section public-showcase public-showcase-lab">
      <div className="landing-inner showcase-layout">
        <div className="stack">
          <h2 id="landing-labs">{t("lab.title")}</h2>
          <p className="muted">{t("lab.intro")}</p>
          <p>
            <strong>{t("lab.disclosure")}</strong>
          </p>
          <p className="muted">{t("lab.practice")}</p>
        </div>
        <figure className="showcase-panel stack">
          <h3>{t(`${quoted}.title`)}</h3>
          <ol className="plain-list trace-excerpt">
            <li>
              <span className="trace-excerpt-label">{t("lab.task")}</span>
              <p>{t(`${quoted}.task`)}</p>
            </li>
            <li>
              <span className="trace-excerpt-label">{t("lab.toolCall")}</span>
              <p>
                <code>{t(`${quoted}.tool`)}</code> <code>{t(`${quoted}.argument`)}</code>
              </p>
              <p className="muted text-small">
                {t("lab.permission")}: <code>{t(`${quoted}.permission`)}</code>
              </p>
            </li>
            <li>
              <span className="trace-excerpt-label">{t("lab.explanation")}</span>
              <p>{t(`${quoted}.explanation`)}</p>
            </li>
            <li>
              <span className="trace-excerpt-label">{t("lab.approval")}</span>
              <p>{t(`${quoted}.approval`)}</p>
            </li>
          </ol>
          <figcaption className="muted text-small">{t("lab.caption")}</figcaption>
        </figure>
      </div>
    </section>
  );
}
