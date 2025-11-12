#!/usr/bin/env python3
"""Streaming conversation example using PyACPSDKClient."""

import asyncio
from pyacp import PyACPSDKClient, PyACPAgentOptions, AssistantMessage, TextBlock


async def main():
    """Have a multi-turn conversation with an ACP agent."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
    )

    async with PyACPSDKClient(options=options) as client:
        # First question
        print("Asking: What's the capital of France?")
        await client.query("What's the capital of France?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Agent: {block.text}")

        # Follow-up question - agent remembers context
        print("\nAsking follow-up: What's the population?")
        await client.query("What's the population of that city?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Agent: {block.text}")


if __name__ == "__main__":
    asyncio.run(main())
