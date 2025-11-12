import asyncio
from dataclasses import dataclass, field


@dataclass
class TerminalInfo:
    """Tracks a single terminal instance."""

    terminal_id: str
    process: asyncio.subprocess.Process
    output_buffer: bytearray = field(default_factory=bytearray)
    output_byte_limit: int | None = None
    truncated: bool = False
    exit_code: int | None = None
    signal: str | None = None
    _output_task: asyncio.Task | None = None

    def add_output(self, data: bytes) -> None:
        """Add output data, enforcing byte limit with UTF-8 character boundary truncation."""
        self.output_buffer.extend(data)

        if self.output_byte_limit is not None and len(self.output_buffer) > self.output_byte_limit:
            # Truncate from the beginning, ensuring UTF-8 character boundaries
            excess = len(self.output_buffer) - self.output_byte_limit

            # Find a valid UTF-8 starting point after the excess
            truncate_point = excess
            while truncate_point < len(self.output_buffer):
                try:
                    # Try to decode from this point to verify it's a valid UTF-8 boundary
                    self.output_buffer[truncate_point:truncate_point+1].decode('utf-8', errors='strict')
                    break
                except UnicodeDecodeError:
                    truncate_point += 1

            self.output_buffer = self.output_buffer[truncate_point:]
            self.truncated = True

    def get_output(self) -> str:
        """Get the current output as a string."""
        try:
            return self.output_buffer.decode('utf-8', errors='replace')
        except Exception:
            return self.output_buffer.decode('utf-8', errors='ignore')

from pathlib import Path

from acp import RequestError
from acp.schema import (
    ReadTextFileRequest,
    ReadTextFileResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)


def _slice_text(content: str, line: int | None, limit: int | None) -> str:
    lines = content.splitlines()
    start = 0
    if line:
        start = max(line - 1, 0)
    end = len(lines)
    if limit:
        end = min(start + limit, end)
    return "\n".join(lines[start:end])


class FileSystemController:
    async def writeTextFile(
        self,
        params: WriteTextFileRequest,
    ) -> WriteTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params.content)
        # Intentionally quiet; WorkerFormat emission handled elsewhere
        return WriteTextFileResponse()

    async def readTextFile(
        self,
        params: ReadTextFileRequest,
    ) -> ReadTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        text = path.read_text()
        # Intentionally quiet; WorkerFormat emission handled via hooks
        if params.line is not None or params.limit is not None:
            text = _slice_text(text, params.line, params.limit)
        return ReadTextFileResponse(content=text)


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
from datetime import datetime
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

from pathlib import Path

from acp import RequestError
from acp.schema import (
    ReadTextFileRequest,
    ReadTextFileResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)


def _slice_text(content: str, line: int | None, limit: int | None) -> str:
    lines = content.splitlines()
    start = 0
    if line:
        start = max(line - 1, 0)
    end = len(lines)
    if limit:
        end = min(start + limit, end)
    return "\n".join(lines[start:end])


class FileSystemController:
    async def writeTextFile(
        self,
        params: WriteTextFileRequest,
    ) -> WriteTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params.content)
        # Intentionally quiet; WorkerFormat emission handled elsewhere
        return WriteTextFileResponse()

    async def readTextFile(
        self,
        params: ReadTextFileRequest,
    ) -> ReadTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        text = path.read_text()
        # Intentionally quiet; WorkerFormat emission handled via hooks
        if params.line is not None or params.limit is not None:
            text = _slice_text(text, params.line, params.limit)
        return ReadTextFileResponse(content=text)


def _pick_preferred_option(options: Iterable[PermissionOption]) -> PermissionOption | None:
    best: PermissionOption | None = None
    for option in options:
        if option.kind in {"allow_once", "allow_always"}:
            return option
        best = best or option
    return best


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
class OtherUpdate:
    """Other update block."""
    update_name: str
    update: dict[str, Any]

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

@dataclass
class EndOfTurnMessage:
    """Sentinel message indicating the agent turn has completed."""
    pass

Message = Union[UserMessage, AssistantMessage, SystemMessage, ResultMessage, EndOfTurnMessage]



import asyncio
import json
import sys

from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    EmbeddedResourceContentBlock,
    ResourceContentBlock,
    SessionNotification,
    TextContentBlock,
    UserMessageChunk,
)
from acp.task.state import InMemoryMessageStateStore


import asyncio
import os
import uuid

from acp import RequestError
from acp.schema import (
    CreateTerminalRequest,
    CreateTerminalResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
)
from pyacp.utils.terminal import TerminalInfo


