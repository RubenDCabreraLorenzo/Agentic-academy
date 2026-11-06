import type { ModuleStatus, PathSummary } from "../catalog/types";

export interface CompetencyRow {
  id: string;
  title: string;
  description: string;
  level: "foundational" | "intermediate" | "advanced";
  status: "not_started" | "in_progress" | "demonstrated";
  demonstrated_at: string | null;
  evidence: { type: "knowledge_check" | "challenge"; id: string; version: string; result_id: string; at: string }[];
}

export interface Dashboard {
  new_learner: boolean;
  active_path: PathSummary | null;
  competencies_demonstrated: number;
  competencies_total: number;
  competencies: CompetencyRow[];
  modules: { id: string; title: string; status: ModuleStatus }[];
  pending_objectives: { id: string; statement: string; module_id: string; module_title: string }[];
  next_step: { kind: "lesson" | "knowledge_check" | "challenge" | "next_path"; target_id: string; label: string; module_id: string | null } | null;
  continue: { module_id: string; lesson_id: string | null } | null;
  path_completed: boolean;
  completion_summary: {
    competencies: CompetencyRow[];
    recommended_next_path: { id: string; title: string; status: string } | null;
  } | null;
}
