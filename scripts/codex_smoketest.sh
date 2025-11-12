#!/bin/bash

# Change to script directory
cd "$(dirname "$0")" || exit 1

# git checkout -- mini_terminal.py
rm mini_terminal.py
cp mini_terminal_w_prints.py  mini_terminal.py 

CMD1="please remove all the print statements from mini_terminal.py"
CMD2="\n 1. Start a background process that counts to 60 and prints once every 5 seconds 2. Check it multiple times until it's done"
CMD3="\n do the following. 1. Create a todo list with the first 4 letters of the alphabet 2. Tell me the content of evaluate.py 3. Run ls"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"



mkdir -p codex_home

cat > codex_home/auth.json <<EOF
{
  "OPENAI_API_KEY": "sk-1234"
}
EOF


cat > codex_home/config.toml <<'EOF'

sandbox_mode = "danger-full-access"
approval_policy = "never"

model = "gpt-5-nano"
model_provider = "openai_chat"
model_reasoning_effort = "high"
model_reasoning_summary = "auto"
model_supports_reasoning_summaries = true
show_raw_agent_reasoning = true 
forced_login_method = "api"



[model_providers.openai_chat]
name = "OpenAI chat"
base_url = "http://127.0.0.1:4000/v1"
env_key = "LITELLM_KEY"
wire_api = "responses"

EOF
export CODEX_HOME="codex_home"
export LITELLM_KEY=sk-1234
printf "$STR_TO_OUTPUT" | uv run python -m pyacp.client.acp_client codex-acp
