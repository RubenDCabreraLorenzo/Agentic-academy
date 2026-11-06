/**
 * Trace player state machine (US5; FR-027, FR-029, FR-030, FR-032). Pure functions only, so the
 * behavior is unit-tested without a browser. Recordings are replayed client-side; no model calls.
 */

export type ElementKind = "execution_event" | "tool_call" | "state_transition" | "decision_summary";

export interface TraceElement {
  id: string;
  seq: number;
  kind: ElementKind;
  event?: string;
  summary?: string;
  payload?: Record<string, unknown>;
  tool?: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  error?: string;
  permission?: "read" | "write" | "destructive";
  approval?: "not_required" | "approved" | "rejected" | "pending";
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  changed_keys?: string[];
  explains?: string[];
  text?: string;
  author?: string;
  reviewed_on?: string;
  label?: string;
}

export interface Variant {
  id: string;
  label: string;
  orchestration_pattern: string;
  branches_from?: { variant_id: string; element_id: string; decision: "approved" | "rejected" };
  recorded_with: { model: string; framework: string; date: string };
  initial_state?: Record<string, unknown>;
  elements: TraceElement[];
}

export interface Scenario {
  id: string;
  version: string;
  last_reviewed: string;
  title: string;
  task: string;
  objective: string;
  tools: { name: string; description: string; permission: "read" | "write" | "destructive" }[];
  variants: Variant[];
  comparisons?: { left_variant: string; right_variant: string; explanation?: string }[];
  failure_cases?: { variant_id: string; element_id: string; kind: string; risk: string; mitigation: string }[];
}

export interface PlayerState {
  variantId: string;
  index: number;
  playing: boolean;
  awaitingApproval: boolean;
}

export type Action =
  | { type: "next" }
  | { type: "prev" }
  | { type: "restart" }
  | { type: "jump"; index: number }
  | { type: "play" }
  | { type: "pause" }
  | { type: "decide"; decision: "approved" | "rejected" }
  | { type: "select"; variantId: string };

export function variantById(s: Scenario, id: string): Variant {
  const v = s.variants.find((x) => x.id === id);
  if (!v) throw new Error(`unknown variant ${id}`);
  return v;
}

/** Elements a variant shows: inherited prefix (for approval branches) followed by its own. */
export function effectiveElements(s: Scenario, variant: Variant): TraceElement[] {
  const origin = variant.branches_from;
  if (!origin) return variant.elements;
  const parent = effectiveElements(s, variantById(s, origin.variant_id));
  const cut = parent.findIndex((e) => e.id === origin.element_id);
  return [...parent.slice(0, cut + 1), ...variant.elements];
}

export function rootVariants(s: Scenario): Variant[] {
  return s.variants.filter((v) => !v.branches_from);
}

export function initialState(s: Scenario, variantId?: string): PlayerState {
  const id = variantId ?? rootVariants(s)[0]?.id ?? s.variants[0]?.id ?? "";
  return { variantId: id, index: 0, playing: false, awaitingApproval: false };
}

function isApproval(e: TraceElement | undefined): boolean {
  return e?.kind === "execution_event" && e.event === "approval_request";
}

function branchFor(s: Scenario, variantId: string, elementId: string, decision: "approved" | "rejected"): Variant | undefined {
  return s.variants.find(
    (v) => v.branches_from && v.branches_from.element_id === elementId && v.branches_from.decision === decision &&
      (v.branches_from.variant_id === variantId || effectiveElements(s, variantById(s, variantId)).some((e) => e.id === elementId)),
  );
}

