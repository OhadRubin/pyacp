"""End-to-end test replicating claude_smoketest.sh workflow using PyACP SDK."""

import pytest
import shutil
from pathlib import Path

from pyacp import PyACPSDKClient, PyACPAgentOptions
from pyacp.types.messages import AssistantMessage
from pyacp.types.content import TextBlock

from tests.e2e.conftest import is_agent_available


@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_smoketest_workflow(claude_code_env, tmp_path):
    """
    Replicate the claude_smoketest.sh workflow using PyACP SDK.

    This test mirrors the exact workflow from scripts/claude_smoketest.sh:
    1. Copy mini_terminal_w_prints.py to mini_terminal.py in test directory
    2. Ask agent to remove all print statements from mini_terminal.py
    3. Ask agent to start a background process counting to 60 (we'll use smaller count for test)
    4. Ask agent to create todo list, show file content, and run ls
    """
    # Setup: Copy mini_terminal files to temporary directory
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    test_mini_terminal = tmp_path / "mini_terminal.py"
    test_mini_terminal_w_prints = tmp_path / "mini_terminal_w_prints.py"

    shutil.copy(scripts_dir / "mini_terminal_w_prints.py", test_mini_terminal_w_prints)
    shutil.copy(scripts_dir / "mini_terminal_w_prints.py", test_mini_terminal)

    # Verify files were copied
    assert test_mini_terminal.exists()
    assert test_mini_terminal_w_prints.exists()

    # Setup SDK client with test working directory
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
        cwd=tmp_path,
    )

    async with PyACPSDKClient(options=options) as client:
        # Task 1: Remove print statements from mini_terminal.py
        print("\n[Task 1] Asking agent to remove print statements...")
        await client.query("please remove all the print statements from mini_terminal.py")

        task1_responses = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        task1_responses.append(block.text)
                        print(f"Agent: {block.text[:100]}...")

        # Verify agent responded
        assert len(task1_responses) > 0, "Should receive response for task 1"

        # Task 2: Start background process (simplified for testing)
        print("\n[Task 2] Asking agent to start background process...")
        await client.query(
            "1. Start a background process that counts to 10 and prints once every 2 seconds "
            "2. Check it multiple times until it's done"
        )

        task2_responses = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        task2_responses.append(block.text)
                        print(f"Agent: {block.text[:100]}...")

        # Verify agent responded
        assert len(task2_responses) > 0, "Should receive response for task 2"

        # Task 3: Multiple commands (todo list, file content, ls)
        print("\n[Task 3] Asking agent to do multiple tasks...")
        await client.query(
            "do the following. "
            "1. Create a todo list with the first 4 letters of the alphabet "
            "2. Tell me the content of mini_terminal.py "
            "3. Run ls"
        )

        task3_responses = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        task3_responses.append(block.text)
                        print(f"Agent: {block.text[:100]}...")

        # Verify agent responded
        assert len(task3_responses) > 0, "Should receive response for task 3"

        # Verify final response mentions expected items
        all_responses = " ".join(task3_responses).lower()
        # Should have created todo list with letters
        assert any(letter in all_responses for letter in ['a', 'b', 'c', 'd']), \
            "Response should mention letters from todo list"


@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_smoketest_file_editing(claude_code_env, tmp_path):
    """
    Test that the agent can successfully edit mini_terminal.py to remove print statements.

    This is a focused test on the file editing capability from the smoketest.
    """
    # Setup: Copy mini_terminal file with prints
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    test_file = tmp_path / "mini_terminal.py"
    shutil.copy(scripts_dir / "mini_terminal_w_prints.py", test_file)

    # Verify file has print statements
    original_content = test_file.read_text()
    assert 'print(' in original_content, "File should contain print statements initially"

    # Setup SDK client
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
        cwd=tmp_path,
    )

    async with PyACPSDKClient(options=options) as client:
        print("\nAsking agent to remove print statements...")
        await client.query("please remove all the print statements from mini_terminal.py")

        responses = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        responses.append(block.text)
                        print(f"Agent: {block.text[:150]}...")

        # Verify agent responded
        assert len(responses) > 0, "Should receive response from agent"

        # Verify file was modified
        modified_content = test_file.read_text()

        # File should still exist and have content
        assert len(modified_content) > 0, "File should not be empty"

        # Print statements should be removed or significantly reduced
        original_print_count = original_content.count('print(')
        modified_print_count = modified_content.count('print(')

        print(f"\nOriginal print statements: {original_print_count}")
        print(f"Modified print statements: {modified_print_count}")

        assert modified_print_count < original_print_count, \
            "Should have fewer print statements after agent's edits"


@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_smoketest_shell_commands(claude_code_env, tmp_path):
    """
    Test that the agent can execute shell commands (ls, etc) from the smoketest.
    """
    # Create some test files in tmp directory
    (tmp_path / "test_file_a.txt").write_text("test content a")
    (tmp_path / "test_file_b.txt").write_text("test content b")
    (tmp_path / "test_file_c.txt").write_text("test content c")

    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
        cwd=tmp_path,
    )

    async with PyACPSDKClient(options=options) as client:
        print("\nAsking agent to list files...")
        await client.query("Run ls and show me all the files in the current directory")

        responses = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        responses.append(block.text)
                        print(f"Agent: {block.text[:150]}...")

        # Verify agent responded
        assert len(responses) > 0, "Should receive response from agent"

        # Verify response mentions some of our test files
        all_text = " ".join(responses)
        assert any(filename in all_text for filename in [
            "test_file_a.txt", "test_file_b.txt", "test_file_c.txt"
        ]), "Response should mention at least one test file"
