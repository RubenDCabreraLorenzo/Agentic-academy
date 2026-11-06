export type QuestionType = "single_choice" | "multiple_choice" | "ordering" | "matching";

export interface Choice {
  id: string;
  text: string;
}

export interface Question {
  id: string;
  type: QuestionType;
  prompt_markdown: string;
  options?: Choice[];
  items?: Choice[];
  left?: Choice[];
  right?: Choice[];
}

export interface Answer {
  selected?: string[];
  pairs?: Record<string, string>;
}

export interface LessonLink {
  module_id: string;
  lesson_id: string;
  anchor: string;
}

export interface Feedback {
  correct: boolean;
  explanation_markdown: string;
  lesson_link: LessonLink;
}

export interface Attempt {
  attempt_id: string;
  knowledge_check_id: string;
  module_id: string;
  version: string;
  status: "in_progress" | "submitted";
  pass_threshold: number;
  objectives: string[];
  questions: Question[];
  saved_answers: Record<string, Answer>;
  feedback: Record<string, Feedback>;
}

export interface AttemptResult {
  attempt_id: string;
  version: string;
  submitted_at: string | null;
  score: number;
  passed: boolean;
  best_score: number | null;
  questions: (Feedback & { question_id: string })[];
  weak_objectives: { id: string; statement: string; lesson_link: LessonLink }[];
  objectives_demonstrated: string[];
  competencies_demonstrated: string[];
}
