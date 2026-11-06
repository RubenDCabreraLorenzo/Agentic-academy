import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router";
import { Loading } from "../components/states";
import {
  AccountPage,
  CheckEmailPage,
  ForgotPasswordPage,
  ResetPasswordPage,
  SignInPage,
  SignUpPage,
  VerifyEmailPage,
} from "../features/auth/pages";
import { ErrorBoundary } from "./ErrorBoundary";
import { Layout } from "./Layout";
import { NotFound } from "./NotFound";
import { RequireAuth } from "./RequireAuth";
import { routes } from "./routes";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const lazyRoutes = routes.map((r) => ({ ...r, Component: lazy(r.load) }));

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Suspense fallback={<Loading />}>
            <Routes>
              <Route element={<Layout />}>
                {lazyRoutes.map(({ path, auth, Component }) => (
                  <Route
                    key={path}
                    path={path}
                    element={auth ? <RequireAuth><Component /></RequireAuth> : <Component />}
                  />
                ))}
                <Route path="/sign-in" element={<SignInPage />} />
                <Route path="/sign-up" element={<SignUpPage />} />
                <Route path="/check-email" element={<CheckEmailPage />} />
                <Route path="/verify-email" element={<VerifyEmailPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/account" element={<RequireAuth><AccountPage /></RequireAuth>} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
