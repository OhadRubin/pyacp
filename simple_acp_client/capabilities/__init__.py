"""Capabilities module - Terminal and filesystem controllers."""

from simple_acp_client.capabilities.terminal import TerminalController, TerminalInfo
from simple_acp_client.capabilities.filesystem import FileSystemController

__all__ = ["TerminalController", "TerminalInfo", "FileSystemController"]
