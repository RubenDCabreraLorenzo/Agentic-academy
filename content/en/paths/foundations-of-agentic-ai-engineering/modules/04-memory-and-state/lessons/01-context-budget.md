---
id: context-budget
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Working within a context budget
---

Every turn and tool result is appended to an agent's conversation. Left alone, the context grows
until it exceeds the window, costs rise with every call, and important instructions get buried.

## Trim and summarize {#trim-summarize}

A common design keeps:

1. the **system message** (task and rules) — always;
2. the **most recent turns** verbatim;
3. a **summary** of older turns, produced by a model call when they are dropped.

```mermaid alt="Memory policy: the system message is always kept; recent messages are kept verbatim; when the budget is exceeded, the oldest messages are summarized into one summary message and removed."
flowchart LR
  S[System message: always kept] --> C[Context sent to the model]
  Sum[Summary of older turns] --> C
  R[Recent turns verbatim] --> C
  O[Oldest turns over budget] -->|summarize| Sum
```

```python title="trim.py"
def trim(messages, keep_last):
    system, rest = messages[0], messages[1:]
    dropped, kept = rest[:-keep_last], rest[-keep_last:]
    return system, dropped, kept   # summarize `dropped` before discarding it
```

:::maturity{level="established"}
Bounding history with a sliding window plus summaries is an established technique.
:::

:::maturity{level="experimental"}
Learned memory systems that decide automatically what to remember across sessions are still
experimental; measure them before relying on them.
:::
