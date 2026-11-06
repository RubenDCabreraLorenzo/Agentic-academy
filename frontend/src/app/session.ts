/** Current learner and platform status hooks. */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { ApiError, AUTH_REQUIRED_EVENT, get, type Schemas } from "../api/client";

export type Me = Schemas["Me"];

export function useMe() {
  return useQuery<Me | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await get<Me>("/me");
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
    retry: false,
  });
}

export interface Health {
  database: "ok" | "unavailable";
  content_bundle_version: string | null;
  evaluation: "available" | "unavailable";
  challenges_enabled: boolean;
}

export function useHealth() {
  return useQuery<Health>({ queryKey: ["health"], queryFn: () => get<Health>("/health"), staleTime: 15_000 });
}

/** When any request returns 401, forget the cached learner so the UI asks to sign in again. */
export function useAuthExpiryListener(onExpired: () => void) {
  const qc = useQueryClient();
  useEffect(() => {
    const handler = (event: Event) => {
      const path = (event as CustomEvent<{ path: string }>).detail?.path ?? "";
      if (path === "/me") return;
      const had = qc.getQueryData<Me | null>(["me"]);
      qc.setQueryData(["me"], null);
      if (had) onExpired();
    };
    window.addEventListener(AUTH_REQUIRED_EVENT, handler);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, handler);
  }, [qc, onExpired]);
}
