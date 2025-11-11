#!/bin/bash

rm mini_terminal.py
cp mini_terminal_w_prints.py  mini_terminal.py 

CMD1="please remove all the print statements from mini_terminal.py"
CMD2="\n 1. Start a background process that counts to 60 and prints once every 5 seconds 2. Check it multiple times until it's done"
CMD3="\n do the following. 1. Create a todo list with the first 4 letters of the alphabet 2. Tell me the content of evaluate.py 3. Run ls"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"

export CLAUDE_CODE_ACTION=bypassPermissions
export ANTHROPIC_MODEL="worker-claude-sonnet-4-5"
export ANTHROPIC_SMALL_FAST_MODEL="worker-claude-haiku-4-5"
export MAX_THINKING_TOKENS=10000
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="sk-1234"
export ACP_MODEL=$ANTHROPIC_MODEL

printf "$STR_TO_OUTPUT" | uv run acp_client.py claude-code-acp



