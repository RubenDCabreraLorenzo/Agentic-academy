/** Where the page sits in the curriculum. The last item is the current page when it has no link. */
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

export function Breadcrumb({ items }: { items: { label: string; to?: string }[] }) {
  const { t } = useTranslation();
  return (
    <nav aria-label={t("ui.breadcrumb")} className="breadcrumb">
      <ol>
        {items.map((item) => (
          <li key={item.label}>{item.to ? <Link to={item.to}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}</li>
        ))}
      </ol>
    </nav>
  );
}
