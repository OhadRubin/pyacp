#!/bin/bash

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
printf "$STR_TO_OUTPUT" | uv run acp_client.py codex-acp

# MODEL_NAME="gemini-2.5-flash"
# export OPENCODE_CONFIG_CONTENT="{\"model\":\"anthropic/$MODEL_NAME\"}"
# CODEX_HOME="." codex -p gpt-5-mini-high

#  codex -p gpt-5-mini-high

# this is `bun dev`
# printf "$STR_TO_OUTPUT" | uv run acp_client.py bun --bun run --cwd /Users/ohadr/dev/forked-opencode/opencode/packages/opencode --conditions=browser src/index.ts acp

# printf "$STR_TO_OUTPUT" | uv run acp_client.py opencode acp

# printf "$STR_TO_OUTPUT" | uv run acp_client.py claude-code-acp
# printf "$STR_TO_OUTPUT" | uv run acp_client.py gemini --experimental-acp --yolo --allowed-tools run_shell_command -m gemini-2.5-flash