class TerminalController:

    # Optional / terminal-related methods ---------------------------------
    async def _capture_terminal_output(self, terminal_info: TerminalInfo) -> None:
        """Background task to capture stdout and stderr from a terminal process."""
        try:
            # Capture both stdout and stderr
            tasks = []
            if terminal_info.process.stdout:
                tasks.append(self._read_stream(terminal_info, terminal_info.process.stdout))
            if terminal_info.process.stderr:
                tasks.append(self._read_stream(terminal_info, terminal_info.process.stderr))

            if tasks:
                await asyncio.gather(*tasks)

            # Wait for process to complete and capture exit status
            await terminal_info.process.wait()

            # Determine exit status
            if terminal_info.process.returncode is not None:
                if terminal_info.process.returncode < 0:
                    # Negative return codes typically indicate signals
                    import signal
                    try:
                        sig = signal.Signals(-terminal_info.process.returncode)
                        terminal_info.signal = sig.name
                    except (ValueError, AttributeError):
                        terminal_info.signal = f"SIGNAL_{-terminal_info.process.returncode}"
                else:
                    terminal_info.exit_code = terminal_info.process.returncode

        except Exception:
            pass

    async def _read_stream(self, terminal_info: TerminalInfo, stream: asyncio.StreamReader) -> None:
        """Read from a stream and add to terminal output buffer."""
        try:
            while True:
                chunk = await stream.read(4096)
                if not chunk:
                    break
                terminal_info.add_output(chunk)
        except Exception:
            pass

    async def createTerminal(
        self,
        params: CreateTerminalRequest,
    ) -> CreateTerminalResponse:  # type: ignore[override]
        # Generate unique terminal ID
        self._terminal_counter += 1
        terminal_id = f"term_{uuid.uuid4().hex[:8]}_{self._terminal_counter}"

        # Build environment
        env = dict(os.environ)
        if params.env:
            for env_var in params.env:
                env[env_var.name] = env_var.value

        # Build command - always run through shell like a real terminal
        full_command = params.command
        if params.args:
            full_command += ' ' + ' '.join(params.args)
        cmd = ['/bin/sh', '-c', full_command]

        # Determine working directory
        cwd = params.cwd if params.cwd else os.getcwd()

        try:
            # Spawn the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            # Create terminal info
            terminal_info = TerminalInfo(
                terminal_id=terminal_id,
                process=process,
                output_byte_limit=params.outputByteLimit,
            )

            # Start background task to capture output
            terminal_info._output_task = asyncio.create_task(
                self._capture_terminal_output(terminal_info)
            )

            # Register terminal
            self.terminals[terminal_id] = terminal_info

            return CreateTerminalResponse(terminalId=terminal_id)

        except Exception as exc:
            raise RequestError.internal_error({"message": f"Failed to create terminal: {exc}"})

    async def terminalOutput(
        self,
        params: TerminalOutputRequest,
    ) -> TerminalOutputResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        output = terminal_info.get_output()

        # Build response
        response_data = {
            "output": output,
            "truncated": terminal_info.truncated,
        }

        # Add exit status if process has completed
        if terminal_info.exit_code is not None or terminal_info.signal is not None:
            response_data["exitStatus"] = {
                "exitCode": terminal_info.exit_code,
                "signal": terminal_info.signal,
            }

        return TerminalOutputResponse(**response_data)

    async def releaseTerminal(
        self,
        params: ReleaseTerminalRequest,
    ) -> ReleaseTerminalResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Kill the process if it's still running
        if terminal_info.process.returncode is None:
            try:
                terminal_info.process.kill()
                # Wait briefly for the process to terminate
                try:
                    await asyncio.wait_for(terminal_info.process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
            except Exception as exc:
                pass

        # Cancel the output capture task if it's still running
        if terminal_info._output_task and not terminal_info._output_task.done():
            terminal_info._output_task.cancel()
            try:
                await terminal_info._output_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        # Remove from registry
        del self.terminals[params.terminalId]

        return ReleaseTerminalResponse()

    async def waitForTerminalExit(
        self,
        params: WaitForTerminalExitRequest,
    ) -> WaitForTerminalExitResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Wait for the process to complete
        await terminal_info.process.wait()

        return WaitForTerminalExitResponse(
            exitCode=terminal_info.exit_code,
            signal=terminal_info.signal
        )

    async def killTerminal(
        self,
        params: KillTerminalCommandRequest,
    ) -> KillTerminalCommandResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Kill the process if it's still running
        if terminal_info.process.returncode is None:
            try:
                terminal_info.process.kill()
                pass
            except Exception:
                pass

        return KillTerminalCommandResponse()


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
        super().__init__()
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
            message["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
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

            await client.query(line)
            async for message in client.receive_messages():
                
                print(f"[message in interactive_loop]: {message}")
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
