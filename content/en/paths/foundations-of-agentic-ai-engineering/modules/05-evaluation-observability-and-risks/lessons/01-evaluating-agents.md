---
id: evaluating-agents
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Evaluating agents
---

Agents need two kinds of evidence: that **your code** behaves correctly, and that **the system**
behaves well with a real model.

## Deterministic tests with model doubles {#test-doubles}

Script the model's responses and assert what your code does with them — every challenge in this
path works this way. These tests are fast, repeatable and run in CI.

## Trace-based evaluation {#traces}

An **execution trace** records what happened: events, tool calls with arguments and results, and
state transitions. Policies can be checked on traces mechanically — which tools were used, whether
destructive calls were approved, how many steps it took.

```python title="policy.py"
def within_policy(trace, allowed_tools, max_steps):
    calls = [e for e in trace if e["kind"] == "tool_call"]
    return all(c["tool"] in allowed_tools for c in calls) and len(calls) <= max_steps
```

```mermaid alt="Evaluation layers: unit tests with scripted models check code logic; trace policies check each run; datasets of real tasks measure quality over time."
flowchart TB
  U[Unit tests with scripted models] --> P[Trace policies on every run]
  P --> D[Evaluation datasets over time]
```

:::maturity{level="established"}
Deterministic tests with test doubles and policy checks on traces are established practice.
:::

:::maturity{level="emerging"}
Using a model as a judge to grade agent outputs is an emerging technique; validate the judge
against human labels before trusting its scores.
:::

## Observability without private reasoning {#observability}

Record what is observable — inputs, tool calls, results, state, errors, timing. Do not treat a
model's own explanation of its reasoning as a faithful account of why it acted; it is more
generated text. The laboratory in this course shows exactly these observable elements.

:::vendor{name="OpenTelemetry"}
OpenTelemetry defines semantic conventions for generative-AI spans and events, so traces can be
exported to standard observability backends.
:::
