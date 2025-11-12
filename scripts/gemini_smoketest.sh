#!/bin/bash

# git checkout -- mini_terminal.py
rm mini_terminal.py
cp mini_terminal_w_prints.py  mini_terminal.py 

CMD1="\n please remove all the print statements from mini_terminal.py"
CMD2="\n 1. Start a background process that counts to 60 and prints once every 5 seconds 2. Check it multiple times until it's done"
CMD3="\n do the following. 1. Create a todo list with the first 4 letters of the alphabet 2. Tell me the content of evaluate.py 3. Run ls"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"

export GOOGLE_GEMINI_BASE_URL="http://localhost:4000"
export GEMINI_API_KEY=sk-1234


printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client gemini --experimental-acp --yolo --allowed-tools run_shell_command -m gemini-2.5-pro

