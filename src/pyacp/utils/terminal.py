"""Terminal management utilities for PyACP SDK."""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field


@dataclass
class TerminalInfo:
    """Tracks a single terminal instance."""

    terminal_id: str
    process: asyncio.subprocess.Process
    output_buffer: bytearray = field(default_factory=bytearray)
    output_byte_limit: int | None = None
    truncated: bool = False
    exit_code: int | None = None
    signal: str | None = None
    _output_task: asyncio.Task | None = None

    def add_output(self, data: bytes) -> None:
        """Add output data, enforcing byte limit with UTF-8 character boundary truncation."""
        self.output_buffer.extend(data)

        if self.output_byte_limit is not None and len(self.output_buffer) > self.output_byte_limit:
            # Truncate from the beginning, ensuring UTF-8 character boundaries
            excess = len(self.output_buffer) - self.output_byte_limit

            # Find a valid UTF-8 starting point after the excess
            truncate_point = excess
            while truncate_point < len(self.output_buffer):
                try:
                    # Try to decode from this point to verify it's a valid UTF-8 boundary
                    self.output_buffer[truncate_point:truncate_point+1].decode('utf-8', errors='strict')
                    break
                except UnicodeDecodeError:
                    truncate_point += 1

            self.output_buffer = self.output_buffer[truncate_point:]
            self.truncated = True

    def get_output(self) -> str:
        """Get the current output as a string."""
        try:
            return self.output_buffer.decode('utf-8', errors='replace')
        except Exception:
            return self.output_buffer.decode('utf-8', errors='ignore')


__all__ = ["TerminalInfo"]
