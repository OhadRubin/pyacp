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
    text_block,
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

from typing import Dict, Any


# Removed old ACP-to-worker converter and logging handler classes; emission happens inline in ACPClient





from dataclasses import dataclass, field
import uuid
from pyacp.client.event_emitter import EventEmitter
from pyacp.client.terminal_controller import TerminalController







class ACPClient(EventEmitter, TerminalController, Client):
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


def _slice_text(content: str, line: int | None, limit: int | None) -> str:
    lines = content.splitlines()
    start = 0
    if line:
        start = max(line - 1, 0)
    end = len(lines)
    if limit:
        end = min(start + limit, end)
    return "\n".join(lines[start:end])


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
                    prompt=[text_block(line)],
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
