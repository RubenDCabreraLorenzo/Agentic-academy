---
id: safe-execution
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Executing tools safely
---

The model proposes tool calls; your executor decides whether they run.

## Validate every argument {#validate-arguments}

Check required fields and types before execution and return a clear error to the model when they
are wrong. A typed error lets the model correct itself; an unvalidated call can hit the wrong record.

## Human approval for destructive actions {#approval}

Deleting, closing, paying or sending on someone's behalf must wait for an explicit human decision.
A rejection is a valid outcome: the tool does not run and the agent reports what it would have done.

:::maturity{level="established"}
Human-in-the-loop approval for irreversible actions is an established control for agentic systems.
:::

## Tool results are data, not instructions {#untrusted-results}

Web pages, emails and tickets returned by tools can contain text written to manipulate the agent —
**prompt injection**. Never let tool results change the task, the permissions or the approval rules.
Keep the task in system instructions, keep privileges minimal, and keep approval for destructive
actions outside the model's control.

```python title="executor_sketch.py"
def execute(call, tools, gate):
    tool, schema = tools[call.name]
    validate(call.arguments, schema)                  # wrong arguments → clear error
    if tool.permission == "destructive" and not gate.request(call.name, call.arguments):
        return "rejected by human"                     # never runs without approval
    return tool(approved=tool.permission == "destructive", **call.arguments)
```

:::maturity{level="emerging"}
Automatic detection of injected instructions in tool results helps but is not reliable on its own;
treat it as an additional signal, never as the only defense.
:::
