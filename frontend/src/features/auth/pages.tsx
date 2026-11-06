/** Sign up, verify, sign in, password reset and account pages (FR-045a). */
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router";
import { ApiError, del, post, type Schemas } from "../../api/client";
import { useMe } from "../../app/session";
import { Loading } from "../../components/states";
import { Alert } from "../../components/ui/Alert";
import { Button, LinkButton } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";

function useErrorMessage() {
  const { t } = useTranslation();
  return (e: unknown) => {
    if (e instanceof ApiError) {
      const key = `auth.errors.${e.code}`;
      const msg = t(key);
      return msg === key ? t("auth.errors.generic") : msg;
    }
    return t("auth.errors.generic");
  };
}

function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <Alert tone="danger" role="alert">
      {message}
    </Alert>
  );
}

function SignedInNotice({ title }: { title: string }) {
  const { t } = useTranslation();
  return (
    <section className="stack reading">
      <h1>{title}</h1>
      <Alert tone="info" role="status">
        <div className="stack">
          <p>{t("auth.alreadySignedIn")}</p>
          <LinkButton to="/dashboard">{t("auth.goToProgress")}</LinkButton>
        </div>
      </Alert>
    </section>
  );
}

function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";
}

export function SignUpPage() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const navigate = useNavigate();
  const toMessage = useErrorMessage();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email"));
    setBusy(true);
    setError(null);
    try {
      await post("/auth/sign-up", { email, password: String(form.get("password")) });
      navigate(`/check-email?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (me) return <SignedInNotice title={t("auth.signUpTitle")} />;

  return (
    <section className="stack">
      <h1>{t("auth.signUpTitle")}</h1>
      <form className="form" onSubmit={submit} noValidate={false}>
        <FormError message={error} />
        <Field label={t("auth.email")} name="email" type="email" autoComplete="email" required />
        <Field
          label={t("auth.password")}
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          required
          hint={t("auth.passwordHint")}
        />
        <Button type="submit" disabled={busy}>
          {t("auth.signUpSubmit")}
        </Button>
        <p>
          {t("auth.haveAccount")} <Link to="/sign-in">{t("auth.signInSubmit")}</Link>
        </p>
      </form>
    </section>
  );
}

export function CheckEmailPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  return (
    <section className="stack reading">
      <h1>{t("auth.checkEmailTitle")}</h1>
      <p>{t("auth.checkEmailBody", { email: params.get("email") ?? "" })}</p>
      <Link to="/sign-in">{t("auth.signInSubmit")}</Link>
    </section>
  );
}

export function VerifyEmailPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const toMessage = useErrorMessage();
  const [state, setState] = useState<"pending" | "done" | string>("pending");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    post("/auth/verify-email", { token: params.get("token") ?? "" })
      .then(() => setState("done"))
      .catch((e: unknown) => setState(toMessage(e)));
  }, [params, toMessage]);

  return (
    <section className="stack reading">
      <h1>{t("auth.verifyTitle")}</h1>
      {state === "pending" && <Loading />}
      {state === "done" && (
        <Alert tone="success" role="status">
          <div className="stack">
            <p>{t("auth.verified")}</p>
            <LinkButton to="/sign-in">{t("auth.signInSubmit")}</LinkButton>
          </div>
        </Alert>
      )}
      {state !== "pending" && state !== "done" && <FormError message={state} />}
    </section>
  );
}

export function SignInPage() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [params] = useSearchParams();
  const toMessage = useErrorMessage();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const me = await post<Schemas["Me"]>("/auth/sign-in", {
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      qc.setQueryData(["me"], me);
      await qc.invalidateQueries();
      navigate(safeNext(params.get("next")), { replace: true });
    } catch (err) {
      setError(toMessage(err));
      setBusy(false); // On success it stays busy, so that the signed-in notice does not flash before the page changes.
    }
  };

  if (me && !busy) return <SignedInNotice title={t("auth.signInTitle")} />;

  return (
    <section className="stack">
      <h1>{t("auth.signInTitle")}</h1>
      <form className="form" onSubmit={submit}>
        <FormError message={error} />
        <Field label={t("auth.email")} name="email" type="email" autoComplete="email" required />
        <Field label={t("auth.password")} name="password" type="password" autoComplete="current-password" required />
        <Button type="submit" disabled={busy}>
          {t("auth.signInSubmit")}
        </Button>
        <p>
          <Link to="/forgot-password">{t("auth.forgot")}</Link>
        </p>
        <p>
          {t("auth.noAccount")} <Link to="/register">{t("auth.signUpSubmit")}</Link>
        </p>
      </form>
    </section>
  );
}

export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const toMessage = useErrorMessage();
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await post("/auth/password-reset/request", { email: String(new FormData(e.currentTarget).get("email")) });
      setSent(true);
    } catch (err) {
      setError(toMessage(err));
    }
  };

  return (
    <section className="stack">
      <h1>{t("auth.forgotTitle")}</h1>
      {sent ? (
        <Alert tone="success" role="status">
          {t("auth.forgotSent")}
        </Alert>
      ) : (
        <form className="form" onSubmit={submit}>
          <FormError message={error} />
          <Field label={t("auth.email")} name="email" type="email" autoComplete="email" required />
          <Button type="submit">{t("auth.forgotSubmit")}</Button>
        </form>
      )}
    </section>
  );
}

export function ResetPasswordPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const toMessage = useErrorMessage();
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await post("/auth/password-reset/confirm", {
        token: params.get("token") ?? "",
        new_password: String(new FormData(e.currentTarget).get("password")),
      });
      setDone(true);
    } catch (err) {
      setError(toMessage(err));
    }
  };

  return (
    <section className="stack">
      <h1>{t("auth.resetTitle")}</h1>
      {done ? (
        <Alert tone="success" role="status">
          <div className="stack">
            <p>{t("auth.resetDone")}</p>
            <LinkButton to="/sign-in">{t("auth.signInSubmit")}</LinkButton>
          </div>
        </Alert>
      ) : (
        <form className="form" onSubmit={submit}>
          <FormError message={error} />
          <Field
            label={t("auth.newPassword")}
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            required
            hint={t("auth.passwordHint")}
          />
          <Button type="submit">{t("auth.resetSubmit")}</Button>
        </form>
      )}
    </section>
  );
}

export function AccountPage() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const toMessage = useErrorMessage();
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const remove = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await del("/me", { confirm: "DELETE" });
      qc.clear();
      qc.setQueryData(["me"], null);
      navigate("/", { replace: true });
    } catch (err) {
      setError(toMessage(err));
    }
  };

  return (
    <section className="stack-lg reading">
      <div className="stack">
        <h1>{t("auth.accountTitle")}</h1>
        {me && <p>{t("auth.signedInAs", { email: me.email })}</p>}
      </div>
      <div className="stack">
        <h2>{t("auth.deleteTitle")}</h2>
        <p>{t("auth.deleteBody")}</p>
        <form className="form" onSubmit={remove}>
          <FormError message={error} />
          <Field label={t("auth.deleteConfirmLabel")} type="text" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" />
          <Button variant="danger" type="submit" disabled={confirm !== "DELETE"}>
            {t("auth.deleteSubmit")}
          </Button>
        </form>
      </div>
    </section>
  );
}
