import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useMe } from "../../app/session";
import { LandingActions } from "./Hero";

export function ClosingAction() {
  const { t } = useTranslation("marketing");
  const { data: me, isLoading } = useMe();
  return (
    <section aria-labelledby="landing-closing" className="landing-section landing-closing">
      <div className="landing-inner stack">
        <h2 id="landing-closing">{t("closing.title")}</h2>
        <p className="measure">{t("closing.body")}</p>
        <LandingActions />
        {!me && !isLoading && (
          <p className="muted">
            {t("actions.haveAccount")} <Link to="/sign-in">{t("actions.signIn")}</Link>
          </p>
        )}
      </div>
    </section>
  );
}
