import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router";
import { Loading } from "../components/states";
import { ErrorBoundary } from "./ErrorBoundary";
import { usePageMeta } from "./navigation/usePageMeta";
import { NotFound } from "./NotFound";
import { RequireAuth } from "./RequireAuth";
import { redirects, routes, shellFor } from "./routes";
import { useMe } from "./session";
import { AppFrame } from "./shells/AppFrame";
import { LearningFooter, LearningNav } from "./shells/LearningShell";
import { PublicFooter, PublicNav } from "./shells/PublicShell";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const lazyRoutes = routes.map((r) => ({ ...r, Component: lazy(r.load) }));

/** Which shell to show. While the session is unknown, session-dependent navigation stays empty. */
function ShellLayout() {
  const { pathname } = useLocation();
  const { data: me, isLoading } = useMe();
  const shell = shellFor(pathname);
  const active = shell === "public" ? "public" : isLoading ? null : me ? "learning" : shell === "session" ? "public" : null;
  return (
    <AppFrame
      nav={active === "learning" ? <LearningNav /> : active === "public" ? <PublicNav /> : null}
      footer={active === "learning" ? <LearningFooter /> : active === "public" ? <PublicFooter /> : null}
    >
      <Outlet />
    </AppFrame>
  );
}

/**
 * The generic title and description. It comes before the page, because effects run in tree order and a
 * page with a content title must have the last word. Outside `Suspense`, so that it applies while a
 * page's code loads.
 */
function RouteMeta({ titleKey }: { titleKey: string }) {
  const { t, i18n } = useTranslation();
  const descriptionKey = titleKey.replace(/\.title$/, ".description");
  usePageMeta({
    title: t(titleKey),
    description: t(i18n.exists(descriptionKey) ? descriptionKey : "meta.default.description"),
  });
  return null;
}

function RoutePage({ titleKey, auth, children }: { titleKey: string; auth: boolean; children: ReactNode }) {
  return (
    <>
      <RouteMeta titleKey={titleKey} />
      <Suspense fallback={<Loading />}>{auth ? <RequireAuth>{children}</RequireAuth> : children}</Suspense>
    </>
  );
}

function RedirectKeepingQuery({ to }: { to: string }) {
  const { search } = useLocation();
  return <Navigate to={{ pathname: to, search }} replace />;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Routes>
            {redirects.map(({ from, to }) => (
              <Route key={from} path={from} element={<RedirectKeepingQuery to={to} />} />
            ))}
            <Route element={<ShellLayout />}>
              {lazyRoutes.map(({ path, auth, titleKey, Component }) => (
                <Route
                  key={path}
                  path={path}
                  element={
                    <RoutePage titleKey={titleKey} auth={auth}>
                      <Component />
                    </RoutePage>
                  }
                />
              ))}
              <Route
                path="*"
                element={
                  <RoutePage titleKey="states.notFound" auth={false}>
                    <NotFound />
                  </RoutePage>
                }
              />
            </Route>
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
