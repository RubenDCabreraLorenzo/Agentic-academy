---
id: agentic-risks
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: A catalogue of agentic risks
---

## Risks and mitigations {#catalogue}

| Risk | What it looks like | Mitigation |
|------|--------------------|------------|
| Prompt injection | Tool results contain instructions | Treat results as data, least privilege, approval for destructive actions |
| Hallucination | Invented ids, facts or arguments | Validate in code, ground in sources |
| Excessive autonomy | Long loops, unexpected tools | Step and budget limits, minimal tool sets |
| Data exposure | Secrets in prompts, logs or memory | Redaction, data minimization |

## Detecting risks in traces {#detection}

Some signals can be checked automatically on every run: destructive tool calls without an approval
event, tool results containing instruction-like text such as "ignore previous instructions",
and runs that exceed their step budget.

```python title="signals.py"
SUSPICIOUS = ("ignore previous instructions", "disregard your instructions", "you are now")

def suspicious_results(trace):
    return [e["id"] for e in trace if e["kind"] == "tool_call"
            and any(s in str(e.get("result", "")).lower() for s in SUSPICIOUS)]
```

:::maturity{level="experimental"}
Keyword and classifier-based injection detection catches only known patterns. Treat detections as
signals for review, never as proof that a run was safe.
:::
