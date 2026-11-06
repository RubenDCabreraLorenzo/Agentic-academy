import { compare, effectiveElements, initialState, reduce, stateAt, type Scenario } from "../../../src/features/lab/player";

const rec = { model: "m", framework: "f", date: "2026-11-01" };
const scenario: Scenario = {
  id: "s",
  version: "1.0.0",
  last_reviewed: "2026-11-06",
  title: "S",
  task: "T",
  objective: "O",
  tools: [
    { name: "search", description: "", permission: "read" },
    { name: "delete", description: "", permission: "destructive" },
  ],
  variants: [
    {
      id: "main",
      label: "Agent loop",
      orchestration_pattern: "agent_loop",
      recorded_with: rec,
      initial_state: { step: 0 },
      elements: [
        { id: "e1", seq: 0, kind: "execution_event", event: "run_started" },
        { id: "e2", seq: 1, kind: "tool_call", tool: "search", arguments: { q: "x" }, permission: "read", approval: "not_required" },
        { id: "e3", seq: 2, kind: "state_transition", before: { step: 0 }, after: { step: 1 }, changed_keys: ["step"] },
        { id: "e4", seq: 3, kind: "execution_event", event: "approval_request" },
      ],
    },
    {
      id: "yes",
      label: "Approved",
      orchestration_pattern: "agent_loop",
      recorded_with: rec,
      branches_from: { variant_id: "main", element_id: "e4", decision: "approved" },
      elements: [
        { id: "y1", seq: 4, kind: "tool_call", tool: "delete", arguments: {}, permission: "destructive", approval: "approved" },
        { id: "y2", seq: 5, kind: "execution_event", event: "run_ended", payload: { outcome: "deleted" } },
      ],
    },
    {
      id: "no",
      label: "Rejected",
      orchestration_pattern: "agent_loop",
      recorded_with: rec,
      branches_from: { variant_id: "main", element_id: "e4", decision: "rejected" },
      elements: [{ id: "n1", seq: 4, kind: "execution_event", event: "run_ended", payload: { outcome: "kept" } }],
    },
    {
      id: "flow",
      label: "Workflow",
      orchestration_pattern: "fixed_workflow",
      recorded_with: rec,
      elements: [
        { id: "f1", seq: 0, kind: "execution_event", event: "run_started" },
        { id: "f2", seq: 1, kind: "execution_event", event: "run_ended", payload: { outcome: "kept" } },
      ],
    },
  ],
};

describe("trace player", () => {
  it("steps forward and back and reports state", () => {
    let st = initialState(scenario);
    expect(st.variantId).toBe("main");
    st = reduce(scenario, st, { type: "next" });
    st = reduce(scenario, st, { type: "next" });
    expect(stateAt(scenario, st.variantId, st.index)).toEqual({ step: 1 });
    st = reduce(scenario, st, { type: "prev" });
    expect(st.index).toBe(1);
    expect(stateAt(scenario, st.variantId, st.index)).toEqual({ step: 0 });
  });

  it("pauses at an approval and follows the chosen branch", () => {
    let st = reduce(scenario, initialState(scenario), { type: "jump", index: 3 });
    expect(st.awaitingApproval).toBe(true);
    expect(reduce(scenario, st, { type: "next" }).index).toBe(3);
    expect(reduce(scenario, st, { type: "play" }).playing).toBe(false);
    st = reduce(scenario, st, { type: "decide", decision: "rejected" });
    expect(st.variantId).toBe("no");
    expect(st.awaitingApproval).toBe(false);
    st = reduce(scenario, st, { type: "next" });
    const rejected = scenario.variants[2];
    expect(rejected && effectiveElements(scenario, rejected)[st.index]?.id).toBe("n1");
    st = reduce(scenario, st, { type: "restart" });
    expect(st).toEqual(initialState(scenario, "main"));
  });

  it("play advances until the end and pause stops", () => {
    let st = reduce(scenario, initialState(scenario, "flow"), { type: "play" });
    expect(st.playing).toBe(true);
    st = reduce(scenario, st, { type: "next" });
    expect(st.index).toBe(1);
    expect(st.playing).toBe(false);
    expect(reduce(scenario, { ...st, playing: true }, { type: "pause" }).playing).toBe(false);
  });

  it("compares counts, outcome and unique elements", () => {
    const [left, right] = compare(scenario, "yes", "flow");
    expect(left.elementCount).toBe(6);
    expect(left.toolCallCount).toBe(2);
    expect(left.outcome).toBe("deleted");
    expect(right.outcome).toBe("kept");
    expect(left.uniqueIds.has("e2")).toBe(true);
    expect(right.uniqueIds.has("f1")).toBe(false);
    expect(right.uniqueIds.has("f2")).toBe(true);
  });
});
