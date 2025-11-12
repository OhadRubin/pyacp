# PyACP API Reference

## Client Classes

### `PyACPSDKClient`

High-level SDK client that maintains conversation sessions across multiple exchanges.

```python
from pyacp import PyACPSDKClient, PyACPAgentOptions

async with PyACPSDKClient(options=options) as client:
    await client.query("Hello")
    async for msg in client.receive_response():
        print(msg)
```

#### Methods

**`__init__(options: PyACPAgentOptions | None = None)`**
- Initialize the client with optional configuration

**`async connect(prompt: str | AsyncIterable[dict] | None = None)`**
- Connect to the ACP agent with an optional initial prompt

**`async query(prompt: str | AsyncIterable[dict], session_id: str = "default")`**
- Send a new request in streaming mode

**`async receive_messages() -> AsyncIterator[Message]`**
- Receive all messages from Claude as an async iterator

**`async receive_response() -> AsyncIterator[Message]`**
- Receive messages until and including a ResultMessage

**`async interrupt()`**
- Send interrupt signal (only works in streaming mode)

**`async disconnect()`**
- Disconnect from Claude and clean up resources

## Functions

### `query()`

Create a new session and query the agent (convenience function).

```python
async for message in query(
    prompt="Hello!",
    options=PyACPAgentOptions(agent_program="claude-code-acp")
):
    print(message)
```

**Parameters:**
- `prompt`: str | AsyncIterable[dict] - The input prompt
- `options`: PyACPAgentOptions | None - Optional configuration

**Returns:** AsyncIterator[Message]

## Types

### `PyACPAgentOptions`

Configuration options for ACP agent queries.

```python
@dataclass
class PyACPAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    permission_mode: PermissionMode | None = None
    model: str | None = None
    cwd: str | Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    agent_program: str | None = None
    agent_args: list[str] = field(default_factory=list)
```

### `PermissionMode`

```python
PermissionMode = Literal[
    "default",
    "acceptEdits",
    "plan",
    "bypassPermissions"
]
```

### Message Types

**`UserMessage`**
```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

**`AssistantMessage`**
```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

**`SystemMessage`**
```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

**`ResultMessage`**
```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
```

### Content Block Types

**`TextBlock`**
```python
@dataclass
class TextBlock:
    text: str
```

**`ThinkingBlock`**
```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str = ""
```

**`ToolUseBlock`**
```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

**`ToolResultBlock`**
```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

## Utility Classes

### `TerminalInfo`

Terminal management utility for tracking subprocess output.

```python
@dataclass
class TerminalInfo:
    terminal_id: str
    process: asyncio.subprocess.Process
    output_buffer: bytearray
    output_byte_limit: int | None = None
    truncated: bool = False
    exit_code: int | None = None
    signal: str | None = None
```

**Methods:**
- `add_output(data: bytes)` - Add output data with UTF-8 boundary handling
- `get_output() -> str` - Get the current output as a string
