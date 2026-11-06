/** Irreversible path reset with explicit confirmation (FR-043). */
import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { del } from "../../api/client";

export function ResetPathDialog({ pathId, pathTitle }: { pathId: string; pathTitle: string }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await del(`/me/paths/${pathId}/progress`, { confirm: "RESET" });
      setOpen(false);
      setConfirm("");
      await qc.invalidateQueries();
    } catch {
      setError(true);
    }
  };

  return (
    <section aria-labelledby="reset" className="stack">
      <h2 id="reset">{t("dashboard.resetTitle")}</h2>
      {!open ? (
        <button type="button" className="btn secondary" onClick={() => setOpen(true)}>
          {t("dashboard.resetOpen", { path: pathTitle })}
        </button>
      ) : (
        <form className="form card" onSubmit={submit} role="alertdialog" aria-labelledby="reset-warning">
          <p id="reset-warning">{t("dashboard.resetWarning", { path: pathTitle })}</p>
          {error && <p role="alert" className="alert error">{t("states.errorBody")}</p>}
          <label>
            {t("dashboard.resetConfirmLabel")}
            <input type="text" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" />
          </label>
          <div className="row">
            <button type="submit" className="btn danger" disabled={confirm !== "RESET"}>
              {t("dashboard.resetSubmit")}
            </button>
            <button type="button" className="btn secondary" onClick={() => setOpen(false)}>
              {t("dashboard.cancel")}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
