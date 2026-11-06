---
id: tool-design
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Designing tools a model can use
---

A tool definition is an interface for a reader that only sees its **name, description and argument
schema**. Ambiguity there becomes wrong calls at runtime.

## Name, description, schema {#schema}

- **Name**: a specific verb–object, such as `get_ticket` rather than `ticket`.
- **Description**: when to use it, when *not* to, and what it returns.
- **Schema**: explicit types, required fields, formats and allowed values.

```python title="ticket_tool.py"
GET_TICKET = {
    "name": "get_ticket",
    "description": "Read one support ticket by id. Use before summarizing or closing a ticket. Read-only.",
    "parameters": {
        "type": "object",
        "properties": {"ticket_id": {"type": "string", "description": "Ticket id such as 'T-1042'."}},
        "required": ["ticket_id"],
        "additionalProperties": False,
    },
}
```

:::maturity{level="established"}
JSON-Schema-style argument definitions are the established way to describe tools to models.
:::

:::vendor{name="Model Context Protocol"}
MCP standardizes how tools, resources and prompts are exposed to models across applications. The
design advice in this lesson applies unchanged to MCP tool definitions.
:::

## Least privilege {#least-privilege}

Give an agent only the tools its task needs, each with the narrowest permission: read before write,
write before destructive. A summarizing agent does not need `close_ticket`.

```mermaid alt="Permission levels: read tools run directly; write tools run after argument validation; destructive tools run only after validation and explicit human approval."
flowchart LR
  R[read] -->|validate args| RUN1[run]
  W[write] -->|validate args| RUN2[run]
  D[destructive] -->|validate args| H{human approves?}
  H -->|yes| RUN3[run]
  H -->|no| STOP[do not run; report rejection]
```
