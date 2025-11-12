#!/usr/bin/env python3
"""Basic query example using the query() function."""

import asyncio
from pyacp import query, PyACPAgentOptions


async def main():
    """Run a simple query to an ACP agent."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",  # or "codex-acp", "opencode", etc.
        permission_mode="bypassPermissions",
    )

    print("Sending query to agent...")
    async for message in query(
        prompt="What is 2 + 2?",
        options=options
    ):
        print(f"Received: {message}")


if __name__ == "__main__":
    asyncio.run(main())
