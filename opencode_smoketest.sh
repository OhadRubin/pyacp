#!/bin/bash

# git checkout -- mini_terminal.py
rm mini_terminal.py
cp mini_terminal_w_prints.py  mini_terminal.py   

CMD1="please remove all the print statements from mini_terminal.py"
CMD2="\n 1. Start a background process that counts to 60 and prints once every 5 seconds 2. Check it multiple times until it's done"
CMD3="\n do the following. 1. Create a todo list with the first 4 letters of the alphabet 2. Tell me the content of evaluate.py 3. Run ls"
STR_TO_OUTPUT="$CMD1 $CMD2 $CMD3"



cat > opencode.json <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/worker-claude-sonnet-4-5",
  "provider": {

    "anthropic": {
      "options": {
        "baseURL": "http://127.0.0.1:4000/v1",
        "apiKey": "sk-1234"
      },
      "models": {
        "worker-claude-sonnet-4-5": {
          "name": "Worker Claude Sonnet 4.5",
          "options": {
            "thinking": {
              "type": "enabled",
              "budgetTokens": 16000
            }
          }
        }
      }
    },
    "openrouter": {
      "options": {
        "baseURL": "http://127.0.0.1:4000/v1",
        "apiKey": "sk-1234"
      },
      "models": {
        "gemini-2.5-pro": {
          "name": "Gemini 2.5 pro"
        }
      }
    },
    "openai": {
      "options": {
        "baseURL": "http://127.0.0.1:4000/v1",
        "apiKey": "sk-1234"
      },
      "models": {
        "gpt-5": {
          "options": {
            "reasoningEffort": "low",
            "textVerbosity": "low",
            "reasoningSummary": "auto",
            "include": ["reasoning.encrypted_content"]
          }
        }
      }
    }
  }
  
}

EOF


export OPENCODE_CONFIG="$PWD/opencode.json"
export MAX_THINKING_TOKENS=10000


# export OPENCODE_CONFIG_CONTENT='{"model":"openrouter/gemini-2.5-pro"}'

export ACP_MODEL="openrouter/gemini-2.5-pro"

printf "$STR_TO_OUTPUT" | uv run acp_client.py opencode acp