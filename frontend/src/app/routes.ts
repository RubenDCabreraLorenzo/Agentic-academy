/** Feature routes, code-split per page. Features are added as increments ship. */
import type { ComponentType } from "react";

export interface RouteDef {
  path: string;
  auth: boolean;
  load: () => Promise<{ default: ComponentType }>;
}

export const routes: RouteDef[] = [
  { path: "/", auth: false, load: () => import("../features/catalog/CatalogPage") },
  { path: "/paths/:pathId", auth: false, load: () => import("../features/catalog/PathPage") },
  { path: "/modules/:moduleId", auth: true, load: () => import("../features/module/ModulePage") },
  { path: "/knowledge-checks/:checkId", auth: true, load: () => import("../features/knowledge-check/KnowledgeCheckPage") },
  { path: "/challenges/:challengeId", auth: true, load: () => import("../features/challenge/ChallengePage") },
  { path: "/lab/:scenarioId", auth: true, load: () => import("../features/lab/LabPage") },
  { path: "/dashboard", auth: true, load: () => import("../features/dashboard/DashboardPage") },
  { path: "/dashboard/competencies", auth: true, load: () => import("../features/dashboard/CompetenciesPage") },
];
