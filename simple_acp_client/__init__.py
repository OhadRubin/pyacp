"""
Simple ACP Client - Python SDK for the Agent Client Protocol (ACP)

A high-level, async-friendly interface for interacting with ACP-compatible agents.
"""

from simple_acp_client.sdk.client import PyACPSDKClient, PyACPAgentOptions
from simple_acp_client.core import (
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
    OtherUpdate,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    EndOfTurnMessage,
    Message,
    ContentBlock,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "PyACPSDKClient",
    "PyACPAgentOptions",
    # Message types
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "OtherUpdate",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "EndOfTurnMessage",
    "Message",
    "ContentBlock",
]
