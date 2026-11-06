/** The route table (routes contract). Every page is code-split, so that the landing page stays small. */
import type { ComponentType } from "react";
import { matchPath } from "react-router";

export type Shell = "public" | "learning" | "session";

export interface RouteDef {
  path: string;
  auth: boolean;
  /** `session` follows the visitor's session; see `ShellLayout`. */
  shell: Shell;
  /** Generic title, used until a page with a content title has its data. */
  titleKey: string;
  load: () => Promise<{ default: ComponentType }>;
}

type AuthPages = typeof import("../features/auth/pages");
const authPage = (name: keyof AuthPages) => () => import("../features/auth/pages").then((m) => ({ default: m[name] }));
const catalog = () => import("../features/catalog/CatalogPage");

export const routes: RouteDef[] = [
  // Renders the catalog until the landing page exists (T075).
  { path: "/", auth: false, shell: "session", titleKey: "meta.landing.title", load: catalog },
  { path: "/curriculum", auth: false, shell: "session", titleKey: "meta.curriculum.title", load: catalog },
  { path: "/paths/:pathId", auth: false, shell: "session", titleKey: "meta.path.title", load: () => import("../features/catalog/PathPage") },
  { path: "/sign-in", auth: false, shell: "public", titleKey: "meta.signIn.title", load: authPage("SignInPage") },
  { path: "/register", auth: false, shell: "public", titleKey: "meta.register.title", load: authPage("SignUpPage") },
  { path: "/check-email", auth: false, shell: "public", titleKey: "meta.checkEmail.title", load: authPage("CheckEmailPage") },
  { path: "/forgot-password", auth: false, shell: "public", titleKey: "meta.forgotPassword.title", load: authPage("ForgotPasswordPage") },
  // Frozen: the backend builds these two addresses into emails.
  { path: "/verify-email", auth: false, shell: "public", titleKey: "meta.verifyEmail.title", load: authPage("VerifyEmailPage") },
  { path: "/reset-password", auth: false, shell: "public", titleKey: "meta.resetPassword.title", load: authPage("ResetPasswordPage") },
  { path: "/dashboard", auth: true, shell: "learning", titleKey: "meta.dashboard.title", load: () => import("../features/dashboard/DashboardPage") },
  { path: "/dashboard/competencies", auth: true, shell: "learning", titleKey: "meta.competencies.title", load: () => import("../features/dashboard/CompetenciesPage") },
  { path: "/account", auth: true, shell: "learning", titleKey: "meta.account.title", load: authPage("AccountPage") },
  { path: "/modules/:moduleId", auth: true, shell: "learning", titleKey: "meta.module.title", load: () => import("../features/module/ModulePage") },
  { path: "/knowledge-checks/:checkId", auth: true, shell: "learning", titleKey: "meta.knowledgeCheck.title", load: () => import("../features/knowledge-check/KnowledgeCheckPage") },
  { path: "/challenges/:challengeId", auth: true, shell: "learning", titleKey: "meta.challenge.title", load: () => import("../features/challenge/ChallengePage") },
  { path: "/lab/:scenarioId", auth: true, shell: "learning", titleKey: "meta.lab.title", load: () => import("../features/lab/LabPage") },
];

/** Old addresses that keep working. They have no shell or title of their own. */
export const redirects = [{ from: "/sign-up", to: "/register" }];

export function shellFor(pathname: string): Shell {
  return routes.find((r) => matchPath(r.path, pathname))?.shell ?? "session";
}
