# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of PyACP SDK
- `ClaudeSDKClient` class for continuous conversation sessions
- `query()` function for simple one-off queries
- Support for multiple ACP agents (Claude Code, Codex, OpenCode, Gemini)
- Claude SDK-compatible API
- Full type hints and mypy support
- Comprehensive test suite (unit and integration tests)
- Example scripts for common use cases
- Complete documentation (quickstart, API reference)
- Permission modes: default, acceptEdits, plan, bypassPermissions
- Tool filtering (allowed_tools, disallowed_tools)
- Environment variable configuration
- Working directory configuration
- Terminal/subprocess management utilities
- Message type system (UserMessage, AssistantMessage, SystemMessage, ResultMessage)
- Content block types (TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock)

### Documentation
- Quickstart guide
- Complete API reference
- Usage examples for basic queries, streaming conversations, terminal interaction, and file operations
- Smoke test scripts for all supported agents

[0.1.0]: https://github.com/yourusername/pyacp/releases/tag/v0.1.0
