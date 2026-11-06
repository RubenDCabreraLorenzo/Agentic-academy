/** Irreversible path reset with explicit confirmation (FR-043). */
import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { del } from "../../api/client";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Field } from "../../components/ui/Field";

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
        <Button variant="secondary" onClick={() => setOpen(true)}>
          {t("dashboard.resetOpen", { path: pathTitle })}
        </Button>
      ) : (
        <Card as="form" className="form" onSubmit={submit} role="alertdialog" aria-labelledby="reset-warning">
          <p id="reset-warning">{t("dashboard.resetWarning", { path: pathTitle })}</p>
          {error && (
            <Alert tone="danger" role="alert">
              {t("states.errorBody")}
            </Alert>
          )}
          <Field label={t("dashboard.resetConfirmLabel")} type="text" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" />
          <div className="row">
            <Button variant="danger" type="submit" disabled={confirm !== "RESET"}>
              {t("dashboard.resetSubmit")}
            </Button>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              {t("dashboard.cancel")}
            </Button>
          </div>
        </Card>
      )}
    </section>
  );
}
