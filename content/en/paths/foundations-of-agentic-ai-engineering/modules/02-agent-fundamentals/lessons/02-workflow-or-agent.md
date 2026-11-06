---
id: workflow-or-agent
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Workflow or agent?
---

Autonomy is a cost, not a feature. Every decision you hand to the model adds variability, latency
and spend, and makes behavior harder to test.

## Prefer workflows when the steps are known {#prefer-workflows}

A **workflow** is code that calls the model and tools in a fixed order. Use one when the steps are
known in advance — classify, look up a template, draft a reply. You get predictable cost, simple
tests and clear failure points.

```python title="workflow.py"
def triage(email, classify, get_template, model):
    category = classify(text=email)            # step 1: always
    template = get_template(category=category) # step 2: always
    return model.complete([...]).content       # step 3: one model call to fill the template
```

## Use agents when the path depends on what you find {#use-agents}

An **agent loop** earns its cost when the next step genuinely depends on intermediate results:
open-ended research, debugging, multi-step lookups. Even then, bound it and give it only the tools
it needs.

```mermaid alt="Decision: if the sequence of steps is known in advance, build a workflow; if the next step depends on intermediate results, build a bounded agent loop with least-privilege tools."
flowchart LR
  Q{Are the steps known in advance?} -->|yes| W[Workflow: fixed sequence in code]
  Q -->|no| A[Bounded agent loop with minimal tools]
```

:::maturity{level="emerging"}
Hybrid designs — a workflow that delegates one open-ended step to a small agent — are an emerging
pattern for keeping autonomy where it pays off.
:::
