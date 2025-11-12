"""Tests for terminal utilities."""

import pytest
import asyncio
from unittest.mock import Mock
from pyacp.utils.terminal import TerminalInfo


@pytest.fixture
def mock_process():
    """Create a mock subprocess."""
    process = Mock(spec=asyncio.subprocess.Process)
    process.returncode = None
    return process


def test_terminal_info_creation(mock_process):
    """Test TerminalInfo creation."""
    terminal = TerminalInfo(
        terminal_id="term-123",
        process=mock_process,
        output_byte_limit=1000
    )
    assert terminal.terminal_id == "term-123"
    assert terminal.process == mock_process
    assert terminal.output_byte_limit == 1000
    assert terminal.truncated is False
    assert terminal.exit_code is None


def test_terminal_info_add_output(mock_process):
    """Test adding output to terminal."""
    terminal = TerminalInfo(terminal_id="term-123", process=mock_process)
    terminal.add_output(b"Hello ")
    terminal.add_output(b"World")

    output = terminal.get_output()
    assert output == "Hello World"


def test_terminal_info_output_limit(mock_process):
    """Test output byte limit enforcement."""
    terminal = TerminalInfo(
        terminal_id="term-123",
        process=mock_process,
        output_byte_limit=10
    )

    # Add more than the limit
    terminal.add_output(b"0123456789")
    terminal.add_output(b"ABCDEFGHIJ")

    output = terminal.get_output()
    assert len(output.encode('utf-8')) <= 10
    assert terminal.truncated is True


def test_terminal_info_utf8_boundary(mock_process):
    """Test UTF-8 character boundary handling."""
    terminal = TerminalInfo(
        terminal_id="term-123",
        process=mock_process,
        output_byte_limit=15
    )

    # Add data with multi-byte UTF-8 characters
    terminal.add_output("Hello 世界".encode('utf-8'))
    terminal.add_output(" More text".encode('utf-8'))

    # Should truncate without breaking UTF-8 characters
    output = terminal.get_output()
    # Output should be valid UTF-8
    assert isinstance(output, str)
