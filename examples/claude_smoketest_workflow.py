#!/usr/bin/env python3
"""Example replicating claude_smoketest.sh workflow using PyACP SDK.

This example demonstrates:
1. Simple file editing operation
2. Receiving and processing agent responses

Based on scripts/claude_smoketest.sh
"""

import asyncio
from pathlib import Path

from pyacp import PyACPSDKClient, PyACPAgentOptions
from pyacp.types.messages import AssistantMessage, ResultMessage
from pyacp.types.content import TextBlock, ThinkingBlock


async def main():
    """Run the claude smoketest workflow using PyACP SDK."""

    # Setup working directory with mini_terminal files
    work_dir = Path(__file__).parent.parent / "scripts"

    print("=" * 80)
    print("Claude Smoketest Workflow Example")
    print("=" * 80)
    print(f"\nWorking directory: {work_dir}")
    print(f"Files: mini_terminal.py, mini_terminal_w_prints.py")
    print()

    # Configure SDK client
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        cwd=work_dir,
        env={
            "CLAUDE_CODE_ACTION": "bypassPermissions",
            "ANTHROPIC_MODEL": "worker-claude-sonnet-4-5",
            "ANTHROPIC_SMALL_FAST_MODEL": "worker-claude-haiku-4-5",
            "MAX_THINKING_TOKENS": "10000",
            "ANTHROPIC_BASE_URL": "http://0.0.0.0:4000",
            "ANTHROPIC_AUTH_TOKEN": "sk-1234",
            "ACP_MODEL": "worker-claude-sonnet-4-5",
        }
    )

    async with PyACPSDKClient(options=options) as client:

        # ========================================================================
        # Task 1: Remove print statements from mini_terminal.py
        # ========================================================================
        print("\n" + "=" * 80)
        print("TASK 1: Remove print statements from mini_terminal.py")
        print("=" * 80)
        print("\nSending: 'please remove all the print statements from mini_terminal.py'\n")

        await client.query("please remove all the print statements from mini_terminal.py")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ThinkingBlock):
                        print(f"[Thinking] {block.thinking[:200]}...")
                    elif isinstance(block, TextBlock):
                        print(f"[Agent] {block.text}")
            elif isinstance(message, ResultMessage):
                print(f"\n[Result] Task completed in {message.duration_ms}ms")
                print(f"         Turns: {message.num_turns}, Error: {message.is_error}")

        print("\n" + "=" * 80)
        print("Workflow Complete!")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
