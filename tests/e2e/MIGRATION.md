# Migration from Smoke Tests to E2E Tests

This document describes the migration from shell-based smoke tests to pytest-based end-to-end tests.

## Overview

The shell scripts in `scripts/` have been converted to proper pytest end-to-end tests in `tests/e2e/`.

## Mapping

| Old Smoke Test | New E2E Test |
|----------------|--------------|
| `scripts/claude_smoketest.sh` | `tests/e2e/test_agents.py::test_claude_code_acp_*` |
| `scripts/codex_smoketest.sh` | `tests/e2e/test_agents.py::test_codex_acp_*` |
| `scripts/opencode_smoketest.sh` | `tests/e2e/test_agents.py::test_opencode_*` |
| `scripts/gemini_smoketest.sh` | `tests/e2e/test_agents.py::test_gemini_*` |

## Improvements

The pytest e2e tests provide several advantages over shell scripts:

### 1. Better Structure
- Proper test isolation
- Shared fixtures for environment setup
- Parametrized tests for cross-agent testing

### 2. Better Error Reporting
- Detailed assertion failures
- Stack traces for debugging
- Integration with pytest reporting tools

### 3. Better Integration
- Part of the unified test suite
- Can be run selectively with markers
- Compatible with CI/CD pipelines

### 4. Better Verification
- Structured assertions on message content
- Type-safe with SDK types
- Can verify specific message fields

### 5. Skip Logic
- Automatic skipping when agents aren't installed
- No manual checks required
- Clear skip reasons in test output

## Migration Details

### Environment Variables

Shell scripts set environment variables directly:
```bash
export CLAUDE_CODE_ACTION=bypassPermissions
export ANTHROPIC_MODEL="worker-claude-sonnet-4-5"
```

E2E tests use pytest fixtures:
```python
@pytest.fixture
def claude_code_env():
    return {
        "CLAUDE_CODE_ACTION": "bypassPermissions",
        "ANTHROPIC_MODEL": "worker-claude-sonnet-4-5",
        # ...
    }
```

### Input Method

Shell scripts used stdin piping:
```bash
printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client claude-code-acp
```

E2E tests use the high-level SDK:
```python
async for message in query(prompt="What is 2 + 2?", options=options):
    # Process messages
```

### Verification

Shell scripts had no automated verification - they just ran and printed output.

E2E tests have proper assertions:
```python
assert len(messages) > 0, "Should receive at least one message"
assistant_messages = [m for m in messages if isinstance(m, AssistantMessage)]
assert len(assistant_messages) > 0, "Should receive at least one AssistantMessage"
```

## Running the New Tests

```bash
# Run all e2e tests
pytest tests/e2e/ -v

# Run specific agent tests
pytest tests/e2e/ -v -m claude_code_acp

# Run with live output
pytest tests/e2e/ -v -s
```

## Keeping Shell Scripts

The shell scripts in `scripts/` are kept for:
1. Manual testing during development
2. Quick sanity checks
3. Backwards compatibility

However, **pytest e2e tests are now the recommended approach** for automated testing.
