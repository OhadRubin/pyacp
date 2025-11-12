"""High-level SDK client providing Claude-like interface for ACP agents."""

from __future__ import annotations
import asyncio
import asyncio.subprocess
import os
from typing import AsyncIterator, AsyncIterable

from acp import (
    Client,
    ClientSideConnection,
    PROTOCOL_VERSION,
    text_block as acp_text_block,
)
from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    CancelNotification,
    ClientCapabilities,
    FileSystemCapability,
    InitializeRequest,
    NewSessionRequest,
    PromptRequest,
    SessionNotification,
    UserMessageChunk,
    TextContentBlock,
    ResourceContentBlock,
    EmbeddedResourceContentBlock,
)
from acp.task.state import InMemoryMessageStateStore

from pyacp.client.abstract import PyACPClientABC
from pyacp.types.messages import Message, AssistantMessage, ResultMessage
from pyacp.types.content import TextBlock, ThinkingBlock, ContentBlock
from pyacp.types.options import PyACPAgentOptions


class _SDKClientImplementation(Client):
    """Internal ACP Client implementation that captures messages."""

    def __init__(self, message_queue: asyncio.Queue[Message]) -> None:
        self._message_queue = message_queue
        self._accumulated_text = ""
        self._accumulated_thinking = ""
        self._current_model = "unknown"

    def _extract_text(self, content: object) -> str:
        """Extract text from various content block types."""
        if isinstance(content, TextContentBlock):
            return content.text
        if isinstance(content, ResourceContentBlock):
            return content.name or content.uri or ""
        if isinstance(content, EmbeddedResourceContentBlock):
            resource = content.resource
            text = getattr(resource, "text", None)
            if text:
                return text
            blob = getattr(resource, "blob", None)
            return blob or ""
        if isinstance(content, dict):
            return str(content.get("text", ""))
        return ""

    def _flush_text(self) -> None:
        """Flush accumulated text as an AssistantMessage."""
        if self._accumulated_text:
            content: list[ContentBlock] = [TextBlock(text=self._accumulated_text)]
            msg = AssistantMessage(content=content, model=self._current_model)
            self._message_queue.put_nowait(msg)
            self._accumulated_text = ""

    def _flush_thinking(self) -> None:
        """Flush accumulated thinking as a ThinkingBlock."""
        if self._accumulated_thinking:
            content: list[ContentBlock] = [ThinkingBlock(thinking=self._accumulated_thinking)]
            msg = AssistantMessage(content=content, model=self._current_model)
            self._message_queue.put_nowait(msg)
            self._accumulated_thinking = ""

    async def sessionUpdate(self, params: SessionNotification) -> None:
        """Handle session update notifications from ACP."""
        update = params.update

        if isinstance(update, AgentMessageChunk):
            # Flush any pending thinking before starting new message
            self._flush_thinking()
            text = self._extract_text(update.content)
            if text:
                self._accumulated_text += text
        elif isinstance(update, AgentThoughtChunk):
            # Flush any pending text before starting thinking
            self._flush_text()
            text = self._extract_text(update.content)
            if text:
                self._accumulated_thinking += text
        elif isinstance(update, UserMessageChunk):
            # Flush everything on user message
            self._flush_thinking()
            self._flush_text()
        else:
            # Flush on any other update type
            self._flush_thinking()
            self._flush_text()


