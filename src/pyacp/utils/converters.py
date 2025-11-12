"""Converters between ACP schema and SDK types."""

from __future__ import annotations
from typing import Any

from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    TextContentBlock,
    ResourceContentBlock,
    EmbeddedResourceContentBlock,
)

from pyacp.types.content import TextBlock, ThinkingBlock


def extract_text_from_acp_content(content: Any) -> str:
    """Extract text from various ACP content block types."""
    if isinstance(content, TextContentBlock):
        return content.text
    if isinstance(content, ResourceContentBlock):
        return content.name or content.uri or ""
    if isinstance(content, EmbeddedResourceContentBlock):
        resource = content.resource
        text = getattr(resource, "text", None)
        if text:
            return text
        blob = getattr(resource, "blob", None)
        return blob or ""
    if isinstance(content, dict):
        # Attempt to pull text field if present
        return str(content.get("text", ""))
    return ""


def acp_message_chunk_to_text_block(chunk: AgentMessageChunk) -> TextBlock:
    """Convert ACP AgentMessageChunk to SDK TextBlock."""
    text = extract_text_from_acp_content(chunk.content)
    return TextBlock(text=text)


def acp_thought_chunk_to_thinking_block(chunk: AgentThoughtChunk) -> ThinkingBlock:
    """Convert ACP AgentThoughtChunk to SDK ThinkingBlock."""
    text = extract_text_from_acp_content(chunk.content)
    return ThinkingBlock(thinking=text, signature="")


__all__ = [
    "extract_text_from_acp_content",
    "acp_message_chunk_to_text_block",
    "acp_thought_chunk_to_thinking_block",
]
