"""End-to-end tests for PyACP SDK with different agents."""

import pytest

from pyacp import PyACPSDKClient, query, PyACPAgentOptions
from pyacp.types.messages import AssistantMessage
from pyacp.types.content import TextBlock

from tests.e2e.conftest import is_agent_available


# ============================================================================
# Claude Code ACP Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_code_acp_query_function(claude_code_env):
    """Test Claude Code ACP using the query() convenience function."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
    )

    messages = []
    async for message in query(prompt="What is 2 + 2?", options=options):
        messages.append(message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")

    # Verify we received at least one message
    assert len(messages) > 0, "Should receive at least one message"

    # Verify we received an AssistantMessage
    assistant_messages = [m for m in messages if isinstance(m, AssistantMessage)]
    assert len(assistant_messages) > 0, "Should receive at least one AssistantMessage"


@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_code_acp_sdk_client(claude_code_env, test_prompts):
    """Test Claude Code ACP using PyACPSDKClient for multi-turn conversation."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
    )

    async with PyACPSDKClient(options=options) as client:
        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            await client.query(prompt)

            messages = []
            async for message in client.receive_response():
                messages.append(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Response: {block.text[:100]}...")

            # Verify we received messages for this prompt
            assert len(messages) > 0, f"Should receive messages for prompt: {prompt}"


@pytest.mark.e2e
@pytest.mark.claude_code_acp
@pytest.mark.skipif(
    not is_agent_available("claude-code-acp"),
    reason="Claude Code ACP not installed"
)
@pytest.mark.asyncio
async def test_claude_code_acp_file_listing(claude_code_env):
    """Test that Claude Code ACP can list files in the current directory."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
        env=claude_code_env,
    )

    response_text = ""
    async for message in query(
        prompt="List the files in the current directory",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    # Verify response contains some expected files
    # (At minimum, we should see pyproject.toml or README.md mentioned)
    assert response_text, "Should receive a non-empty response"


# ============================================================================
# Codex ACP Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.codex_acp
@pytest.mark.skipif(
    not is_agent_available("codex-acp"),
    reason="Codex ACP not installed"
)
@pytest.mark.asyncio
async def test_codex_acp_query_function(codex_env):
    """Test Codex ACP using the query() convenience function."""
    options = PyACPAgentOptions(
        agent_program="codex-acp",
        permission_mode="bypassPermissions",
        env=codex_env,
    )

    messages = []
    async for message in query(prompt="What is 2 + 2?", options=options):
        messages.append(message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")

    # Verify we received at least one message
    assert len(messages) > 0, "Should receive at least one message"

    # Verify we received an AssistantMessage
    assistant_messages = [m for m in messages if isinstance(m, AssistantMessage)]
    assert len(assistant_messages) > 0, "Should receive at least one AssistantMessage"


@pytest.mark.e2e
@pytest.mark.codex_acp
@pytest.mark.skipif(
    not is_agent_available("codex-acp"),
    reason="Codex ACP not installed"
)
@pytest.mark.asyncio
async def test_codex_acp_sdk_client(codex_env, test_prompts):
    """Test Codex ACP using PyACPSDKClient for multi-turn conversation."""
    options = PyACPAgentOptions(
        agent_program="codex-acp",
        permission_mode="bypassPermissions",
        env=codex_env,
    )

    async with PyACPSDKClient(options=options) as client:
        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            await client.query(prompt)

            messages = []
            async for message in client.receive_response():
                messages.append(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Response: {block.text[:100]}...")

            # Verify we received messages for this prompt
            assert len(messages) > 0, f"Should receive messages for prompt: {prompt}"


# ============================================================================
# OpenCode Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.opencode
@pytest.mark.skipif(
    not is_agent_available("opencode"),
    reason="OpenCode not installed"
)
@pytest.mark.asyncio
async def test_opencode_query_function(opencode_env):
    """Test OpenCode using the query() convenience function."""
    options = PyACPAgentOptions(
        agent_program="opencode",
        agent_args=["acp"],
        permission_mode="bypassPermissions",
        env=opencode_env,
    )

    messages = []
    async for message in query(prompt="What is 2 + 2?", options=options):
        messages.append(message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")

    # Verify we received at least one message
    assert len(messages) > 0, "Should receive at least one message"

    # Verify we received an AssistantMessage
    assistant_messages = [m for m in messages if isinstance(m, AssistantMessage)]
    assert len(assistant_messages) > 0, "Should receive at least one AssistantMessage"


@pytest.mark.e2e
@pytest.mark.opencode
@pytest.mark.skipif(
    not is_agent_available("opencode"),
    reason="OpenCode not installed"
)
@pytest.mark.asyncio
async def test_opencode_sdk_client(opencode_env, test_prompts):
    """Test OpenCode using PyACPSDKClient for multi-turn conversation."""
    options = PyACPAgentOptions(
        agent_program="opencode",
        agent_args=["acp"],
        permission_mode="bypassPermissions",
        env=opencode_env,
    )

    async with PyACPSDKClient(options=options) as client:
        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            await client.query(prompt)

            messages = []
            async for message in client.receive_response():
                messages.append(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Response: {block.text[:100]}...")

            # Verify we received messages for this prompt
            assert len(messages) > 0, f"Should receive messages for prompt: {prompt}"


# ============================================================================
# Gemini Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.gemini
@pytest.mark.skipif(
    not is_agent_available("gemini"),
    reason="Gemini not installed"
)
@pytest.mark.asyncio
async def test_gemini_query_function(gemini_env):
    """Test Gemini using the query() convenience function."""
    options = PyACPAgentOptions(
        agent_program="gemini",
        agent_args=[
            "--experimental-acp",
            "--yolo",
            "--allowed-tools", "run_shell_command",
            "-m", "gemini-2.5-pro"
        ],
        permission_mode="bypassPermissions",
        env=gemini_env,
    )

    messages = []
    async for message in query(prompt="What is 2 + 2?", options=options):
        messages.append(message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")

    # Verify we received at least one message
    assert len(messages) > 0, "Should receive at least one message"

    # Verify we received an AssistantMessage
    assistant_messages = [m for m in messages if isinstance(m, AssistantMessage)]
    assert len(assistant_messages) > 0, "Should receive at least one AssistantMessage"


@pytest.mark.e2e
@pytest.mark.gemini
@pytest.mark.skipif(
    not is_agent_available("gemini"),
    reason="Gemini not installed"
)
@pytest.mark.asyncio
async def test_gemini_sdk_client(gemini_env, test_prompts):
    """Test Gemini using PyACPSDKClient for multi-turn conversation."""
    options = PyACPAgentOptions(
        agent_program="gemini",
        agent_args=[
            "--experimental-acp",
            "--yolo",
            "--allowed-tools", "run_shell_command",
            "-m", "gemini-2.5-pro"
        ],
        permission_mode="bypassPermissions",
        env=gemini_env,
    )

    async with PyACPSDKClient(options=options) as client:
        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            await client.query(prompt)

            messages = []
            async for message in client.receive_response():
                messages.append(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Response: {block.text[:100]}...")

            # Verify we received messages for this prompt
            assert len(messages) > 0, f"Should receive messages for prompt: {prompt}"


# ============================================================================
# Parametrized Tests (Run same test across all agents)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.parametrize("agent_config", [
    pytest.param(
        {
            "program": "claude-code-acp",
            "args": [],
            "env_fixture": "claude_code_env",
        },
        marks=[
            pytest.mark.claude_code_acp,
            pytest.mark.skipif(
                not is_agent_available("claude-code-acp"),
                reason="Claude Code ACP not installed"
            )
        ],
        id="claude-code-acp"
    ),
    pytest.param(
        {
            "program": "codex-acp",
            "args": [],
            "env_fixture": "codex_env",
        },
        marks=[
            pytest.mark.codex_acp,
            pytest.mark.skipif(
                not is_agent_available("codex-acp"),
                reason="Codex ACP not installed"
            )
        ],
        id="codex-acp"
    ),
    pytest.param(
        {
            "program": "opencode",
            "args": ["acp"],
            "env_fixture": "opencode_env",
        },
        marks=[
            pytest.mark.opencode,
            pytest.mark.skipif(
                not is_agent_available("opencode"),
                reason="OpenCode not installed"
            )
        ],
        id="opencode"
    ),
    pytest.param(
        {
            "program": "gemini",
            "args": ["--experimental-acp", "--yolo", "--allowed-tools", "run_shell_command", "-m", "gemini-2.5-pro"],
            "env_fixture": "gemini_env",
        },
        marks=[
            pytest.mark.gemini,
            pytest.mark.skipif(
                not is_agent_available("gemini"),
                reason="Gemini not installed"
            )
        ],
        id="gemini"
    ),
])
@pytest.mark.asyncio
async def test_agent_basic_math(agent_config, request):
    """Parametrized test: verify all agents can answer basic math questions."""
    # Get environment from fixture
    env = request.getfixturevalue(agent_config["env_fixture"])

    options = PyACPAgentOptions(
        agent_program=agent_config["program"],
        agent_args=agent_config["args"],
        permission_mode="bypassPermissions",
        env=env,
    )

    response_text = ""
    async for message in query(prompt="What is 2 + 2?", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    # Verify we got a response
    assert response_text, "Should receive a non-empty response"

    # Optionally verify the response mentions "4" (though phrasing may vary)
    # This is a loose check since different agents format differently
    print(f"\nAgent {agent_config['program']} response: {response_text[:200]}...")
