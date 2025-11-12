# End-to-End Tests

These tests replace the shell-based smoke tests with proper pytest end-to-end tests that verify PyACP SDK functionality with real ACP agents.

## Prerequisites

Install the ACP agents you want to test:

```bash
# Claude Code ACP
npm install -g @zed-industries/claude-code-acp

# Codex ACP
npm install -g @zed-industries/codex-acp

# OpenCode
# Install from https://opencode.ai

# Gemini
# Install Gemini with ACP support
```

## Running Tests

### Run all e2e tests
```bash
pytest tests/e2e/ -v
```

### Run specific agent tests
```bash
# Claude Code ACP only
pytest tests/e2e/ -v -m claude_code_acp

# Codex ACP only
pytest tests/e2e/ -v -m codex_acp

# OpenCode only
pytest tests/e2e/ -v -m opencode

# Gemini only
pytest tests/e2e/ -v -m gemini
```

### Run with output
```bash
# See agent responses in real-time
pytest tests/e2e/ -v -s
```

### Run parametrized tests (same test across all agents)
```bash
pytest tests/e2e/test_agents.py::test_agent_basic_math -v
```

## Test Structure

Each agent has two types of tests:

1. **`query()` function tests** - Test the convenience function for one-off queries
2. **`PyACPSDKClient` tests** - Test multi-turn conversations with context

Additionally, parametrized tests run the same test logic across all available agents.

## Skipping Tests

Tests automatically skip if the required agent is not installed. You can also skip all e2e tests:

```bash
# Run all tests except e2e
pytest -v -m "not e2e"
```

## Environment Variables

Tests use appropriate environment variables for each agent (configured in `conftest.py`):

- **Claude Code ACP**: ANTHROPIC_MODEL, ANTHROPIC_BASE_URL, etc.
- **Codex ACP**: CODEX_HOME, LITELLM_KEY
- **OpenCode**: OPENCODE_CONFIG, ACP_MODEL
- **Gemini**: GOOGLE_GEMINI_BASE_URL, GEMINI_API_KEY

## What Gets Tested

Each test verifies:
- ✅ Agent can be initialized and connected
- ✅ Messages are received from the agent
- ✅ AssistantMessage blocks contain text responses
- ✅ Multi-turn conversations maintain context
- ✅ File listing and basic operations work

These tests replace the original smoke test shell scripts:
- `scripts/claude_smoketest.sh` → `test_claude_code_acp_*`
- `scripts/codex_smoketest.sh` → `test_codex_acp_*`
- `scripts/opencode_smoketest.sh` → `test_opencode_*`
- `scripts/gemini_smoketest.sh` → `test_gemini_*`
