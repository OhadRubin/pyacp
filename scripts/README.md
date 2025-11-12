# Test Scripts

This directory contains smoke test scripts that showcase how to use the interactive example with various LiteLLM setups and ACP-compatible agents.

## Overview

These scripts demonstrate different configurations for testing the Simple ACP Client with various agent implementations:

- `codex_smoketest.sh` - Test with Codex ACP agent
- `claude_smoketest.sh` - Test with Claude Code ACP agent
- `gemini_smoketest.sh` - Test with Gemini CLI
- `opencode_smoketest.sh` - Test with OpenCode

## Usage

Each script sets up a custom configuration with LiteLLM to route requests through a local proxy. This allows testing with different model providers and configurations.

**Note:** These scripts also work without any special setup if you're already authenticated with the respective apps (Claude Code, Codex, etc.). The LiteLLM configuration is optional and primarily useful for local testing or using alternative model providers.

## Running Tests

Simply execute any of the test scripts:

```bash
./scripts/codex_smoketest.sh
./scripts/claude_smoketest.sh
./scripts/gemini_smoketest.sh
./scripts/opencode_smoketest.sh
```

Each script will:
1. Set up a temporary configuration directory
2. Configure the agent with appropriate settings
3. Run a series of test commands through the interactive example
4. Clean up temporary files on exit
