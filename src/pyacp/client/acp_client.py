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

from pyacp.types.messages import Message, AssistantMessage, ResultMessage
from pyacp.types.content import TextBlock, ThinkingBlock, ContentBlock



from pyacp.client.event_emitter import EventEmitter
from pyacp.client.terminal_controller import TerminalController
from pyacp.client.file_system_controller import FileSystemController


from dataclasses import dataclass, field
from typing import AsyncIterable, Iterable
import asyncio
from pathlib import Path

from acp.schema import (
    CancelNotification,
    DeniedOutcome,
    AllowedOutcome,
)
from pyacp.types.messages import PermissionOption
from acp.client import Client, ClientSideConnection

from typing import AsyncIterator


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
        pass

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


async def interactive_loop(conn: ClientSideConnection, session_id: str) -> None:
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
            await conn.cancel(CancelNotification(sessionId=session_id))
            continue

        try:
            if not line.strip():
                continue
            print(f"[line]: {line}")
            await conn.prompt(
                PromptRequest(
                    sessionId=session_id,
                    prompt=[acp_text_block(line)],
                )
            )
        except RequestError as err:
            _print_request_error("prompt", err)
        except Exception as exc:  # noqa: BLE001
            print(f"Prompt failed: {exc}", file=sys.stderr)


async def run(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python acp_client.py AGENT_PROGRAM [ARGS...]", file=sys.stderr)
        return 2
    model_id = os.environ.get("ACP_MODEL", None)
    program = argv[1]
    args = argv[2:]

    program_path = Path(program)
    spawn_program = program
    spawn_args = args

    if program_path.exists() and not os.access(program_path, os.X_OK):
        spawn_program = sys.executable
        spawn_args = [str(program_path), *args]

    try:
        async with spawn_stdio_transport(
            spawn_program,
            *spawn_args,
            stderr=asyncio.subprocess.PIPE,
            env={
                **os.environ,
            },
        ) as (stdout, stdin, proc):
            client_impl = ACPClient()
            conn = ClientSideConnection(
                lambda _agent: client_impl,
                stdin,
                stdout,
                state_store=client_impl.state_store,
            )

            try:
                init_resp = await conn.initialize(
                    InitializeRequest(
                        protocolVersion=PROTOCOL_VERSION,
                        clientCapabilities=ClientCapabilities(
                            fs=FileSystemCapability(readTextFile=True, writeTextFile=True),
                            terminal=True,
                        ),
                    )
                )
            except RequestError as err:
                _print_request_error("initialize", err)
                return 1
            except Exception as exc:  # noqa: BLE001
                print(f"Initialize error: {exc}", file=sys.stderr)
                return 1

            # No non-canonical emission here

            try:
                session = await conn.newSession(
                    NewSessionRequest(
                        cwd=os.getcwd(),
                        mcpServers=[],
                    )
                )
            except RequestError as err:
                _print_request_error("new_session", err)
                return 1
            except Exception as exc:  # noqa: BLE001
                print(f"New session error: {exc}", file=sys.stderr)
                return 1

            # No non-canonical emission here
            if model_id is not None:
                await conn.setSessionModel(SetSessionModelRequest(modelId=model_id,sessionId=session.sessionId))

            await interactive_loop(conn, session.sessionId)

            # Close connection gracefully before exiting context
            with contextlib.suppress(Exception):
                await conn.close()

            return 0

    except FileNotFoundError as exc:
        print(f"Failed to start agent process: {exc}", file=sys.stderr)
        return 1


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
