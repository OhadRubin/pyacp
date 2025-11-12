# PyACP Quickstart Guide

## Installation

Install PyACP using pip or uv:

```bash
# Using pip
pip install pyacp

# Using uv
uv add pyacp
```

## Prerequisites

You'll need an ACP-compatible agent installed. PyACP supports:

- **Claude Code ACP**: `npm install -g @zed-industries/claude-code-acp`
- **Codex ACP**: `npm install -g @zed-industries/codex-acp`
- **OpenCode**: Install from https://opencode.ai
- **Gemini**: Use with ACP support

## Basic Usage

### Simple Query

The simplest way to use PyACP is with the `query()` function:

```python
import asyncio
from pyacp import query, PyACPAgentOptions

async def main():
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
    )

    async for message in query(
        prompt="What is 2 + 2?",
        options=options
    ):
        print(message)

asyncio.run(main())
```

### Continuous Conversation

For multi-turn conversations, use `PyACPSDKClient`:

```python
import asyncio
from pyacp import PyACPSDKClient, PyACPAgentOptions

async def main():
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
    )

    async with PyACPSDKClient(options=options) as client:
        # First question
        await client.query("What's the capital of France?")
        async for msg in client.receive_response():
            print(msg)

        # Follow-up - agent remembers context!
        await client.query("What's its population?")
        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
```

## Configuration

### Permission Modes

Control how the agent handles permissions:

- `"default"`: Standard permission behavior (asks for approval)
- `"acceptEdits"`: Auto-accept file edits
- `"plan"`: Planning mode - no execution
- `"bypassPermissions"`: Bypass all permission checks (use with caution)

### Allowed Tools

Restrict which tools the agent can use:

```python
options = PyACPAgentOptions(
    agent_program="claude-code-acp",
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits",
)
```

### Working Directory

Specify the working directory for the agent:

```python
from pathlib import Path

options = PyACPAgentOptions(
    agent_program="claude-code-acp",
    cwd="/path/to/project",  # or Path("/path/to/project")
)
```

### Environment Variables

Pass custom environment variables:

```python
options = PyACPAgentOptions(
    agent_program="codex-acp",
    env={
        "CODEX_HOME": "configs/codex_home",
        "API_KEY": "your-key-here",
    }
)
```

## Next Steps

- See [examples/](../examples/) for more usage examples
- Read [api_reference.md](api_reference.md) for complete API documentation
- Check out [claude_client_sdk.md](claude_client_sdk.md) for Claude SDK compatibility details
