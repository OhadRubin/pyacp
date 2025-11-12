#!/bin/bash

# Change to script directory
cd "$(dirname "$0")" || exit 1

rm mini_terminal.py
cp mini_terminal_w_prints.py  mini_terminal.py 

CMD1="please remove all the print statements from mini_terminal.py"
CMD2="\n"
CMD3=$'\x03'  # Send a Ctrl+C character
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"

export CLAUDE_CODE_ACTION=bypassPermissions
export ANTHROPIC_MODEL="worker-claude-sonnet-4-5"
export ANTHROPIC_SMALL_FAST_MODEL="worker-claude-haiku-4-5"
export MAX_THINKING_TOKENS=10000
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="sk-1234"
export ACP_MODEL=$ANTHROPIC_MODEL

printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client claude-code-acp



