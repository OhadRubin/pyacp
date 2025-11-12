"""Tests for configuration options."""

import pytest
from pathlib import Path
from pyacp.types.options import PyACPAgentOptions, PermissionMode


def test_pyacp_agent_options_defaults():
    """Test PyACPAgentOptions with default values."""
    options = PyACPAgentOptions()
    assert options.allowed_tools == []
    assert options.system_prompt is None
    assert options.permission_mode is None
    assert options.model is None
    assert options.env == {}


def test_pyacp_agent_options_with_values():
    """Test PyACPAgentOptions with custom values."""
    options = PyACPAgentOptions(
        allowed_tools=["Read", "Write"],
        permission_mode="acceptEdits",
        model="claude-3",
        cwd="/tmp",
        agent_program="claude-code-acp",
    )
    assert options.allowed_tools == ["Read", "Write"]
    assert options.permission_mode == "acceptEdits"
    assert options.model == "claude-3"
    assert options.cwd == "/tmp"
    assert options.agent_program == "claude-code-acp"


def test_pyacp_agent_options_with_path():
    """Test PyACPAgentOptions with Path object."""
    options = PyACPAgentOptions(cwd=Path("/tmp"))
    assert isinstance(options.cwd, Path)


def test_permission_mode_types():
    """Test valid PermissionMode values."""
    options1 = PyACPAgentOptions(permission_mode="default")
    options2 = PyACPAgentOptions(permission_mode="acceptEdits")
    options3 = PyACPAgentOptions(permission_mode="plan")
    options4 = PyACPAgentOptions(permission_mode="bypassPermissions")

    assert options1.permission_mode == "default"
    assert options2.permission_mode == "acceptEdits"
    assert options3.permission_mode == "plan"
    assert options4.permission_mode == "bypassPermissions"
