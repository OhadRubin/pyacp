from __future__ import annotations

import asyncio
import asyncio.subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, AsyncIterable, Union, AsyncIterator, Any
from dataclasses import dataclass, field

from acp import (
    Client,
    ClientSideConnection,
    PROTOCOL_VERSION,
    RequestError,
    text_block as acp_text_block,
)
from acp.transports import spawn_stdio_transport
from acp.schema import (
    AllowedOutcome,
    CancelNotification,
    ClientCapabilities,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    FileSystemCapability,
    InitializeRequest,
    NewSessionRequest,
    PermissionOption,
    PromptRequest,
    RequestPermissionRequest,
    RequestPermissionResponse,
    ResourceContentBlock,
    SessionNotification,
    SetSessionModelRequest,
    TextContentBlock,
    AgentMessageChunk,
    AgentThoughtChunk,
    UserMessageChunk,
)
from acp.task.state import InMemoryMessageStateStore

from pyacp.core import (
    TextBlock,
    ThinkingBlock,
    OtherUpdate,
    EndOfTurnMessage,
    Message,
)
from pyacp.capabilities.filesystem import FileSystemController
from pyacp.capabilities.terminal import TerminalController


def _pick_preferred_option(options: Iterable[PermissionOption]) -> PermissionOption | None:
    best: PermissionOption | None = None
    for option in options:
        if option.kind in {"allow_once", "allow_always"}:
            return option
        best = best or option
    return best


class MyInMemoryMessageStateStore(InMemoryMessageStateStore):
    def __init__(self, client_impl):
        super().__init__()
        self._client_impl = client_impl

    def resolve_outgoing(self, request_id: int, result):
        # Flush accumulated message when a turn ends
        try:
            stop_reason = None
            if isinstance(result, dict):
                stop_reason = result.get("stopReason")
            else:
                # Fallback for objects with attribute access
                stop_reason = getattr(result, "stopReason", None)
            if stop_reason == "end_turn":
                # Schedule the async flush and queue end-of-turn sentinel
                asyncio.create_task(self._client_impl._on_end_turn())
        except Exception:
            # Never let flushing interfere with state resolution
            pass
        super().resolve_outgoing(request_id, result)


class EventEmitter:
    def __init__(self):
        self.accumulated_message = ""
        self.current_message_type = None
        self.state_store = MyInMemoryMessageStateStore(self)

    # ------------------------- WorkerFormat emitters -------------------------
    async def _emit_worker_event(self, payload: dict) -> None:
        try:
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
        except Exception:
            import traceback
            traceback.print_exc()

    async def _emit_text(self, text: str) -> None:
        if not text:
            return
        await self._emit_worker_event({"type": "TextBlock", "message": {"text": text}})

    async def _emit_thinking(self, thinking: str) -> None:
        if not thinking:
            return
        await self._emit_worker_event({"type": "ThinkingBlock", "message": {"thinking": thinking}})
    # Accumulation helpers -------------------------------------------------
    def _extract_text(self, content: object) -> str:
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
            # Attempt to pull text field if present
            return str(content.get("text", ""))
        return ""

    async def _accumulate_chunk(self, msg_type: str, content: object) -> None:
        # Flush if the incoming type differs from current
        if self.current_message_type and msg_type != self.current_message_type:
            await self._flush_accumulated_message(trigger="type_change")

        if self.current_message_type != msg_type:
            self.current_message_type = msg_type

        text = self._extract_text(content)
        if text:
            self.accumulated_message += text

    async def _flush_accumulated_message(self, trigger: str | None = None) -> None:
        if self.accumulated_message:
            msg_type = self.current_message_type or "message"
            if msg_type == "agent_thought":
                await self._emit_thinking(self.accumulated_message)
            elif msg_type == "agent_message":
                await self._emit_text(self.accumulated_message)
            # Deliberately skip emitting user messages to keep only canonical blocks
        # Reset regardless of whether there was content
        self.accumulated_message = ""
        self.current_message_type = None
        

    async def sessionUpdate(
        self,
        params: SessionNotification,
    ) -> None:  # type: ignore[override]
        update = params.update
        if isinstance(update, AgentMessageChunk):
            await self._accumulate_chunk("agent_message", update.content)
        elif isinstance(update, AgentThoughtChunk):
            await self._accumulate_chunk("agent_thought", update.content)
        elif isinstance(update, UserMessageChunk):
            await self._accumulate_chunk("user_message", update.content)
        else:
            await self._flush_accumulated_message(trigger="other_update")
            await self._emit_worker_event({"type": f"OtherUpdate:{update.__class__.__name__}", "message": {"update": update.model_dump()}})
            



