# npm install @zed-industries/codex-acp
# uv add agent-client-protocol
# npm install -g @zed-industries/claude-code-acp
#  uv run acp_client.py claude-code-acp
#  uv run acp_client.py codex-acp

from __future__ import annotations

import asyncio
import asyncio.subprocess
import contextlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Any


from acp import (
    Client,
    ClientSideConnection,
    PROTOCOL_VERSION,
    RequestError,
    text_block as acp_text_block,
)
from acp.transports import spawn_stdio_transport
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    CancelNotification,
    ClientCapabilities,
    FileEditToolCallContent,
    FileSystemCapability,
    CreateTerminalRequest,
    CreateTerminalResponse,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    InitializeRequest,
    SetSessionModelRequest,
    NewSessionRequest,
    PermissionOption,
    PromptRequest,
    ReadTextFileRequest,
    ReadTextFileResponse,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    SessionNotification,
    TerminalToolCallContent,
    TerminalOutputRequest,
    TerminalOutputResponse,
    ContentToolCallContent,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)
from acp.contrib.session_state import SessionAccumulator

#!/usr/bin/env python3
"""
ACP client that emits canonical WorkerFormat events inline.

Only these content block types are emitted:
- TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock, ContentBlock
"""



# Removed old ACP-to-worker converter and logging handler classes; emission happens inline in ACPClient



from pyacp.client.event_emitter import EventEmitter
from pyacp.client.terminal_controller import TerminalController
from pyacp.client.file_system_controller import FileSystemController


from dataclasses import dataclass, field
from typing import AsyncIterable, Iterable, Union, AsyncIterator
import asyncio
from pathlib import Path

from acp.schema import (
    CancelNotification,
    DeniedOutcome,
    AllowedOutcome,
)


# Inlined type definitions from pyacp.types

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

Message = Union[UserMessage, AssistantMessage, SystemMessage, ResultMessage]


@dataclass
class PyACPAgentOptions:
    """Configuration options for ACP agent queries.

    This provides a Claude SDK-compatible interface for ACP agents.
    """
    model: str | None = None
    cwd: str | Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    max_turns: int | None = None

    # Additional ACP-specific options
    agent_program: str | None = None  # Path to ACP agent executable
    agent_args: list[str] = field(default_factory=list)  # Args for agent


class PyACPSDKClient:
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
        self._client_impl: _SDKClientImplementation | None = None
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self._connected = False
        self._transport_cm = None  # Context manager for the transport


    async def __aenter__(self) -> PyACPSDKClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self, agent_command: str | list[str] | None = None) -> None:
        """
        Connect to the ACP agent and establish a session.

        Args:
            agent_command: Agent program path or command list. If None, uses options.agent_program
        """
        if self._connected:
            raise RuntimeError("Client already connected")

        # Determine agent command
        if agent_command is None:
            if self.options.agent_program is None:
                raise ValueError("No agent command specified. Provide agent_command or set options.agent_program")
            spawn_program = self.options.agent_program
            spawn_args = self.options.agent_args
        elif isinstance(agent_command, str):
            # Check if the program exists and is executable
            program_path = Path(agent_command)
            if program_path.exists() and not os.access(program_path, os.X_OK):
                spawn_program = sys.executable
                spawn_args = [str(program_path)]
            else:
                spawn_program = agent_command
                spawn_args = []
        else:
            # It's a list
            spawn_program = agent_command[0]
            spawn_args = agent_command[1:] if len(agent_command) > 1 else []

        # Spawn the agent process
        self._transport_cm = spawn_stdio_transport(
            spawn_program,
            *spawn_args,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )

        # Enter the transport context manager
        stdout, stdin, proc = await self._transport_cm.__aenter__()

        # Create client implementation
        model = self.options.model or "unknown"
        self._client_impl = _SDKClientImplementation(self._message_queue, model=model)

        # Create connection
        self._connection = ClientSideConnection(
            lambda _agent: self._client_impl,
            stdin,
            stdout,
            state_store=self._client_impl.state_store,
        )

        # Initialize the connection
        try:
            await self._connection.initialize(
                InitializeRequest(
                    protocolVersion=PROTOCOL_VERSION,
                    clientCapabilities=ClientCapabilities(
                        fs=FileSystemCapability(readTextFile=True, writeTextFile=True),
                        terminal=True,
                    ),
                )
            )
        except RequestError as err:
            await self._cleanup_connection()
            raise RuntimeError(f"Initialize failed: {err.to_error_obj()}") from err
        except Exception as exc:
            await self._cleanup_connection()
            raise RuntimeError(f"Initialize error: {exc}") from exc

        # Create new session
        try:
            cwd = self.options.cwd or os.getcwd()
            session = await self._connection.newSession(
                NewSessionRequest(
                    cwd=str(cwd),
                    mcpServers=[],
                )
            )
            self._session_id = session.sessionId
        except RequestError as err:
            await self._cleanup_connection()
            raise RuntimeError(f"New session failed: {err.to_error_obj()}") from err
        except Exception as exc:
            await self._cleanup_connection()
            raise RuntimeError(f"New session error: {exc}") from exc

        # Set model if specified
        if self.options.model:
            try:
                await self._connection.setSessionModel(
                    SetSessionModelRequest(
                        modelId=self.options.model,
                        sessionId=self._session_id
                    )
                )
            except Exception:
                # Model setting is optional, don't fail if it doesn't work
                pass

        self._connected = True

    async def _cleanup_connection(self) -> None:
        """Clean up connection resources on error."""
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None

        if self._transport_cm:
            try:
                await self._transport_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._transport_cm = None

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
            self._client_impl._flush()

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
            self._client_impl._flush()

        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None

        # Exit transport context manager (handles process cleanup)
        if self._transport_cm:
            try:
                await self._transport_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._transport_cm = None

        self._connected = False
        self._session_id = None
        self._client_impl = None






