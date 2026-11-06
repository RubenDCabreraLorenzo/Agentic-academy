"""Reference solution (validator only; never shipped to learners)."""

from collections import Counter

SUSPICIOUS = ("ignore previous instructions", "disregard your instructions", "you are now")


def _calls(trace):
    return [e for e in trace if e.get("kind") == "tool_call"]


def count_tool_calls(trace) -> dict:
    return dict(Counter(e["tool"] for e in _calls(trace)))


def unapproved_destructive(trace) -> list:
    return [e["id"] for e in _calls(trace) if e.get("permission") == "destructive" and e.get("approval") != "approved"]


def suspicious_results(trace) -> list:
    return [e["id"] for e in _calls(trace) if any(s in str(e.get("result", "")).lower() for s in SUSPICIOUS)]


def passes_policy(trace, allowed_tools, max_tool_calls) -> bool:
    calls = _calls(trace)
    return (
        all(e["tool"] in allowed_tools for e in calls)
        and len(calls) <= max_tool_calls
        and not unapproved_destructive(trace)
    )
