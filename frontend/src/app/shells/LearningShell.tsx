/** Learning shell: the contents of `AppFrame`'s slots. No marketing content here (FR-024). */
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { NavLink, useNavigate } from "react-router";
import { post } from "../../api/client";
import { Button } from "../../components/ui/Button";

export function LearningNav() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const navigate = useNavigate();

  const signOut = async () => {
    try {
      await post("/auth/sign-out");
    } finally {
      qc.clear();
      // Known rather than cleared, so that the navigation does not go through its "unknown" state.
      qc.setQueryData(["me"], null);
      navigate("/");
    }
  };

  return (
    <>
      <NavLink to="/dashboard" className="app-nav-link">
        {t("app.nav.dashboard")}
      </NavLink>
      <NavLink to="/curriculum" className="app-nav-link">
        {t("app.nav.catalog")}
      </NavLink>
      <NavLink to="/account" className="app-nav-link">
        {t("app.nav.account")}
      </NavLink>
      <Button variant="ghost" onClick={signOut}>
        {t("app.nav.signOut")}
      </Button>
    </>
  );
}

export function LearningFooter() {
  const { t } = useTranslation();
  return <>{t("app.name")}</>;
}
