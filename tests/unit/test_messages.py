"""Tests for message types."""

import pytest
from pyacp.types.messages import (
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
)
from pyacp.types.content import TextBlock


def test_user_message_with_string():
    """Test UserMessage with string content."""
    msg = UserMessage(content="Hello")
    assert msg.content == "Hello"


def test_user_message_with_blocks():
    """Test UserMessage with content blocks."""
    blocks = [TextBlock(text="Hello")]
    msg = UserMessage(content=blocks)
    assert len(msg.content) == 1
    assert isinstance(msg.content[0], TextBlock)


def test_assistant_message():
    """Test AssistantMessage."""
    blocks = [TextBlock(text="Hi there")]
    msg = AssistantMessage(content=blocks, model="claude-3")
    assert len(msg.content) == 1
    assert msg.model == "claude-3"


def test_system_message():
    """Test SystemMessage."""
    msg = SystemMessage(subtype="info", data={"key": "value"})
    assert msg.subtype == "info"
    assert msg.data["key"] == "value"


def test_result_message():
    """Test ResultMessage."""
    msg = ResultMessage(
        subtype="success",
        duration_ms=1000,
        duration_api_ms=800,
        is_error=False,
        num_turns=3,
        session_id="session-123",
        total_cost_usd=0.05,
    )
    assert msg.subtype == "success"
    assert msg.duration_ms == 1000
    assert msg.session_id == "session-123"
    assert msg.total_cost_usd == 0.05
