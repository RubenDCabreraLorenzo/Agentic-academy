"""Vendor-neutral model and tool doubles for Agentic Academy challenges (runner protocol §9).

Learner code talks to a model through the small :class:`ModelClient` protocol taught in the course,
so tests can drive it deterministically with :class:`ScriptedModel` and never call a real model
service (FR-022b).
"""

from academy_sim.core import (
    ApprovalGate,
    FakeTool,
    Message,
    ModelClient,
    ModelResponse,
    PermissionDeniedError,
    ScriptedModel,
    ScriptExhaustedError,
    ToolCall,
    ToolSpec,
    TraceRecorder,
    assert_approval_requested,
    assert_tool_called,
    assert_tool_not_called,
)

__all__ = [
    "ApprovalGate",
    "FakeTool",
    "Message",
    "ModelClient",
    "ModelResponse",
    "PermissionDeniedError",
    "ScriptExhaustedError",
    "ScriptedModel",
    "ToolCall",
    "ToolSpec",
    "TraceRecorder",
    "assert_approval_requested",
    "assert_tool_called",
    "assert_tool_not_called",
]
