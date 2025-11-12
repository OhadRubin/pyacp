"""Pytest configuration and fixtures for end-to-end tests."""

import shutil
import pytest
from pathlib import Path


def is_agent_available(agent_program: str) -> bool:
    """Check if an agent program is available in PATH."""
    return shutil.which(agent_program) is not None


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "claude_code_acp: tests requiring Claude Code ACP"
    )
    config.addinivalue_line(
        "markers", "codex_acp: tests requiring Codex ACP"
    )
    config.addinivalue_line(
        "markers", "opencode: tests requiring OpenCode"
    )
    config.addinivalue_line(
        "markers", "gemini: tests requiring Gemini with ACP support"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests (may be slow)"
    )


@pytest.fixture
def claude_code_env():
    """Environment variables for Claude Code ACP."""
    return {
        "CLAUDE_CODE_ACTION": "bypassPermissions",
        "ANTHROPIC_MODEL": "worker-claude-sonnet-4-5",
        "ANTHROPIC_SMALL_FAST_MODEL": "worker-claude-haiku-4-5",
        "MAX_THINKING_TOKENS": "10000",
        "ANTHROPIC_BASE_URL": "http://0.0.0.0:4000",
        "ANTHROPIC_AUTH_TOKEN": "sk-1234",
        "ACP_MODEL": "worker-claude-sonnet-4-5",
    }


@pytest.fixture
def codex_env():
    """Environment variables for Codex ACP."""
    return {
        "CODEX_HOME": str(Path(__file__).parent.parent.parent / "configs" / "codex_home"),
        "LITELLM_KEY": "sk-1234",
    }


@pytest.fixture
def opencode_env():
    """Environment variables for OpenCode."""
    return {
        "OPENCODE_CONFIG": str(Path(__file__).parent.parent.parent / "configs" / "opencode.json"),
        "MAX_THINKING_TOKENS": "10000",
        "ACP_MODEL": "openrouter/gemini-2.5-pro",
    }


@pytest.fixture
def gemini_env():
    """Environment variables for Gemini."""
    return {
        "GOOGLE_GEMINI_BASE_URL": "http://localhost:4000",
        "GEMINI_API_KEY": "sk-1234",
    }


@pytest.fixture
def test_prompts():
    """Standard test prompts for all agents."""
    return [
        "Say hello and tell me what you can do",
        "What is 2 + 2?",
        "List the files in the current directory",
    ]
