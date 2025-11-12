"""Tests for content block types."""

import pytest
from pyacp.types.content import (
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)


def test_text_block():
    """Test TextBlock creation."""
    block = TextBlock(text="Hello world")
    assert block.text == "Hello world"


def test_thinking_block():
    """Test ThinkingBlock creation."""
    block = ThinkingBlock(thinking="Let me think...", signature="sig123")
    assert block.thinking == "Let me think..."
    assert block.signature == "sig123"


def test_thinking_block_default_signature():
    """Test ThinkingBlock with default signature."""
    block = ThinkingBlock(thinking="Thinking...")
    assert block.thinking == "Thinking..."
    assert block.signature == ""


def test_tool_use_block():
    """Test ToolUseBlock creation."""
    block = ToolUseBlock(
        id="tool-123",
        name="bash",
        input={"command": "ls -la"}
    )
    assert block.id == "tool-123"
    assert block.name == "bash"
    assert block.input["command"] == "ls -la"


def test_tool_result_block():
    """Test ToolResultBlock creation."""
    block = ToolResultBlock(
        tool_use_id="tool-123",
        content="output here",
        is_error=False
    )
    assert block.tool_use_id == "tool-123"
    assert block.content == "output here"
    assert block.is_error is False


def test_tool_result_block_with_list_content():
    """Test ToolResultBlock with list content."""
    block = ToolResultBlock(
        tool_use_id="tool-123",
        content=[{"type": "text", "text": "result"}]
    )
    assert isinstance(block.content, list)
    assert len(block.content) == 1
