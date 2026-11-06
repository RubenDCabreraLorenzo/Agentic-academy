import { useTranslation } from "react-i18next";

const STEPS = ["study", "check", "build", "inspect"] as const;

export function Methodology() {
  const { t } = useTranslation("marketing");
  return (
    <section aria-labelledby="landing-methodology" className="landing-section">
      <div className="landing-inner stack-lg">
        <h2 id="landing-methodology">{t("methodology.title")}</h2>
        <ol className="plain-list method-steps">
          {STEPS.map((step, index) => (
            <li key={step} className="method-step">
              <span className="method-step-number" aria-hidden="true">
                {index + 1}
              </span>
              <h3>{t(`methodology.steps.${step}.title`)}</h3>
              <p className="muted">{t(`methodology.steps.${step}.body`)}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
