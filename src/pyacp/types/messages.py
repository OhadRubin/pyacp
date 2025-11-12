"""Message type definitions for PyACP SDK."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Union
from pyacp.types.content import ContentBlock


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


# Union type of all possible messages
Message = Union[UserMessage, AssistantMessage, SystemMessage, ResultMessage]


__all__ = [
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "Message",
]
