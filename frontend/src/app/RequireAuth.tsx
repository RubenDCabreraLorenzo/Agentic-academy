import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { Loading } from "../components/states";
import { useMe } from "./session";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { data: me, isLoading } = useMe();
  const location = useLocation();
  if (isLoading) return <Loading />;
  if (!me) return <Navigate to={`/sign-in?next=${encodeURIComponent(location.pathname)}`} replace />;
  return <>{children}</>;
}