export function reduce(s: Scenario, state: PlayerState, action: Action): PlayerState {
  const elements = effectiveElements(s, variantById(s, state.variantId));
  const last = elements.length - 1;
  switch (action.type) {
    case "next": {
      if (state.awaitingApproval || state.index >= last) return { ...state, playing: false };
      const index = state.index + 1;
      const target = elements[index];
      const awaiting = !!target && isApproval(target) && !hasBranchAfter(s, state.variantId, target.id);
      return { ...state, index, awaitingApproval: awaiting, playing: state.playing && !awaiting && index < last };
    }
    case "prev": {
      // Stepping back before an approval in a branch returns to the variant the branch came from.
      const variant = variantById(s, state.variantId);
      const index = Math.max(0, state.index - 1);
      const origin = variant.branches_from;
      if (origin) {
        const parent = effectiveElements(s, variantById(s, origin.variant_id));
        const cut = parent.findIndex((e) => e.id === origin.element_id);
        if (index < cut) return { variantId: origin.variant_id, index, playing: false, awaitingApproval: false };
      }
      return { ...state, index, playing: false, awaitingApproval: false };
    }
    case "restart":
      return initialState(s, rootOf(s, state.variantId));
    case "jump": {
      const index = Math.min(Math.max(0, action.index), last);
      const target = elements[index];
      return { ...state, index, playing: false, awaitingApproval: !!target && isApproval(target) && !hasBranchAfter(s, state.variantId, target.id) };
    }
    case "play":
      return state.awaitingApproval || state.index >= last ? state : { ...state, playing: true };
    case "pause":
      return { ...state, playing: false };
    case "decide": {
      const current = elements[state.index];
      if (!state.awaitingApproval || !current) return state;
      const branch = branchFor(s, state.variantId, current.id, action.decision);
      if (!branch) return { ...state, awaitingApproval: false };
      return { variantId: branch.id, index: state.index, playing: false, awaitingApproval: false };
    }
    case "select":
      return initialState(s, action.variantId);
  }
}

function rootOf(s: Scenario, variantId: string): string {
  let v = variantById(s, variantId);
  while (v.branches_from) v = variantById(s, v.branches_from.variant_id);
  return v.id;
}

/** True when the current variant already continues past this approval (i.e. it is a branch). */
function hasBranchAfter(s: Scenario, variantId: string, approvalId: string): boolean {
  const v = variantById(s, variantId);
  return effectiveElements(s, v).findIndex((e) => e.id === approvalId) < effectiveElements(s, v).length - 1 && !!v.branches_from;
}

/** Agent state at a position: the last state transition's "after", or the initial state. */
export function stateAt(s: Scenario, variantId: string, index: number): Record<string, unknown> {
  const variant = variantById(s, variantId);
  const elements = effectiveElements(s, variant).slice(0, index + 1);
  let root = variant;
  while (root.branches_from) root = variantById(s, root.branches_from.variant_id);
  let state: Record<string, unknown> = root.initial_state ?? {};
  for (const e of elements) if (e.kind === "state_transition" && e.after) state = e.after;
  return state;
}

function signature(e: TraceElement): string {
  if (e.kind === "tool_call") return `tool:${e.tool}:${JSON.stringify(e.arguments ?? {})}`;
  if (e.kind === "execution_event") return `event:${e.event}:${JSON.stringify(e.payload?.outcome ?? null)}`;
  if (e.kind === "state_transition") return `state:${(e.changed_keys ?? []).join(",")}`;
  return `summary:${e.text ?? ""}`;
}

export interface ComparisonSide {
  variant: Variant;
  elementCount: number;
  toolCallCount: number;
  outcome: string;
  uniqueIds: Set<string>;
}

function outcomeOf(elements: TraceElement[]): string {
  const end = [...elements].reverse().find((e) => e.kind === "execution_event" && (e.event === "run_ended" || e.event === "error" || e.event === "step_limit_reached"));
  if (!end) return "—";
  const outcome = end.payload?.outcome;
  return typeof outcome === "string" ? outcome : (end.summary ?? end.event ?? "—");
}

/** FR-029: counts, final outcome and elements present in only one of the two executions. */
export function compare(s: Scenario, leftId: string, rightId: string): [ComparisonSide, ComparisonSide] {
  const left = effectiveElements(s, variantById(s, leftId)).filter((e) => e.kind !== "decision_summary");
  const right = effectiveElements(s, variantById(s, rightId)).filter((e) => e.kind !== "decision_summary");
  const ls = new Set(left.map(signature));
  const rs = new Set(right.map(signature));
  const side = (variant: Variant, els: TraceElement[], other: Set<string>): ComparisonSide => ({
    variant,
    elementCount: els.length,
    toolCallCount: els.filter((e) => e.kind === "tool_call").length,
    outcome: outcomeOf(els),
    uniqueIds: new Set(els.filter((e) => !other.has(signature(e))).map((e) => e.id)),
  });
  return [side(variantById(s, leftId), left, rs), side(variantById(s, rightId), right, ls)];
}
