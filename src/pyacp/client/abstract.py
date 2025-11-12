"""
Abstract base class for Claude SDK Client interface.

This module defines the abstract interface that any Claude client implementation
should follow, based on the Claude Code SDK specification.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, AsyncIterable, Any


class PyACPClientABC(ABC):
    """
    Abstract base class defining the interface for ACP SDK clients.

    This class maintains a conversation session across multiple exchanges,
    supporting session continuity, interrupts, and explicit lifecycle management.
    """

    @abstractmethod
    def __init__(self, options: Any | None = None) -> None:
        """
        Initialize the client with optional configuration.

        Args:
            options: Optional configuration object (e.g., PyACPAgentOptions)
        """
        pass

    @abstractmethod
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None:
        """
        Connect to Claude with an optional initial prompt or message stream.

        Args:
            prompt: Optional initial prompt as a string or async iterable
                   for streaming mode
        """
        pass

    @abstractmethod
    async def query(
        self,
        prompt: str | AsyncIterable[dict],
        session_id: str = "default"
    ) -> None:
        """
        Send a new request in streaming mode.

        Args:
            prompt: The input prompt as a string or async iterable for streaming
            session_id: Session identifier (default: "default")
        """
        pass

    @abstractmethod
    async def receive_messages(self) -> AsyncIterator[Any]:
        """
        Receive all messages from Claude as an async iterator.

        Yields:
            Message objects from the conversation
        """
        pass

    @abstractmethod
    async def receive_response(self) -> AsyncIterator[Any]:
        """
        Receive messages until and including a ResultMessage.

        Yields:
            Message objects until a ResultMessage is received
        """
        pass

    @abstractmethod
    async def interrupt(self) -> None:
        """
        Send interrupt signal (only works in streaming mode).

        This can be used to stop Claude mid-execution.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from Claude.

        Closes the connection and cleans up resources.
        """
        pass

    async def __aenter__(self):
        """
        Async context manager entry.

        Automatically connects when entering the context.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.

        Automatically disconnects when exiting the context.
        """
        await self.disconnect()
