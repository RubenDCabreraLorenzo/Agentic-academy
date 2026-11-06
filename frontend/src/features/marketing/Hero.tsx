import { useTranslation } from "react-i18next";
import { useMe } from "../../app/session";
import { LinkButton } from "../../components/ui/Button";

/** The two actions, by audience (public content contract). A failed session check offers the visitor's. */
export function LandingActions() {
  const { t } = useTranslation("marketing");
  const { data: me, isLoading } = useMe();
  return (
    <div className="row landing-actions">
      {isLoading ? (
        // Holds the space, so that a signed-in learner does not see "Create account" flash.
        <span className="btn btn-primary landing-action-pending" aria-hidden="true">
          {t("actions.register")}
        </span>
      ) : (
        <LinkButton to={me ? "/dashboard" : "/register"}>{t(me ? "actions.progress" : "actions.register")}</LinkButton>
      )}
      <LinkButton variant="secondary" to="/curriculum">
        {t("actions.explore")}
      </LinkButton>
    </div>
  );
}

export function Hero() {
  const { t } = useTranslation("marketing");
  return (
    <section className="public-hero">
      <div className="landing-inner">
        <div className="public-hero-copy">
          <h1>{t("hero.title")}</h1>
          <p className="public-hero-summary">{t("hero.summary")}</p>
          <LandingActions />
        </div>
      </div>
    </section>
  );
}