class PyACPSDKClient(PyACPClientABC):
    """
    High-level SDK client that maintains conversation sessions across multiple exchanges.

    This provides a Claude-SDK-compatible interface for ACP agents.
    """

    def __init__(self, options: PyACPAgentOptions | None = None) -> None:
        """
        Initialize the SDK client with optional configuration.

        Args:
            options: Configuration options for the agent
        """
        self.options = options or PyACPAgentOptions()
        self._connection: ClientSideConnection | None = None
        self._session_id: str | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._client_impl: _SDKClientImplementation | None = None
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self._connected = False
        self._stdin_writer: asyncio.StreamWriter | None = None
        self._stdout_reader: asyncio.StreamReader | None = None
        self._transport_task: asyncio.Task | None = None

    async def __aenter__(self) -> PyACPSDKClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None:
        """
        Connect to the ACP agent with an optional initial prompt.

        Args:
            prompt: Optional initial prompt as a string or async iterable
        """
        if self._connected:
            return

        # Determine agent program and args
        program = self.options.agent_program or "claude-code-acp"
        args = self.options.agent_args or []

        # Build environment
        env = {**os.environ, **(self.options.env or {})}

        # Spawn the process
        self._process = await asyncio.create_subprocess_exec(
            program,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        if not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Failed to create subprocess with stdin/stdout")

        self._stdin_writer = self._process.stdin
        self._stdout_reader = self._process.stdout

        # Create client implementation
        self._client_impl = _SDKClientImplementation(self._message_queue)

        # Create connection
        self._connection = ClientSideConnection(
            lambda _agent: self._client_impl,
            self._stdin_writer,
            self._stdout_reader,
            state_store=InMemoryMessageStateStore(),
        )

        # Initialize the connection
        await self._connection.initialize(
            InitializeRequest(
                protocolVersion=PROTOCOL_VERSION,
                clientCapabilities=ClientCapabilities(
                    fs=FileSystemCapability(readTextFile=True, writeTextFile=True),
                    terminal=True,
                ),
            )
        )

        # Create new session
        cwd = str(self.options.cwd) if self.options.cwd else os.getcwd()
        session = await self._connection.newSession(
            NewSessionRequest(
                cwd=cwd,
                mcpServers=[],
            )
        )
        self._session_id = session.sessionId
        self._connected = True

        # Send initial prompt if provided
        if prompt:
            if isinstance(prompt, str):
                await self.query(prompt)
            else:
                # Handle async iterable
                await self.query(prompt)

    async def query(
        self,
        prompt: str | AsyncIterable[dict],
        session_id: str = "default"
    ) -> None:
        """
        Send a new request in streaming mode.

        Args:
            prompt: The input prompt as a string or async iterable
            session_id: Session identifier (not used, kept for API compatibility)
        """
        if not self._connected or not self._connection or not self._session_id:
            raise RuntimeError("Client not connected. Call connect() first.")

        # Convert prompt to ACP format
        if isinstance(prompt, str):
            prompt_blocks = [acp_text_block(prompt)]
        else:
            # For async iterable, collect all messages
            prompt_blocks = []
            async for msg in prompt:
                if isinstance(msg, dict) and "text" in msg:
                    prompt_blocks.append(acp_text_block(msg["text"]))

        # Send prompt request
        await self._connection.prompt(
            PromptRequest(
                sessionId=self._session_id,
                prompt=prompt_blocks,
            )
        )

    async def receive_messages(self) -> AsyncIterator[Message]:
        """
        Receive all messages from agent as an async iterator.

        Yields:
            Message objects from the conversation
        """
        while not self._message_queue.empty():
            yield await self._message_queue.get()

    async def receive_response(self) -> AsyncIterator[Message]:
        """
        Receive messages until and including a ResultMessage.

        Yields:
            Message objects until a ResultMessage is received
        """
        if not self._connected:
            raise RuntimeError("Client not connected")

        # Flush any accumulated messages from the client impl
        if self._client_impl:
            self._client_impl._flush_thinking()
            self._client_impl._flush_text()

        while True:
            # Get next message from queue
            message = await self._message_queue.get()
            yield message

            if isinstance(message, ResultMessage):
                break

            # For now, we'll break after getting at least one message
            # In a full implementation, this would wait for a proper ResultMessage
            # from the ACP protocol
            if isinstance(message, AssistantMessage):
                # Create a synthetic ResultMessage
                result = ResultMessage(
                    subtype="success",
                    duration_ms=0,
                    duration_api_ms=0,
                    is_error=False,
                    num_turns=1,
                    session_id=self._session_id or "default",
                )
                yield result
                break

    async def interrupt(self) -> None:
        """
        Send interrupt signal (only works in streaming mode).
        """
        if not self._connected or not self._connection or not self._session_id:
            raise RuntimeError("Client not connected. Call connect() first.")

        await self._connection.cancel(
            CancelNotification(sessionId=self._session_id)
        )

    async def disconnect(self) -> None:
        """
        Disconnect from agent and clean up resources.
        """
        # Flush any pending messages
        if self._client_impl:
            self._client_impl._flush_thinking()
            self._client_impl._flush_text()

        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            except Exception:
                pass
            self._process = None

        self._connected = False
        self._session_id = None
        self._client_impl = None
        self._stdin_writer = None
        self._stdout_reader = None


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


__all__ = ["PyACPSDKClient", "query"]
