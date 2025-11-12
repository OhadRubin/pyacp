"""
PyACP - Python SDK for Agent Client Protocol

A Python SDK providing a Claude-like interface for interacting with
ACP-compatible agents.
"""

from typing import AsyncIterator, AsyncIterable

__version__ = "0.1.0"

# Import and export public API from acp_client
from pyacp.client.acp_client import (
    PyACPSDKClient,
    PyACPAgentOptions,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    Message,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
    ContentBlock,
)


async def query(
    *,
    prompt: str | AsyncIterable[dict],
    options: PyACPAgentOptions | None = None
) -> AsyncIterator[Message]:
    """
    Create a new session and query the agent (Claude SDK-compatible interface).

    This is a convenience function that creates a new client, sends a query,
    and yields all response messages.

    Args:
        prompt: The input prompt as a string or async iterable
        options: Optional configuration object

    Yields:
        Message objects from the agent response

    Example:
        ```python
        async for message in query(
            prompt="Hello!",
            options=PyACPAgentOptions(agent_program="claude-code-acp")
        ):
            print(message)
        ```
    """
    async with PyACPSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            yield message


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
]
