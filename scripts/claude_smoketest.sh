#!/bin/bash

# Change to project root
cd "$(dirname "$0")/.." || exit 1

CMD1="Say hello and tell me what you can do"
CMD2="\n What is 2 + 2?"
CMD3="\n List the files in the current directory"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"

export CLAUDE_CODE_ACTION=bypassPermissions
export ANTHROPIC_MODEL="worker-claude-sonnet-4-5"
export ANTHROPIC_SMALL_FAST_MODEL="worker-claude-haiku-4-5"
export MAX_THINKING_TOKENS=10000
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="sk-1234"
export ACP_MODEL=$ANTHROPIC_MODEL

printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client claude-code-acp



