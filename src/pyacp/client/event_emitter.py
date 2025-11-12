import json
import sys

from acp.schema import (
    TextContentBlock,
    ResourceContentBlock,
    EmbeddedResourceContentBlock,
)


class EventEmitter:

    # ------------------------- WorkerFormat emitters -------------------------
    def _emit_worker_event(self, payload: dict) -> None:
        try:
            sys.stdout.write(json.dumps(payload) + "\n")
            sys.stdout.flush()
        except Exception:
            # Never let emitting break the flow
            pass

    def _emit_text(self, text: str) -> None:
        if not text:
            return
        self._emit_worker_event({"type": "TextBlock", "message": {"text": text}})

    def _emit_thinking(self, thinking: str) -> None:
        if not thinking:
            return
        self._emit_worker_event({"type": "ThinkingBlock", "message": {"thinking": thinking}})
    # Accumulation helpers -------------------------------------------------
    def _extract_text(self, content: object) -> str:
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

    def _accumulate_chunk(self, msg_type: str, content: object) -> None:
        # Flush if the incoming type differs from current
        if self.current_message_type and msg_type != self.current_message_type:
            self._flush_accumulated_message(trigger="type_change")

        if self.current_message_type != msg_type:
            self.current_message_type = msg_type

        text = self._extract_text(content)
        if text:
            self.accumulated_message += text

    def _flush_accumulated_message(self, trigger: str | None = None) -> None:
        if self.accumulated_message:
            msg_type = self.current_message_type or "message"
            if msg_type == "agent_thought":
                self._emit_thinking(self.accumulated_message)
            elif msg_type == "agent_message":
                self._emit_text(self.accumulated_message)
            # Deliberately skip emitting user messages to keep only canonical blocks
        # Reset regardless of whether there was content
        self.accumulated_message = ""
        self.current_message_type = None