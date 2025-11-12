#!/usr/bin/env python3
"""Minimal terminal test for ACP client."""

import asyncio
import os


async def test_shell_command():
    """Test executing a shell command with subprocess."""

    # Test 1: Simple shell script
    full_command = 'for i in $(seq 1 3); do echo "Count: $i"; sleep 0.5; done'
    cmd = ["/bin/sh", "-c", full_command]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    # Test 2: Simple command with args
    cmd = ["/bin/sh", "-c", "ls -la"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    # Test 3: Echo command
    cmd = ["/bin/sh", "-c", 'echo "Hello from shell: $USER"']

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    # Test 4: Command chaining with &&
    cmd = ["/bin/sh", "-c", 'echo "First" && echo "Second" && echo "Third"']

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    # Test 5: Piping
    cmd = ["/bin/sh", "-c", 'echo -e "apple\\nbanana\\ncherry" | grep "an"']

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    # Test 6: Complex pipe chain
    cmd = ["/bin/sh", "-c", "ls -la | head -5 | tail -3"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()


# cp todo.sh $LOGDIR/todo.sh

if __name__ == "__main__":
    asyncio.run(test_shell_command())
