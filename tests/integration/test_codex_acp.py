"""Integration tests for Codex ACP."""

import pytest
import os
from pyacp import query, PyACPAgentOptions


@pytest.mark.skipif(
    not os.path.exists("/usr/local/bin/codex-acp") and
    not os.path.exists(os.path.expanduser("~/.local/bin/codex-acp")),
    reason="codex-acp not installed"
)
@pytest.mark.asyncio
async def test_codex_simple_query():
    """Test simple query to Codex ACP."""
    options = PyACPAgentOptions(
        agent_program="codex-acp",
        env={"CODEX_HOME": "configs/codex_home"},
    )

    response_count = 0
    async for message in query(prompt="Say 'Hello'", options=options):
        response_count += 1

    assert response_count > 0