class _SDKClientImplementation(EventEmitter, TerminalController, FileSystemController, Client):
    """
    Internal ACP client implementation that queues messages for PyACPSDKClient.

    This class extends ACPClient to handle ACP protocol events and convert them
    into Message objects that are queued for consumption by the SDK client.
    """

    def __init__(self, message_queue: asyncio.Queue[Message]):
        """
        Initialize the SDK client implementation.

        Args:
            message_queue: Queue to put Message objects into
            model: Model identifier for AssistantMessage objects
        """
        # Initialize all parent classes
        EventEmitter.__init__(self)
        TerminalController.__init__(self)
        # FileSystemController has no __init__, Client.__init__ is handled by EventEmitter chain

        self.tool_call_requests = {}
        self._message_queue = message_queue


    async def requestPermission(
        self,
        params: RequestPermissionRequest,
    ) -> RequestPermissionResponse:  # type: ignore[override]
        option = _pick_preferred_option(params.options)
        if option is None:
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
        return RequestPermissionResponse(outcome=AllowedOutcome(optionId=option.optionId, outcome="selected"))

    async def _emit_worker_event(self, payload: dict) -> None:

        # Also queue messages for SDK consumption
        if payload["type"] == "TextBlock":
            msg = TextBlock(text=payload["message"]["text"])
        elif payload["type"] == "ThinkingBlock":
            msg = ThinkingBlock(thinking=payload["message"]["thinking"])
        elif payload["type"].startswith("OtherUpdate"):
            msg = OtherUpdate(update_name=payload["type"], update=payload["message"]["update"])
        else:
            raise ValueError(f"Unknown message type: {payload['type']}")
        await self._message_queue.put(msg)

    async def _on_end_turn(self) -> None:
        """Called when the agent turn completes."""
        # Flush any accumulated messages
        await self._flush_accumulated_message(trigger="end_turn")
        # Queue the end-of-turn sentinel
        await self._message_queue.put(EndOfTurnMessage())

    



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


    async def __aenter__(self):
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

        self._client_impl = _SDKClientImplementation(self._message_queue)

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
    ) -> None:
        """
        Send a new request in streaming mode. Returns immediately - messages stream via receive_messages().

        Args:
            prompt: The input prompt as a string or async iterable
            session_id: Session identifier (not used, kept for API compatibility)
        """
        if not self._connected or not self._connection or not self._session_id:
            raise RuntimeError("Client not connected. Call connect() first.")

        # Convert prompt to ACP format
        assert isinstance(prompt, str)
        prompt_blocks = [acp_text_block(prompt)]
        # Send prompt request without blocking (fire-and-forget)
        asyncio.create_task(
            self._connection.prompt(
                PromptRequest(
                    sessionId=self._session_id,
                    prompt=prompt_blocks,
                )
            )
        )

    async def receive_messages(self) -> AsyncIterator[Message]:
        """
        Stream messages from agent as they arrive until end-of-turn.

        Yields:
            Message objects from the conversation (excludes EndOfTurnMessage sentinel)
        """
        while True:
            message = await self._message_queue.get()
            if isinstance(message, EndOfTurnMessage):
                # Turn is complete, stop streaming
                break
            setattr(message, "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
            yield message

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