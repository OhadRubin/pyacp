# Code Review Guide: PR #2 - PyACPSDKClient Connection Implementation

## Table of Contents
1. [Background: What is Agent Client Protocol (ACP)?](#background-what-is-agent-client-protocol-acp)
2. [About PyACP](#about-pyacp)
3. [Current Repository Architecture](#current-repository-architecture)
4. [PR #2 Overview](#pr-2-overview)
5. [Detailed Changes](#detailed-changes)
6. [Key Review Points](#key-review-points)

---

## Background: What is Agent Client Protocol (ACP)?

### What is ACP?

The **Agent Client Protocol (ACP)** is a standardized communication framework that enables interoperability between:
- **Code Editors** (e.g., Zed, Neovim, Marimo) - Interactive programs for viewing and editing source code
- **Coding Agents** (e.g., Claude Code, Codex, Gemini, goose) - AI-powered programs that autonomously modify code

### Why ACP Exists

Before ACP, each editor-agent pair required custom integration. ACP solves this by providing:
- A **standardized JSON-RPC protocol** for communication
- **Common interfaces** for file operations, terminal access, and permissions
- **Session management** for maintaining conversation context
- **Tool call abstractions** for agent actions (read files, execute commands, etc.)

### How ACP Works

ACP uses a **client-server architecture** over stdio (standard input/output):

1. **Editor (Client)** spawns an agent process
2. **Agent (Server)** communicates via JSON-RPC over stdin/stdout
3. **Protocol flow**:
   ```
   Editor → initialize() → Agent
   Editor → newSession() → Agent
   Editor → prompt() → Agent
   Agent → sessionUpdate() notifications → Editor
   Agent → requestPermission() → Editor
   Editor → responds with allow/deny → Agent
   ```

### Key ACP Concepts

- **Session**: A conversation context that persists across multiple exchanges
- **Protocol Version**: Ensures client/agent compatibility
- **Capabilities**: Editor declares what it can do (filesystem, terminal, etc.)
- **Permissions**: Agents request permission for sensitive operations
- **Message Chunks**: Streaming updates (text, thinking, tool calls)

---

## About PyACP

**PyACP** is a Python SDK that implements the ACP client side, allowing Python programs to:
- Connect to any ACP-compatible agent
- Manage conversation sessions
- Send prompts and receive responses
- Handle file operations and terminal interactions

### Design Philosophy

PyACP mimics the **Claude Agent SDK** API, making it familiar to users of Claude's official SDK while being agent-agnostic (works with Claude Code, Codex, OpenCode, Gemini, etc.).

### Key Components

```
PyACP Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    PyACPSDKClient                            │
│  (High-level API - Claude SDK-compatible interface)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─→ ClientSideConnection (from acp library)
                     │   (Handles JSON-RPC protocol)
                     │
                     ├─→ _SDKClientImplementation / ACPClient
                     │   (Implements ACP Client interface)
                     │   │
                     │   ├─→ EventEmitter (message streaming)
                     │   ├─→ TerminalController (terminal ops)
                     │   └─→ FileSystemController (file ops)
                     │
                     └─→ Message Queue (asyncio.Queue)
                         (Buffers messages for consumer)
```

---

## Current Repository Architecture

### Repository Structure

```
pyacp/
├── src/pyacp/
│   ├── client/
│   │   ├── acp_client.py          ← Main file modified in PR #2
│   │   ├── event_emitter.py       ← Handles streaming events
│   │   ├── terminal_controller.py ← Terminal operations
│   │   ├── file_system_controller.py ← File operations
│   │   └── abstract.py            ← Base interfaces
│   ├── types/                     ← Type definitions
│   └── utils/                     ← Utilities
├── examples/                      ← Usage examples
├── tests/
│   ├── unit/                      ← Unit tests
│   ├── integration/               ← Integration tests
│   └── e2e/                       ← End-to-end tests
└── scripts/                       ← Smoke test scripts
```

### Main Classes Before PR #2

#### 1. `PyACPSDKClient`
High-level SDK client for maintaining conversation sessions.

**Before PR #2**:
- `connect()` method was a stub (just `pass`)
- Could not actually connect to agents
- Other methods (`query()`, `receive_response()`) assumed connection existed

#### 2. `ACPClient`
Legacy implementation used by the `run()` CLI function.

**Key characteristics**:
- Directly implements `EventEmitter`, `TerminalController`, `FileSystemController`
- Prints output directly to stdout
- Used for standalone CLI script execution

#### 3. `_SDKClientImplementation`
Internal implementation that adapts ACP events to SDK message queue.

**Key characteristics**:
- Extends same base classes as `ACPClient`
- Instead of printing, queues `Message` objects
- Used internally by `PyACPSDKClient`

---

## PR #2 Overview

**Branch**: `origin/feat/pyacp-sdk-client-refactoring`
**Commit**: `4da2ef1 - Implement PyACPSDKClient.connect() and refactor run() to use SDK client`

### What Does This PR Do?

This PR completes the implementation of `PyACPSDKClient` by:

1. **Implementing `PyACPSDKClient.connect()`** - Previously a stub
2. **Refactoring `run()` function** - Now uses `PyACPSDKClient` instead of direct protocol calls
3. **Refactoring `interactive_loop()`** - Now uses `PyACPSDKClient` instead of raw connection
4. **Improving error handling** - Better cleanup on connection failures
5. **Unifying the codebase** - Single code path through `PyACPSDKClient`

### The Big Picture

**Before PR #2**:
- Two separate code paths:
  - SDK path: `PyACPSDKClient` (incomplete, `connect()` was stub)
  - CLI path: Direct protocol calls in `run()` function
- Code duplication between paths
- `PyACPSDKClient` was unusable

**After PR #2**:
- Single unified path through `PyACPSDKClient`
- `run()` function delegates to `PyACPSDKClient`
- All connection logic centralized in `connect()` method
- Consistent error handling and cleanup

---

## Detailed Changes

### File Changed
- `src/pyacp/client/acp_client.py` (269 lines changed: +193, -76)

### Change 1: Implement `PyACPSDKClient.connect()` (Lines 211-320)

#### Before
```python
async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None:
    """
    Connect to the ACP agent with an optional initial prompt.

    Args:
        prompt: Optional initial prompt as a string or async iterable
    """
    pass  # ← Was a stub!
```

#### After
```python
async def connect(self, agent_command: str | list[str] | None = None) -> None:
    """
    Connect to the ACP agent and establish a session.

    Args:
        agent_command: Agent program path or command list. If None, uses options.agent_program
    """
    # 193 lines of actual implementation
```

#### What It Does

1. **Validates connection state** - Prevents double-connection
2. **Resolves agent command**:
   - From parameter, or
   - From `options.agent_program`
   - Handles both string and list formats
   - Special handling for non-executable Python scripts
3. **Spawns agent process** via `spawn_stdio_transport()`
4. **Creates client implementation** (`_SDKClientImplementation`)
5. **Initializes ACP connection**:
   - Sends `InitializeRequest` with protocol version
   - Declares client capabilities (filesystem, terminal)
6. **Creates session** via `newSession()`
7. **Sets model** (if specified)
8. **Error handling** - Cleans up resources on failure

#### Key Points to Review

- **Agent command resolution logic** (lines 221-239): Handles various input formats
- **Context manager storage** (line 200, 246-248): Stores `_transport_cm` for cleanup
- **Error handling** (lines 263-270, 277-284, 288-298): Try-catch blocks with cleanup
- **Cleanup method** (lines 305-320): `_cleanup_connection()` for error scenarios

---

### Change 2: Add Cleanup Helper (Lines 305-320)

**New method**: `_cleanup_connection()`

```python
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
```

#### Purpose
Ensures proper cleanup of connection and transport resources when initialization fails.

#### Key Points to Review
- **Exception suppression**: Should failures during cleanup be logged?
- **Resource nullification**: Sets references to `None` after cleanup

---

### Change 3: Enhanced `disconnect()` (Lines 425-448)

#### Before
```python
async def disconnect(self) -> None:
    """Disconnect from agent and clean up resources."""
    self._client_impl._flush()  # ← Could fail if _client_impl is None!

    if self._connection:
        # ... cleanup code ...
```

#### After
```python
async def disconnect(self) -> None:
    """Disconnect from agent and clean up resources."""
    if self._client_impl:  # ← Null check added!
        self._client_impl._flush()

    if self._connection:
        # ... cleanup code ...

    # NEW: Reset state
    self._connected = False
    self._session_id = None
    self._client_impl = None
```

#### Key Points to Review
- **Null safety**: Guards against calling methods on None
- **State reset**: Explicitly resets connection state
- **Idempotent**: Can be called multiple times safely

---

### Change 4: Refactored `interactive_loop()` (Lines 534-592)

#### Before (Old Signature)
```python
async def interactive_loop(conn: ClientSideConnection, session_id: str) -> None:
    # ...
    await conn.prompt(
        PromptRequest(
            sessionId=session_id,
            prompt=[acp_text_block(line)],
        )
    )
```

#### After (New Signature)
```python
async def interactive_loop(client: PyACPSDKClient) -> None:
    """
    Interactive loop for CLI usage with PyACPSDKClient.

    Args:
        client: Connected PyACPSDKClient instance
    """
    # ...
    await client.query(line, session_id=client._session_id or "default")

    # Receive and print messages
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                # ... handle other block types
```

#### What Changed
- **Parameter change**: Takes `PyACPSDKClient` instead of raw connection
- **Uses high-level API**: `client.query()` and `client.receive_response()`
- **Better message handling**: Processes different message types properly
- **Cancel uses SDK method**: `await client.interrupt()` instead of raw protocol

#### Key Points to Review
- **Message iteration**: Does the message receiving logic work correctly?
- **Block type handling**: Are all relevant block types handled?
- **Error messages**: Printed to stderr appropriately

---

### Change 5: Refactored `run()` Function (Lines 597-654)

#### Before
```python
async def run(argv: list[str]) -> int:
    # ... parse args ...

    try:
        async with spawn_stdio_transport(...) as (stdout, stdin, proc):
            client_impl = ACPClient()  # ← Direct protocol usage
            conn = ClientSideConnection(...)

            # Manually call initialize()
            init_resp = await conn.initialize(...)

            # Manually call newSession()
            session = await conn.newSession(...)

            # Manually set model
            await conn.setSessionModel(...)

            await interactive_loop(conn, session.sessionId)

            return 0
    except FileNotFoundError as exc:
        # ... error handling
```

#### After
```python
async def run(argv: list[str]) -> int:
    """
    Standalone CLI runner that uses PyACPSDKClient for all protocol operations.
    """
    # ... parse args ...

    # Build agent command
    agent_command = [program] + args

    # Create options
    options = PyACPAgentOptions(model=model_id, cwd=os.getcwd())

    # Create and connect client
    client = PyACPSDKClient(options)

    try:
        await client.connect(agent_command)  # ← Single call!
        await interactive_loop(client)
        await client.disconnect()
        return 0
    except FileNotFoundError as exc:
        # ... error handling
    except RuntimeError as exc:
        # ... error handling
    except Exception as exc:
        # ... error handling
    finally:
        # Ensure cleanup
        if client._connected:
            with contextlib.suppress(Exception):
                await client.disconnect()
```

#### What Changed
- **Simplified dramatically**: 86 lines → 61 lines
- **Single responsibility**: `run()` just sets up and uses SDK client
- **Better error handling**: More exception types caught
- **Guaranteed cleanup**: `finally` block ensures disconnection
- **Consistent code path**: Uses same code as library users

#### Key Points to Review
- **Error handling**: Are all relevant exceptions caught?
- **Finally block**: Is the nested exception suppression appropriate?
- **State check**: `if client._connected` - accessing private attribute, is this OK?

---

## Key Review Points

### 1. API Design

#### Signature Change
The `connect()` signature changed:
- **Before**: `async def connect(self, prompt: str | AsyncIterable[dict] | None = None)`
- **After**: `async def connect(self, agent_command: str | list[str] | None = None)`

**Question**: Is removing the `prompt` parameter a breaking change? Should it support both?

#### Agent Command Resolution
Lines 221-239 handle various agent command formats.

**Questions**:
- Is the logic for detecting non-executable scripts correct?
- Should there be validation that the agent program exists?

---

### 2. Resource Management

#### Context Manager Storage
Line 200 adds `self._transport_cm = None` and lines 246-248 store the context manager.

**Questions**:
- Is storing the context manager reference safe?
- Could this create lifecycle issues?

#### Cleanup Path
Two cleanup paths: `_cleanup_connection()` (for errors) and `disconnect()` (normal).

**Questions**:
- Is there any duplication between these?
- Should they share common logic?

---

### 3. Error Handling

#### Silent Exception Suppression
Many places use bare `except Exception: pass`:
- Lines 311-313, 317-319 (_cleanup_connection)
- Lines 435-437, 441-443 (disconnect)
- Lines 646-648 (run finally block)

**Questions**:
- Should these failures be logged?
- Are there cases where silent failure is dangerous?

#### Error Messages
New exception types in `run()`:
- `RuntimeError` for connection errors
- Generic `Exception` for unexpected errors

**Questions**:
- Are these exception types appropriate?
- Should custom exceptions be defined?

---

### 4. State Management

#### Connection State
The PR adds:
- Line 199: `self._connected = False`
- Line 304: `self._connected = True`
- Line 446: `self._connected = False` (in disconnect)

**Questions**:
- Is `_connected` always accurate?
- What happens if connect() partially succeeds?

#### State Reset in Disconnect
Lines 446-448 explicitly reset state.

**Questions**:
- Should this also reset `_message_queue`?
- Are there other state variables that should be reset?

---

### 5. Concurrency and Thread Safety

#### Message Queue
The `_message_queue` is shared between:
- `_SDKClientImplementation` (producer - may run in callback)
- `receive_response()` (consumer - runs in user's async task)

**Questions**:
- Is `asyncio.Queue` sufficient for thread safety?
- Could there be race conditions?

#### Transport Process
The agent runs in a subprocess, communicating via stdin/stdout.

**Questions**:
- What happens if the subprocess crashes mid-operation?
- Are there resource leaks if cleanup fails?

---

### 6. Testing Considerations

The PR only modifies production code, no test changes.

**Questions to consider**:
- Are there existing tests for `connect()`?
- How is the refactored `run()` function tested?
- Should there be tests for error paths (failed initialization, etc.)?
- Integration tests with real agents?

---

### 7. Documentation

The docstrings were updated, but:

**Questions**:
- Does the README need updates to reflect the signature change?
- Should there be migration notes for users of the old API?
- Are the examples still accurate?

---

### 8. Code Quality

#### Accessing Private Attributes
Line 642 in `run()`: `if client._connected:`

**Question**: Should there be a public `is_connected()` method?

#### Line 571: Session ID Fallback
```python
await client.query(line, session_id=client._session_id or "default")
```

**Question**: When would `_session_id` be None after successful connection? Should this be an error?

---

## Summary

### What This PR Achieves

✅ Completes the `PyACPSDKClient` implementation
✅ Unifies code paths (SDK and CLI now use same code)
✅ Improves error handling and resource cleanup
✅ Simplifies the `run()` function significantly
✅ Makes the SDK actually usable for library consumers

### Potential Concerns

⚠️ **Breaking change**: `connect()` signature changed
⚠️ **Silent error suppression**: Many exceptions swallowed without logging
⚠️ **Accessing private state**: `run()` checks `client._connected`
⚠️ **Test coverage**: No test updates in this PR
⚠️ **Documentation**: May need updates for API changes

### Recommended Review Focus

1. **Connection lifecycle**: Verify the connect/disconnect flow is correct
2. **Error paths**: Ensure cleanup happens in all failure scenarios
3. **Resource leaks**: Check subprocess and file descriptor handling
4. **API stability**: Consider the breaking change impact
5. **Concurrency**: Review async/queue interactions for race conditions

---

## Appendix: Testing the Changes

### Manual Testing Commands

```bash
# Test with Claude Code ACP
npm install -g @zed-industries/claude-code-acp
python src/pyacp/client/acp_client.py claude-code-acp

# Test with Codex ACP
npm install @zed-industries/codex-acp
python src/pyacp/client/acp_client.py codex-acp

# Test with environment model override
ACP_MODEL=claude-3-5-sonnet-20241022 python src/pyacp/client/acp_client.py claude-code-acp
```

### SDK Usage Test

```python
import asyncio
from pyacp.client.acp_client import PyACPSDKClient, PyACPAgentOptions

async def test_connection():
    options = PyACPAgentOptions(agent_program="claude-code-acp")
    client = PyACPSDKClient(options)

    try:
        await client.connect()
        await client.query("What is 2 + 2?")
        async for message in client.receive_response():
            print(message)
    finally:
        await client.disconnect()

asyncio.run(test_connection())
```

---

**Document Version**: 1.0
**Date**: Based on PR commit `4da2ef1`
**Reviewer**: [Your Name]
