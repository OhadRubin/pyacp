"""Integration tests for Claude Code ACP."""

import pytest
import os
from pyacp import query, PyACPAgentOptions


@pytest.mark.skipif(
    not os.path.exists("/usr/local/bin/claude-code-acp") and
    not os.path.exists(os.path.expanduser("~/.local/bin/claude-code-acp")),
    reason="claude-code-acp not installed"
)
@pytest.mark.asyncio
async def test_claude_code_simple_query():
    """Test simple query to Claude Code ACP."""
    options = PyACPAgentOptions(
        agent_program="claude-code-acp",
        permission_mode="bypassPermissions",
    )

    response_count = 0
    async for message in query(prompt="Say 'Hello'", options=options):
        response_count += 1

    assert response_count > 0
