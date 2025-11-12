"""
PyACP - Python SDK for Agent Client Protocol

A Python SDK providing a Claude-like interface for interacting with
ACP-compatible agents.
"""

__version__ = "0.1.0"

# Import and export public API
from pyacp.client.sdk_client import PyACPSDKClient, query
from pyacp.types.messages import (
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    Message,
)
from pyacp.types.content import (
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
    ContentBlock,
)
from pyacp.types.options import (
    PyACPAgentOptions,
    PermissionMode,
    SystemPromptPreset,
)

__all__ = [
    # Main client
    "PyACPSDKClient",
    "query",
    # Message types
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "Message",
    # Content blocks
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ContentBlock",
    # Options
    "PyACPAgentOptions",
    "PermissionMode",
    "SystemPromptPreset",
]
