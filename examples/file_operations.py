#!/usr/bin/env python3
"""Example showing file read/write operations through ACP."""

import asyncio
from pyacp import query, PyACPAgentOptions


async def main():
    """Ask agent to perform file operations."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        allowed_tools=["Read", "Write"],
        permission_mode="acceptEdits",
    )

    async for message in query(
        prompt="Create a file called hello.txt with the content 'Hello, World!'",
        options=options
    ):
        print(message)


if __name__ == "__main__":
    asyncio.run(main())