class _SDKClientImplementation(EventEmitter, TerminalController, FileSystemController, Client):
    """
    Internal ACP client implementation that queues messages for PyACPSDKClient.

    This class extends ACPClient to handle ACP protocol events and convert them
    into Message objects that are queued for consumption by the SDK client.
    """

    def __init__(self, message_queue: asyncio.Queue[Message], model: str = "unknown"):
        """
        Initialize the SDK client implementation.

        Args:
            message_queue: Queue to put Message objects into
            model: Model identifier for AssistantMessage objects
        """
        super().__init__()
        self.tool_call_requests = {}
        self._message_queue = message_queue
        self._model = model
        self._content_blocks: list[ContentBlock] = []

    def _emit_text(self, text: str) -> None:
        """Override to queue TextBlock instead of emitting to stdout."""
        if not text:
            return
        self._content_blocks.append(TextBlock(text=text))

    def _emit_thinking(self, thinking: str) -> None:
        """Override to queue ThinkingBlock instead of emitting to stdout."""
        if not thinking:
            return
        self._content_blocks.append(ThinkingBlock(thinking=thinking))

    def _flush(self) -> None:
        """Flush accumulated content blocks as an AssistantMessage to the queue."""
        if self._content_blocks:
            message = AssistantMessage(
                content=self._content_blocks.copy(),
                model=self._model
            )
            try:
                self._message_queue.put_nowait(message)
            except asyncio.QueueFull:
                # Queue is full, skip this message
                pass
            self._content_blocks.clear()


class ACPClient(EventEmitter, TerminalController, FileSystemController, Client):
    def __init__(self):
        super().__init__()
        self.tool_call_requests = {}



    async def requestPermission(
        self,
        params: RequestPermissionRequest,
    ) -> RequestPermissionResponse:  # type: ignore[override]
        option = _pick_preferred_option(params.options)
        if option is None:
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        return RequestPermissionResponse(outcome=AllowedOutcome(optionId=option.optionId, outcome="selected"))






def _pick_preferred_option(options: Iterable[PermissionOption]) -> PermissionOption | None:
    best: PermissionOption | None = None
    for option in options:
        if option.kind in {"allow_once", "allow_always"}:
            return option
        best = best or option
    return best


async def interactive_loop(client: PyACPSDKClient) -> None:
    """
    Interactive loop for CLI usage with PyACPSDKClient.

    Args:
        client: Connected PyACPSDKClient instance
    """
    print("Type a message and press Enter to send.")
    print("Commands: :cancel, :exit")

    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, lambda: input("\n> ").strip())
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not line:
            continue
        if line in {":exit", ":quit"}:
            break
        if line == ":cancel":
            try:
                await client.interrupt()
                print("[Cancelled]")
            except Exception as exc:
                print(f"Cancel failed: {exc}", file=sys.stderr)
            continue

        try:
            if not line.strip():
                continue
            print(f"[line]: {line}")

            # Send the query
            await client.query(line, session_id=client._session_id or "default")

            # Receive and print messages
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                        elif isinstance(block, ThinkingBlock):
                            print(f"[Thinking]: {block.thinking}")
                        elif isinstance(block, ToolUseBlock):
                            print(f"[Tool Use]: {block.name} - {block.input}")
                        elif isinstance(block, ToolResultBlock):
                            print(f"[Tool Result]: {block.content}")
                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        print(f"[Error]: {message.result}", file=sys.stderr)
                    else:
                        print(f"[Result - {message.num_turns} turns, {message.duration_ms}ms]")

        except RequestError as err:
            _print_request_error("prompt", err)
        except Exception as exc:  # noqa: BLE001
            print(f"Prompt failed: {exc}", file=sys.stderr)


async def run(argv: list[str]) -> int:
    """
    Standalone CLI runner that uses PyACPSDKClient for all protocol operations.

    Args:
        argv: Command line arguments (program name, agent command, agent args)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if len(argv) < 2:
        print("Usage: python acp_client.py AGENT_PROGRAM [ARGS...]", file=sys.stderr)
        return 2

    model_id = os.environ.get("ACP_MODEL", None)
    program = argv[1]
    args = argv[2:]

    # Build agent command
    agent_command = [program] + args

    # Create options
    options = PyACPAgentOptions(
        model=model_id,
        cwd=os.getcwd(),
    )

    # Create and connect client
    client = PyACPSDKClient(options)

    try:
        # Connect to agent (this handles all initialization)
        await client.connect(agent_command)

        # Run interactive loop
        await interactive_loop(client)

        # Disconnect gracefully
        await client.disconnect()

        return 0

    except FileNotFoundError as exc:
        print(f"Failed to start agent process: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1
    finally:
        # Ensure cleanup even on error
        if client._connected:
            with contextlib.suppress(Exception):
                await client.disconnect()


def _print_request_error(stage: str, err: RequestError) -> None:
    payload = err.to_error_obj()
    message = payload.get("message", "")
    code = payload.get("code")
    data = payload.get("data")
    print(f"{stage} request error: code={code} message={message} data={data}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    # Keep logging quiet; emission happens directly from ACPClient
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.ERROR)

    args = sys.argv if argv is None else argv
    return asyncio.run(run(list(args)))


if __name__ == "__main__":
    raise SystemExit(main())
