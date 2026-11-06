"""Evaluate agent runs from execution traces."""

SUSPICIOUS = ("ignore previous instructions", "disregard your instructions", "you are now")


def count_tool_calls(trace) -> dict:
    raise NotImplementedError


def unapproved_destructive(trace) -> list:
    raise NotImplementedError


def suspicious_results(trace) -> list:
    raise NotImplementedError


def passes_policy(trace, allowed_tools, max_tool_calls) -> bool:
    raise NotImplementedError
