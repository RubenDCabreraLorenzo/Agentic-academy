import type { DeprecationInfo } from "../../components/content/Callouts";

export type Level = "foundational" | "intermediate" | "advanced";
export type ModuleStatus = "not_started" | "in_progress" | "completed";

export interface Competency {
  id: string;
  title: string;
  level: Level;
}

export interface ContentMetaFields {
  id: string;
  version: string;
  lang: string;
  last_reviewed: string;
  deprecation?: DeprecationInfo | null;
}

export interface PathSummary extends ContentMetaFields {
  title: string;
  summary: string;
  level: Level;
  status: "available" | "planned";
  order: number;
  estimated_hours: number;
  prerequisite_paths: string[];
  competencies: Competency[];
}

export interface PathDetail extends PathSummary {
  objectives: string[];
  entry_prerequisites: { label: string; resource_url: string }[];
  modules: { id: string; title: string; summary: string; order: number; status?: ModuleStatus }[];
}

export interface ModuleDetail extends ContentMetaFields {
  path_id: string;
  path_title?: string;
  title: string;
  summary: string;
  status: ModuleStatus;
  objectives: { id: string; statement: string }[];
  objectives_demonstrated: boolean;
  competencies: Competency[];
  missing_prerequisites: { id: string; title: string; taught_in_module: string }[];
  lessons: (ContentMetaFields & { title: string; body_markdown: string })[];
  references: { title: string; url: string; vendor?: string | null }[];
  knowledge_check_id: string | null;
  challenges: { id: string; title: string }[];
  lab_scenarios: { id: string; title: string }[];
  previous_module_id: string | null;
  next_module_id: string | null;
  deprecations: Record<string, DeprecationInfo>;
}
