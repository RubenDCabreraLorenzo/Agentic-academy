/** Live curriculum data, with the same query keys as the curriculum and path pages (FR-016). */
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import { useMe } from "../../app/session";
import type { PathDetail, PathSummary } from "../catalog/types";

export function useCatalog() {
  return useQuery({ queryKey: ["catalog"], queryFn: () => get<PathSummary[]>("/catalog") });
}

export function availablePaths(paths: PathSummary[] | undefined): PathSummary[] {
  return (paths ?? []).filter((p) => p.status === "available");
}

export function usePathDetail(pathId: string | undefined) {
  const { data: me } = useMe();
  return useQuery({
    queryKey: ["path", pathId, !!me],
    queryFn: () => get<PathDetail>(`/paths/${pathId}`),
    enabled: !!pathId,
  });
}
