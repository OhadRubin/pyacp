"""PyACP - Python SDK for Agent Client Protocol with Claude-like interface."""

__version__ = "0.1.0"

# Re-export main SDK components
from pyacp.client.acp_client import (
    PyACPSDKClient,
    PyACPAgentOptions,
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

__all__ = [
    "PyACPSDKClient",
    "PyACPAgentOptions",
    "AssistantMessage",
    "UserMessage",
    "SystemMessage",
    "ResultMessage",
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
]
