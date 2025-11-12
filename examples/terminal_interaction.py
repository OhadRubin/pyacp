#!/usr/bin/env python3
"""Example showing terminal/command execution through ACP."""

import asyncio
from pyacp import query, PyACPAgentOptions


async def main():
    """Ask agent to run terminal commands."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        allowed_tools=["Bash"],
        permission_mode="bypassPermissions",
    )

    async for message in query(
        prompt="Run 'ls -la' and show me the results",
        options=options
    ):
        print(message)


if __name__ == "__main__":
    asyncio.run(main())
