"""Configuration options for PyACP SDK."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, TypedDict, NotRequired
from pathlib import Path


# Permission modes
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all permission checks (use with caution)
]


class SystemPromptPreset(TypedDict):
    """Configuration for using preset system prompts."""

    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]


@dataclass
class PyACPAgentOptions:
    """Configuration options for ACP agent queries.

    This provides a Claude SDK-compatible interface for ACP agents.
    """

    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    permission_mode: PermissionMode | None = None
    model: str | None = None
    cwd: str | Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)

    # Additional ACP-specific options
    agent_program: str | None = None  # Path to ACP agent executable
    agent_args: list[str] = field(default_factory=list)  # Args for agent


__all__ = [
    "PermissionMode",
    "SystemPromptPreset",
    "PyACPAgentOptions",
]
