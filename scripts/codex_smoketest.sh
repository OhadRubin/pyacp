#!/bin/bash

# Change to project root
cd "$(dirname "$0")/.." || exit 1

CMD1="Say hello and tell me what you can do"
CMD2="\n What is 2 + 2?"
CMD3="\n List the files in the current directory"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"

export CODEX_HOME="configs/codex_home"
export LITELLM_KEY=sk-1234
printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client codex-acp
