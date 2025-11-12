# PyACP

**PyACP** is a Python SDK for the [Agent Client Protocol (ACP)](https://github.com/anthropics/acp), providing a high-level, async-friendly interface for interacting with ACP-compatible agents. Build powerful agent-based applications with support for streaming messages, terminal operations, and filesystem capabilities.

## Features

- **Async/Await API**: Built on modern Python async patterns for efficient I/O
- **Streaming Messages**: Real-time message streaming with support for text, thinking blocks, and updates
- **Terminal Capabilities**: Create, manage, and interact with terminal sessions
- **Filesystem Operations**: Read and write text files with path safety guarantees
- **Session Management**: Maintain conversation context across multiple exchanges
- **Context Manager Support**: Clean resource management with async context managers
- **Interrupt Support**: Cancel long-running operations gracefully
- **Type-Safe**: Full type hints for better IDE support and code safety

## Requirements

- Python 3.12 or higher
- `agent-client-protocol>=0.6.3`

## Installation

Install PyACP using pip:

```bash
pip install pyacp
```

Or with uv:

```bash
uv add pyacp
```

## Quick Start

Here's a simple example to get you started:

```python
import asyncio
from pyacp.sdk.client import PyACPSDKClient, PyACPAgentOptions

async def main():
    # Configure the agent options
    options = PyACPAgentOptions(
        model="claude-sonnet-4-5",  # Optional: specify model
        cwd="/path/to/working/directory"  # Optional: set working directory
    )

    # Create and connect the client
    async with PyACPSDKClient(options) as client:
        await client.connect(["codex-acp"])  # Path to your ACP agent

        # Send a query and stream responses
        await client.query("What files are in the current directory?")

        async for message in client.receive_messages():
            if hasattr(message, 'text'):
                print(f"Agent: {message.text}")
            elif hasattr(message, 'thinking'):
                print(f"[Thinking]: {message.thinking}")

asyncio.run(main())
```

## Core Concepts

### PyACPSDKClient

The main client class that manages connections to ACP agents and handles protocol operations.

#### Key Methods

- **`connect(agent_command)`**: Establish connection to an ACP agent
- **`query(prompt)`**: Send a prompt to the agent (non-blocking)
- **`receive_messages()`**: Stream messages from the agent until end of turn
- **`interrupt()`**: Cancel the current agent operation
- **`disconnect()`**: Close the connection and cleanup resources

#### Example Usage

```python
from pyacp.sdk.client import PyACPSDKClient, PyACPAgentOptions

# Initialize with options
options = PyACPAgentOptions(
    model="claude-sonnet-4-5",
    cwd="/workspace",
    env={"DEBUG": "true"}
)

client = PyACPSDKClient(options)

# Connect to agent
await client.connect(["path/to/agent", "--arg1", "--arg2"])

# Send query
await client.query("Analyze this codebase")

# Receive streaming responses
async for message in client.receive_messages():
    # Handle different message types
    print(message)

# Cleanup
await client.disconnect()
```

### PyACPAgentOptions

Configuration options for the ACP agent connection.

#### Fields

- **`model`** (`str | None`): Model identifier to use (e.g., "claude-sonnet-4-5")
- **`cwd`** (`str | Path | None`): Working directory for the agent session
- **`env`** (`dict[str, str]`): Environment variables for the agent process
- **`max_turns`** (`int | None`): Maximum number of conversation turns
- **`agent_program`** (`str | None`): Path to ACP agent executable
- **`agent_args`** (`list[str]`): Arguments to pass to the agent program

### Message Types

PyACP uses typed message objects defined in `pyacp.core`:

#### TextBlock

Represents text content from the agent:

```python
@dataclass
class TextBlock:
    text: str
    timestamp: str  # Automatically added
```

#### ThinkingBlock

Represents agent reasoning (for models with thinking capability):

```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str = ""
    timestamp: str  # Automatically added
```

#### OtherUpdate

Represents protocol updates and events:

```python
@dataclass
class OtherUpdate:
    update_name: str
    update: dict[str, Any]
    timestamp: str  # Automatically added
```

## Advanced Usage

### Interactive CLI Example

```python
import asyncio
from pyacp.sdk.client import PyACPSDKClient, PyACPAgentOptions

async def interactive_loop(client: PyACPSDKClient):
    """Interactive command-line interface."""
    print("Type your message and press Enter. Commands: :cancel, :exit")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue
        if user_input in {":exit", ":quit"}:
            break
        if user_input == ":cancel":
            await client.interrupt()
            print("[Cancelled]")
            continue

        # Send query and stream responses
        await client.query(user_input)

        async for message in client.receive_messages():
            if hasattr(message, 'text'):
                print(f"\nAgent: {message.text}")
            elif hasattr(message, 'thinking'):
                print(f"\n[Thinking]: {message.thinking}")

async def main():
    options = PyACPAgentOptions(model="claude-sonnet-4-5")

    async with PyACPSDKClient(options) as client:
        await client.connect(["codex-acp"])
        await interactive_loop(client)

asyncio.run(main())
```

### Context Manager Pattern

PyACP supports async context managers for automatic cleanup:

```python
async with PyACPSDKClient(options) as client:
    await client.connect(["agent-command"])

    await client.query("Hello!")
    async for message in client.receive_messages():
        print(message)

    # Automatic disconnect when exiting the context
```

### Manual Connection Management

For more control, manage connections manually:

```python
client = PyACPSDKClient(options)

try:
    await client.connect(["agent-command"])

    await client.query("Process this task")
    async for message in client.receive_messages():
        handle_message(message)

finally:
    await client.disconnect()  # Always cleanup
```

### Error Handling

```python
from acp import RequestError

try:
    await client.connect(["agent-command"])
except FileNotFoundError:
    print("Agent program not found")
except RuntimeError as e:
    print(f"Connection error: {e}")

try:
    await client.query("Query text")
    async for message in client.receive_messages():
        process_message(message)
except RequestError as e:
    print(f"Request failed: {e.to_error_obj()}")
```

## Capabilities

### Terminal Operations

PyACP provides full terminal support through the ACP protocol:

- Create terminal sessions with custom commands and environment
- Capture stdout/stderr with automatic buffering
- Monitor exit codes and signals
- Release terminals when done

The terminal controller is built into the client and handles:
- UTF-8 character boundary truncation
- Output byte limits
- Background output capture
- Process lifecycle management

### Filesystem Operations

Secure filesystem operations with path validation:

- **Read text files**: Load file contents with optional line slicing
- **Write text files**: Save content with automatic directory creation
- **Path safety**: All paths must be absolute for security

Both operations are handled transparently through the ACP protocol.

## ACP Agent Compatibility

PyACP is compatible with ACP agents that implement the Agent Client Protocol. Popular agents include:

- **Codex ACP**: `npm install @zed-industries/codex-acp`
- **Claude Code ACP**: `npm install -g @zed-industries/claude-code-acp`

Example with Codex:

```bash
# Install Codex ACP agent
npm install -g @zed-industries/codex-acp

# Use with PyACP
python -c "
import asyncio
from pyacp.sdk.client import PyACPSDKClient, PyACPAgentOptions

async def main():
    async with PyACPSDKClient(PyACPAgentOptions()) as client:
        await client.connect(['codex-acp'])
        await client.query('List files in current directory')
        async for msg in client.receive_messages():
            print(msg)

asyncio.run(main())
"
```

## Development

### Project Structure

```
pyacp/
├── pyacp/
│   ├── sdk/
│   │   └── client.py          # Main SDK client
│   ├── capabilities/
│   │   ├── terminal.py        # Terminal operations
│   │   └── filesystem.py      # File operations
│   └── core.py                # Message types
├── examples/
│   └── interactive.py         # CLI example
└── scripts/
    └── *.sh                   # Test scripts
```

### Running Examples

The project includes an interactive CLI example:

```bash
# Clone the repository
git clone <repo-url>
cd pyacp

# Install dependencies
uv sync

# Run the interactive example
uv run python examples/interactive.py codex-acp
```

### Testing

Smoke test scripts are provided in the `scripts/` directory:

```bash
# Test with Codex ACP
./scripts/codex_smoketest.sh

# Test with Claude Code ACP
./scripts/opencode_smoketest.sh
```

## License

[Include your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [Agent Client Protocol](https://github.com/anthropics/acp)
- [ACP Python Library](https://github.com/anthropics/agent-client-protocol-python)

## Changelog

### 0.1.0 (Initial Release)

- Initial implementation of PyACP SDK
- Support for streaming messages
- Terminal and filesystem capabilities
- Async context manager support
- Interactive CLI example

---

Made with the Agent Client Protocol
