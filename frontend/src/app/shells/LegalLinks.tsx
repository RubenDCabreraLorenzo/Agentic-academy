/** Links and details that exist only once the owner supplies them (FR-022, FR-022a). */
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { legal } from "../../features/legal/availability";

export function LegalLinks() {
  const { t } = useTranslation();
  const { privacy, terms, publisher } = legal;
  return (
    <>
      {privacy && <Link to="/privacy">{t("legal.privacy")}</Link>}
      {terms && <Link to="/terms">{t("legal.terms")}</Link>}
      {publisher && <a href={`mailto:${publisher.contact_email}`}>{t("legal.contact")}</a>}
    </>
  );
}

export function PublisherDetails() {
  const { publisher } = legal;
  if (!publisher) return null;
  return <p>{[publisher.name, publisher.address, publisher.registration].filter(Boolean).join(" · ")}</p>;
}
