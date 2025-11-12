# Simple ACP Client

**Simple ACP Client** is a Python SDK for the [Agent Client Protocol (ACP)](https://github.com/agentclientprotocol/agent-client-protocol), providing a high-level, async-friendly interface for interacting with ACP-compatible agents. Build powerful agent-based applications with support for streaming messages, terminal operations, and filesystem capabilities.

## Features

- A familiar interface similar to [Claude Agent SDK](https://docs.claude.com/en/docs/agent-sdk/overview)
- Can be used with any ACP compatible executable such as [Claude Code (via the Zed adapter)](https://github.com/zed-industries/claude-code-acp), [Codex-CLI (via the Zed adapter)](https://github.com/zed-industries/codex-acp), Gemini CLI, or OpenCode.
  
## Requirements

- Python 3.12 or higher
- `agent-client-protocol>=0.6.3`

## Installation

Install Simple ACP Client using pip:

```bash
pip install simple-acp-client
```

Or with uv:

```bash
uv add simple-acp-client
```

## Quick Start


Here's a simple example to get you started:

```python
import asyncio
from simple_acp_client.sdk.client import PyACPSDKClient, PyACPAgentOptions

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
from simple_acp_client.sdk.client import PyACPSDKClient, PyACPAgentOptions

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

**Capabilities:** Terminal (create/manage sessions, buffer output, exit/signals) and secure filesystem (read/write text files, absolute paths) are supported natively via the ACP protocol.

## ACP Agent Compatibility

PyACP is compatible with ACP agents that implement the Agent Client Protocol. Popular agents include:

- **Codex ACP**: `npm install @zed-industries/codex-acp`
- **Claude Code ACP**: `npm install -g @zed-industries/claude-code-acp`

# TODO
- Right now the code in scripts always gives full capabilities to the agent, so only run it in docker/heavy sandboxing.