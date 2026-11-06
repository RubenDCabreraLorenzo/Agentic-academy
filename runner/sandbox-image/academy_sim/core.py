"""Core doubles: messages, scripted model, fake tools, approval gate and trace recorder."""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

Permission = Literal["read", "write", "destructive"]
PERMISSIONS: tuple[Permission, ...] = ("read", "write", "destructive")


@dataclass(frozen=True)
class ToolCall:
    """A model's request to call a tool."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class ModelResponse:
    """What a model returns for one turn: text, tool-call requests, or both."""

    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    permission: Permission = "read"


@runtime_checkable
class ModelClient(Protocol):
    """The minimal model interface learner code depends on."""

    def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> ModelResponse: ...


class ScriptExhaustedError(AssertionError):
    """The code under test called the model more times than the script allows."""


def _coerce_response(turn: ModelResponse | Mapping[str, Any] | str) -> ModelResponse:
    if isinstance(turn, ModelResponse):
        return turn
    if isinstance(turn, str):
        return ModelResponse(content=turn)
    calls = tuple(
        c
        if isinstance(c, ToolCall)
        else ToolCall(c.get("id", f"call-{i}"), c["name"], dict(c.get("arguments", {})))
        for i, c in enumerate(turn.get("tool_calls", []))
    )
    return ModelResponse(content=turn.get("content"), tool_calls=calls)


class ScriptedModel:
    """A deterministic :class:`ModelClient` returning scripted turns in order.

    ``turns`` may contain :class:`ModelResponse` objects, plain strings (text answers) or dicts
    like ``{"tool_calls": [{"name": "search", "arguments": {"q": "x"}}]}``. A callable turn
    receives the messages and returns a response, which lets tests react to learner input.
    """

    def __init__(
        self,
        turns: Iterable[ModelResponse | Mapping[str, Any] | str | Callable[[list[Message]], Any]],
    ) -> None:
        self._turns = list(turns)
        self.calls: list[list[Message]] = []
        self.tools_seen: list[list[ToolSpec]] = []

    def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> ModelResponse:
        if len(self.calls) >= len(self._turns):
            raise ScriptExhaustedError(
                f"model called {len(self.calls) + 1} times but only {len(self._turns)} turns are scripted"
            )
        self.calls.append(copy.deepcopy(list(messages)))
        self.tools_seen.append(list(tools or []))
        turn = self._turns[len(self.calls) - 1]
        if callable(turn):
            turn = turn(list(messages))
        return _coerce_response(turn)

    @property
    def call_count(self) -> int:
        return len(self.calls)


class PermissionDeniedError(PermissionError):
    """A tool was invoked without the approval its permission requires."""


@dataclass
class _Invocation:
    arguments: dict[str, Any]
    approved: bool
    result: Any = None
    error: str | None = None


class FakeTool:
    """A tool double that records calls and enforces its declared permission.

    ``destructive`` tools raise :class:`PermissionDeniedError` unless called with
    ``approved=True`` (normally the decision of an :class:`ApprovalGate`).
    """

    def __init__(
        self,
        name: str,
        permission: Permission = "read",
        handler: Callable[..., Any] | None = None,
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if permission not in PERMISSIONS:
            raise ValueError(f"permission must be one of {PERMISSIONS}")
        self.name = name
        self.permission: Permission = permission
        self.description = description or name
        self.parameters = parameters or {"type": "object", "properties": {}}
        self._handler = handler or (lambda **_: None)
        self.invocations: list[_Invocation] = []

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(self.name, self.description, self.parameters, self.permission)

    @property
    def calls(self) -> list[dict[str, Any]]:
        return [inv.arguments for inv in self.invocations]

    def __call__(self, approved: bool = False, **arguments: Any) -> Any:
        inv = _Invocation(arguments=dict(arguments), approved=approved)
        self.invocations.append(inv)
        if self.permission == "destructive" and not approved:
            inv.error = "permission denied: destructive tool requires approval"
            raise PermissionDeniedError(inv.error)
        try:
            inv.result = self._handler(**arguments)
        except Exception as exc:
            inv.error = f"{type(exc).__name__}: {exc}"
            raise
        return inv.result


class ApprovalGate:
    """Simulated human approval. ``decisions`` are consumed in order (``True`` = approve)."""

    def __init__(self, decisions: Iterable[bool]) -> None:
        self._decisions = list(decisions)
        self.requests: list[tuple[str, dict[str, Any]]] = []

    def request(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> bool:
        self.requests.append((tool_name, dict(arguments or {})))
        if len(self.requests) > len(self._decisions):
            raise AssertionError("approval requested more times than decisions were scripted")
        return self._decisions[len(self.requests) - 1]


class TraceRecorder:
    """Collects the four trace element kinds used by the laboratory (FR-027)."""

    def __init__(self) -> None:
        self.elements: list[dict[str, Any]] = []

    def _add(self, kind: str, **data: Any) -> dict[str, Any]:
        element = {
            "id": f"e{len(self.elements) + 1}",
            "seq": len(self.elements),
            "kind": kind,
            **data,
        }
        self.elements.append(element)
        return element

    def event(self, event: str, summary: str = "", **payload: Any) -> dict[str, Any]:
        return self._add("execution_event", event=event, summary=summary, payload=payload)

    def tool_call(
        self,
        tool: str,
        arguments: Mapping[str, Any],
        *,
        permission: Permission = "read",
        approval: Literal["not_required", "approved", "rejected", "pending"] = "not_required",
        result: Any = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        return self._add(
            "tool_call",
            tool=tool,
            arguments=dict(arguments),
            permission=permission,
            approval=approval,
            result=result,
            error=error,
        )

    def state_transition(
        self, before: Mapping[str, Any], after: Mapping[str, Any]
    ) -> dict[str, Any]:
        before_c, after_c = copy.deepcopy(dict(before)), copy.deepcopy(dict(after))
        changed = sorted(
            k for k in set(before_c) | set(after_c) if before_c.get(k) != after_c.get(k)
        )
        return self._add("state_transition", before=before_c, after=after_c, changed_keys=changed)

    def of_kind(self, kind: str) -> list[dict[str, Any]]:
        return [e for e in self.elements if e["kind"] == kind]

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        return self.of_kind("tool_call")

    @property
    def events(self) -> list[str]:
        return [e["event"] for e in self.of_kind("execution_event")]


def _calls_from(
    source: TraceRecorder | FakeTool | Iterable[dict[str, Any]], name: str
) -> list[dict[str, Any]]:
    if isinstance(source, FakeTool):
        return source.calls if source.name == name else []
    elements = source.elements if isinstance(source, TraceRecorder) else list(source)
    return [
        e.get("arguments", {})
        for e in elements
        if e.get("kind") == "tool_call" and e.get("tool") == name
    ]


def assert_tool_called(
    source: TraceRecorder | FakeTool | Iterable[dict[str, Any]], name: str, **expected: Any
) -> None:
    """Assert ``name`` was called at least once with arguments containing ``expected``."""
    calls = _calls_from(source, name)
    if not calls:
        raise AssertionError(f"expected tool '{name}' to be called, but it was not")
    if expected and not any(all(c.get(k) == v for k, v in expected.items()) for c in calls):
        raise AssertionError(f"tool '{name}' was called with {calls}, none matching {expected}")


def assert_tool_not_called(
    source: TraceRecorder | FakeTool | Iterable[dict[str, Any]], name: str
) -> None:
    calls = _calls_from(source, name)
    if calls:
        raise AssertionError(
            f"expected tool '{name}' not to be called, but it was called {len(calls)} time(s)"
        )


def assert_approval_requested(gate: ApprovalGate, tool_name: str) -> None:
    if not any(name == tool_name for name, _ in gate.requests):
        raise AssertionError(f"expected an approval request for '{tool_name}'")
