"""Content block type definitions for PyACP SDK."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Union


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
class ToolResultBlock:
    """Tool execution result block."""

    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None


# Union type of all content blocks
ContentBlock = Union[TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock]


__all__ = [
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ContentBlock",
]
