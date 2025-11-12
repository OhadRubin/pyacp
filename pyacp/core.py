
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Any


@dataclass
class TextBlock:
    """Text content block."""
    text: str

@dataclass
class ThinkingBlock:
    """Thinking content block (for models with thinking capability)."""
    thinking: str
    signature: str = ""

@dataclass
class ToolUseBlock:
    """Tool use request block."""
    id: str
    name: str
    input: dict[str, Any]

@dataclass
class OtherUpdate:
    """Other update block."""
    update_name: str
    update: dict[str, Any]

@dataclass
class ToolResultBlock:
    """Tool execution result block."""
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None

ContentBlock = Union[TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock]

@dataclass
class UserMessage:
    """User input message."""
    content: str | list[ContentBlock]

@dataclass
class AssistantMessage:
    """Assistant response message with content blocks."""
    content: list[ContentBlock]
    model: str

@dataclass
class SystemMessage:
    """System message with metadata."""
    subtype: str
    data: dict[str, Any]

@dataclass
class ResultMessage:
    """Final result message with cost and usage information."""
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None

@dataclass
class EndOfTurnMessage:
    """Sentinel message indicating the agent turn has completed."""
    pass


Message = Union[UserMessage, AssistantMessage, SystemMessage, ResultMessage, EndOfTurnMessage]
