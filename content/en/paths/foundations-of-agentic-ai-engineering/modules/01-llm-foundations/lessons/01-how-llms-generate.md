---
id: how-llms-generate
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: How language models generate text
---

Every agent you will build in this academy sits on top of a language model. Before designing loops,
tools or memory, you need an accurate mental model of what the model actually does — and does not
do — on each call. Most agent failures that look mysterious are ordinary consequences of the
mechanics below.

## Tokens, not words {#tokens}

A model never sees characters or words directly. Input text is split into **tokens**: frequent
character sequences learned from training data. A common English word is often one token; a rare
word, a long number or a piece of code may be several. Everything the model reads and writes is a
sequence of token ids.

Why this matters for engineering:

- **Limits and costs are counted in tokens**, not characters. A JSON payload with long keys can cost
  far more than the same data in a compact form.
- **Exact string operations are unreliable.** Counting letters, reversing strings or comparing long
  ids happens across token boundaries the model never sees as individual characters. Do these in
  code, not in the prompt.

:::maturity{level="established"}
Sub-word tokenization (for example byte-pair encoding) is the standard input representation for
current language models.
:::

## Next-token prediction {#next-token}

Given the tokens so far, the model outputs a **probability distribution over the next token**. The
runtime picks one token from that distribution, appends it, and repeats until it produces a stop
token or reaches a length limit.

```mermaid alt="Generation loop: the prompt tokens go into the model, which outputs probabilities for the next token; one token is sampled and appended to the sequence, and the loop repeats until a stop token or the length limit."
flowchart LR
  P[Prompt tokens] --> M[Model]
  M --> D[Next-token probabilities]
  D --> S[Sample one token]
  S --> A[Append to sequence]
  A -->|repeat| M
  S -->|stop token or limit| O[Output]
```

The model has **no separate step where it "decides" an answer and then writes it down**. The answer
is the sequence of sampled tokens. That is why asking for an explanation *after* an answer does not
reveal how the answer was produced — the explanation is just more generated text.

## The context window {#context-window}

The **context window** is the maximum number of tokens the model can consider in one call: system
instructions, conversation history, tool results and the output it is generating. Anything outside
the window does not exist for that call.

Agents fill context quickly: every tool result and every turn is appended. Two consequences you will
design around in later modules:

1. Long-running agents must decide **what to keep, summarize or drop** (Module 4, memory and state).
2. Information placed in a very long context is not always used reliably, so important instructions
   and data should be concise and well structured rather than buried.

## Sampling and temperature {#sampling}

The runtime does not always pick the most likely token. **Sampling parameters** reshape the
distribution before a token is drawn:

- **Temperature** divides the model's scores before converting them to probabilities. Low values
  make likely tokens even more likely (more deterministic); high values flatten the distribution
  (more varied, more errors).
- **Top-p / top-k** restrict sampling to the most likely tokens.

The example below shows the effect of temperature on a toy distribution. It uses only the standard
library so you can run it anywhere.

```python title="temperature.py" annotate
import math
import random

def apply_temperature(scores: dict[str, float], temperature: float) -> dict[str, float]:
    scaled = {tok: s / temperature for tok, s in scores.items()}  # note: lower temperature = sharper distribution
    top = max(scaled.values())
    exps = {tok: math.exp(s - top) for tok, s in scaled.items()}  # note: subtract the max for numerical stability
    total = sum(exps.values())
    return {tok: e / total for tok, e in exps.items()}

scores = {"refund": 2.0, "replacement": 1.0, "apology": 0.5}
for t in (0.2, 1.0, 2.0):
    probs = apply_temperature(scores, t)
    choice = random.choices(list(probs), weights=list(probs.values()))[0]
    print(t, {k: round(v, 2) for k, v in probs.items()}, "->", choice)
```

**Design rule:** use low temperature for steps that must be consistent (classification, extracting
fields, choosing a tool) and accept that even at temperature 0 many providers do not guarantee
bit-identical outputs. Your code must tolerate variation instead of assuming it away.

:::vendor{name="Model providers"}
Parameter names, ranges and defaults differ between providers and models, and some models ignore or
restrict certain parameters. Check the documentation of the provider you use instead of copying
values between them.
:::
