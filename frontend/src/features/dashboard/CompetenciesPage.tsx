/** Competency view with level, status and evidence (FR-039, FR-041). */
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { get } from "../../api/client";
import { ErrorState, Loading } from "../../components/states";
import { formatDate } from "../../i18n";
import type { CompetencyRow } from "./types";

export default function CompetenciesPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const pathId = params.get("path");
  const q = useQuery({
    queryKey: ["competencies", pathId],
    queryFn: () => get<CompetencyRow[]>(`/me/competencies${pathId ? `?pathId=${encodeURIComponent(pathId)}` : ""}`),
  });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  return (
    <section className="stack">
      <p>
        <Link to="/dashboard">{t("dashboard.back")}</Link>
      </p>
      <h1>{t("dashboard.competencyTitle")}</h1>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th scope="col" style={{ textAlign: "left" }}>{t("dashboard.colCompetency")}</th>
              <th scope="col" style={{ textAlign: "left" }}>{t("dashboard.colLevel")}</th>
              <th scope="col" style={{ textAlign: "left" }}>{t("dashboard.colStatus")}</th>
              <th scope="col" style={{ textAlign: "left" }}>{t("dashboard.colEvidence")}</th>
            </tr>
          </thead>
          <tbody>
            {q.data.map((c) => (
              <tr key={c.id} style={{ borderTop: "1px solid var(--border)" }}>
                <th scope="row" style={{ textAlign: "left", fontWeight: 600, padding: "8px 8px 8px 0" }}>
                  {c.title}
                  <div className="muted" style={{ fontWeight: 400 }}>{c.description}</div>
                </th>
                <td>{t(`catalog.level.${c.level}`)}</td>
                <td>
                  <span className={c.status === "demonstrated" ? "badge success" : c.status === "in_progress" ? "badge warning" : "badge"}>
                    {t(`dashboard.status.${c.status}`)}
                  </span>
                  {c.demonstrated_at && <div className="muted">{formatDate(c.demonstrated_at)}</div>}
                </td>
                <td>
                  <ul style={{ margin: 0, paddingLeft: 16 }}>
                    {c.evidence.map((e) => (
                      <li key={`${e.type}-${e.id}`}>
                        <Link to={e.type === "challenge" ? `/challenges/${e.id}` : `/knowledge-checks/${e.id}`}>
                          {t(`dashboard.evidence.${e.type}`, { version: e.version })}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
