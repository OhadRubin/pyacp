
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, Any


def _default_timestamp() -> str:
    """Generate a default timestamp in ISO format."""
    return datetime.now().isoformat()


@dataclass
class TextBlock:
    """Text content block."""
    text: str
    timestamp: str = field(default_factory=_default_timestamp)

@dataclass
class ThinkingBlock:
    """Thinking content block (for models with thinking capability)."""
    thinking: str
    signature: str = ""
    timestamp: str = field(default_factory=_default_timestamp)

@dataclass
class ToolUseBlock:
    """Tool use request block."""
    id: str
    name: str
    input: dict[str, Any]
    timestamp: str = field(default_factory=_default_timestamp)

@dataclass
class OtherUpdate:
    """Other update block."""
    update_name: str
    update: dict[str, Any]
    timestamp: str = field(default_factory=_default_timestamp)

@dataclass
class ToolResultBlock:
    """Tool execution result block."""
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
    timestamp: str = field(default_factory=_default_timestamp)

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
