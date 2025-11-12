# Bug: SDK Client Hangs When Receiving ACP Messages

## Summary

The `PyACPSDKClient` in `src/pyacp/client/sdk_client.py` hangs indefinitely when trying to receive messages from the ACP agent. The query is sent successfully, but `receive_response()` blocks forever waiting for messages that never arrive.

## The Problem

**Symptom:**
```bash
[DEBUG] About to send query...
[DEBUG] Query sent, starting to receive responses...
# <-- HANGS HERE FOREVER
```

**Root Cause:** The SDK client doesn't have a background task reading messages from the agent's stdout stream.

## How ACP Communication Works

The ACP (Agent Communication Protocol) uses JSON-RPC over stdin/stdout:

1. **Client → Agent (stdin)**: Client sends requests as JSON-RPC messages
2. **Agent → Client (stdout)**: Agent sends responses/notifications as JSON-RPC messages
3. **Background Reading Required**: The client MUST continuously read from stdout in a background task, otherwise messages pile up in the OS pipe buffer and eventually the agent blocks when trying to write

The ACP protocol sends multiple notification messages during execution:
- `SessionNotification` with `AvailableCommandsUpdate`
- `SessionNotification` with `AgentMessageChunk` (text content)
- `SessionNotification` with `AgentThoughtChunk` (thinking content)
- `SessionNotification` with `ToolCallStart`, `ToolCallProgress` updates

## How `acp_client.py` Works (CORRECT Implementation)

Location: `src/pyacp/client/acp_client.py:519`

**Key:** Uses `spawn_stdio_transport()` from the ACP library, which automatically handles background message reading.

```python
async with spawn_stdio_transport(
    program,
    *args,
    stderr=asyncio.subprocess.PIPE,
    env={**os.environ},
) as (stdout, stdin, proc):
    client_impl = ACPClient()
    conn = ClientSideConnection(
        lambda _agent: client_impl,
        stdin,
        stdout,
        state_store=MyInMemoryMessageStateStore(client_impl),
    )

    # Initialize, create session, send prompts...
```

`spawn_stdio_transport()` creates an async context manager that:
1. Spawns the subprocess
2. **Starts a background asyncio task that continuously reads from stdout**
3. Automatically parses JSON-RPC messages
4. Routes messages to the appropriate handlers (like `client_impl.sessionUpdate()`)
5. Cleans up on exit

## How `sdk_client.py` Was Broken (INCORRECT Implementation)

Location: `src/pyacp/client/sdk_client.py:142`

**Problem:** Manually creates subprocess streams but never starts a background reader task.

```python
# BROKEN: Manual subprocess creation without background reader
self._process = await asyncio.create_subprocess_exec(
    program,
    *args,
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env,
)

self._stdin_writer = self._process.stdin
self._stdout_reader = self._process.stdout

# Creates connection with streams
self._connection = ClientSideConnection(
    lambda _agent: self._client_impl,
    self._stdin_writer,  # ✓ Can write
    self._stdout_reader, # ✗ Nobody reading from this!
    state_store=InMemoryMessageStateStore(),
)
```

**What happens:**
1. Client sends query via stdin ✓
2. Agent processes and writes responses to stdout
3. Nobody is reading from stdout, so messages pile up in OS pipe buffer
4. Eventually agent blocks trying to write more output
5. `receive_response()` waits for messages on `_message_queue` ✗
6. `_message_queue` is empty because no background task is calling `sessionUpdate()` to populate it ✗
7. Deadlock: agent blocked on write, client blocked on queue.get()



## Output Examples

### Working Example: `./scripts/claude_smoketest.sh`

```
>> ./scripts/claude_smoketest.sh 2>&1 | tee claude_smoketest_sh.out
Type a message and press Enter to send.
Commands: :cancel, :exit

> [line]: please remove all the print statements from mini_terminal.py
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=AvailableCommandsUpdate(field_meta=None, availableCommands=[AvailableCommand(field_meta=None, description='the following command prints out the entire content of the folder into stdout. DO NOT RUN IT YET ... (project, gitignored)', input=None, name='shorten_docs'), AvailableCommand(field_meta=None, description='Custom command (project, gitignored)', input=None, name='improve_plan'), AvailableCommand(field_meta=None, description='Give me a plan for the following: (project, gitignored)', input=None, name='plan'), AvailableCommand(field_meta=None, description='milestone improvement agents guide (project, gitignored)', input=None, name='research_agents'), AvailableCommand(field_meta=None, description='Write a comprehensive bug report using the provided debugging context. Follow professional standa... (project, gitignored)', input=None, name='bug_report'), AvailableCommand(field_meta=None, description='Custom command (project)', input=None, name='improve_plan'), AvailableCommand(field_meta=None, description='milestone improvement agents guide (project)', input=None, name='research_agents'), AvailableCommand(field_meta=None, description='Give me a plan for the following: (project)', input=None, name='plan'), AvailableCommand(field_meta=None, description='Write a comprehensive bug report using the provided debugging context. Follow professional standa... (project)', input=None, name='bug_report'), AvailableCommand(field_meta=None, description='the following command prints out the entire content of the folder into stdout. DO NOT RUN IT YET ... (project)', input=None, name='shorten_docs'), AvailableCommand(field_meta=None, description='Clear conversation history but keep a summary in context. Optional: /compact [instructions for summarization]', input=AvailableCommandInput(root=CommandInputHint(hint='<optional custom summarization instructions>')), name='compact'), AvailableCommand(field_meta=None, description='Initialize a new CLAUDE.md file with codebase documentation', input=None, name='init'), AvailableCommand(field_meta=None, description='Get comments from a GitHub pull request', input=None, name='pr-comments'), AvailableCommand(field_meta=None, description='Review a pull request', input=None, name='review'), AvailableCommand(field_meta=None, description='Complete a security review of the pending changes on the current branch', input=None, name='security-review')], sessionUpdate='available_commands_update')
{"type": "ThinkingBlock", "message": {"thinking": "The user wants me to remove all print statements from mini_terminal.py. Let me first read the file to see what print statements are present.\n\nLooking at the context, I'm in /Users/ohadr/pyacp/scripts directory, and mini_terminal.py should be in this directory.\n\nThis is a straightforward task - I should:\n1. Read the file to see the current content\n2. Remove all print statements\n3. Write the updated file back\n\nSince this is a simple task with just one clear objective, I don't need to use the TodoWrite tool (as per the guidelines - don't use it for single, straightforward tasks)."}}
{"type": "TextBlock", "message": {"text": "I'll read the file first to see what print statements need to be removed."}}
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[], kind='read', locations=[], rawInput={}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Read File', toolCallId='toolu_vrtx_01DgMRKLk9ZoyQYeMFHhRtcz')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[], kind='read', locations=[ToolCallLocation(field_meta=None, line=0, path='/Users/ohadr/pyacp/scripts/mini_terminal.py')], rawInput={'file_path': '/Users/ohadr/pyacp/scripts/mini_terminal.py'}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Read /Users/ohadr/pyacp/scripts/mini_terminal.py', toolCallId='toolu_vrtx_01DgMRKLk9ZoyQYeMFHhRtcz')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallProgress(field_meta=None, content=[ContentToolCallContent(content=TextContentBlock(field_meta=None, annotations=None, text='```\n#!/usr/bin/env python3\n"""Minimal terminal test for ACP client."""\n\nimport asyncio\nimport os\n\n\nasync def test_shell_command():\n    """Test executing a shell command with subprocess."""\n\n    # Test 1: Simple shell script\n    full_command = \'for i in $(seq 1 3); do echo "Count: $i"; sleep 0.5; done\'\n    cmd = [\'/bin/sh\', \'-c\', full_command]\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n    # Test 2: Simple command with args\n    cmd = [\'/bin/sh\', \'-c\', \'ls -la\']\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n    # Test 3: Echo command\n    print("Test 3: Echo with variable")\n    cmd = [\'/bin/sh\', \'-c\', \'echo "Hello from shell: $USER"\']\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n    # Test 4: Command chaining with &&\n    cmd = [\'/bin/sh\', \'-c\', \'echo "First" && echo "Second" && echo "Third"\']\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n    # Test 5: Piping\n    print("Test 5: Piping commini_terminal.pymands")\n    cmd = [\'/bin/sh\', \'-c\', \'echo -e "apple\\\\nbanana\\\\ncherry" | grep "an"\']\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n    # Test 6: Complex pipe chain\n    cmd = [\'/bin/sh\', \'-c\', \'ls -la | head -5 | tail -3\']\n\n    process = await asyncio.create_subprocess_exec(\n        *cmd,\n        stdout=asyncio.subprocess.PIPE,\n        stderr=asyncio.subprocess.PIPE,\n    )\n\n    stdout, stderr = await process.communicate()\n\n# cp todo.sh $LOGDIR/todo.sh\n\nif __name__ == "__main__":\n    asyncio.run(test_shell_command())\n```', type='text'), type='content')], kind=None, locations=None, rawInput=None, rawOutput=None, sessionUpdate='tool_call_update', status='completed', title=None, toolCallId='toolu_vrtx_01DgMRKLk9ZoyQYeMFHhRtcz')
{"type": "ThinkingBlock", "message": {"thinking": "Looking at the file, I can see there are two print statements:\n1. Line 37: `print(\"Test 3: Echo with variable\")`\n2. Line 56: `print(\"Test 5: Piping commini_terminal.pymands\")` (this one seems to have a typo in the string)\n\nI need to remove both of these print statements. I'll use the Edit tool to remove them one by one."}}
{"type": "TextBlock", "message": {"text": "I can see there are 2 print statements in the file. I'll remove them both:"}}
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[], kind='edit', locations=[], rawInput={}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Edit', toolCallId='toolu_vrtx_01JnHk7P5ZiazKVLFk5BMwhM')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[FileEditToolCallContent(field_meta=None, newText='    # Test 3: Echo command\n    cmd = [\'/bin/sh\', \'-c\', \'echo "Hello from shell: $USER"\']', oldText='    # Test 3: Echo command\n    print("Test 3: Echo with variable")\n    cmd = [\'/bin/sh\', \'-c\', \'echo "Hello from shell: $USER"\']', path='/Users/ohadr/pyacp/scripts/mini_terminal.py', type='diff')], kind='edit', locations=[ToolCallLocation(field_meta=None, line=None, path='/Users/ohadr/pyacp/scripts/mini_terminal.py')], rawInput={'file_path': '/Users/ohadr/pyacp/scripts/mini_terminal.py', 'old_string': '    # Test 3: Echo command\n    print("Test 3: Echo with variable")\n    cmd = [\'/bin/sh\', \'-c\', \'echo "Hello from shell: $USER"\']', 'new_string': '    # Test 3: Echo command\n    cmd = [\'/bin/sh\', \'-c\', \'echo "Hello from shell: $USER"\']'}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Edit `/Users/ohadr/pyacp/scripts/mini_terminal.py`', toolCallId='toolu_vrtx_01JnHk7P5ZiazKVLFk5BMwhM')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[], kind='edit', locations=[], rawInput={}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Edit', toolCallId='toolu_vrtx_01MNjS7KhHe7VHTeEVopH7Ts')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallStart(field_meta=None, content=[FileEditToolCallContent(field_meta=None, newText='    # Test 5: Piping\n    cmd = [\'/bin/sh\', \'-c\', \'echo -e "apple\\\\nbanana\\\\ncherry" | grep "an"\']', oldText='    # Test 5: Piping\n    print("Test 5: Piping commini_terminal.pymands")\n    cmd = [\'/bin/sh\', \'-c\', \'echo -e "apple\\\\nbanana\\\\ncherry" | grep "an"\']', path='/Users/ohadr/pyacp/scripts/mini_terminal.py', type='diff')], kind='edit', locations=[ToolCallLocation(field_meta=None, line=None, path='/Users/ohadr/pyacp/scripts/mini_terminal.py')], rawInput={'file_path': '/Users/ohadr/pyacp/scripts/mini_terminal.py', 'old_string': '    # Test 5: Piping\n    print("Test 5: Piping commini_terminal.pymands")\n    cmd = [\'/bin/sh\', \'-c\', \'echo -e "apple\\\\nbanana\\\\ncherry" | grep "an"\']', 'new_string': '    # Test 5: Piping\n    cmd = [\'/bin/sh\', \'-c\', \'echo -e "apple\\\\nbanana\\\\ncherry" | grep "an"\']'}, rawOutput=None, sessionUpdate='tool_call', status='pending', title='Edit `/Users/ohadr/pyacp/scripts/mini_terminal.py`', toolCallId='toolu_vrtx_01MNjS7KhHe7VHTeEVopH7Ts')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallProgress(field_meta=None, content=None, kind=None, locations=None, rawInput=None, rawOutput=None, sessionUpdate='tool_call_update', status='completed', title=None, toolCallId='toolu_vrtx_01JnHk7P5ZiazKVLFk5BMwhM')
[params]: field_meta=None sessionId='019a767c-cae2-721f-b895-4c255ee7a2b8' update=ToolCallProgress(field_meta=None, content=None, kind=None, locations=None, rawInput=None, rawOutput=None, sessionUpdate='tool_call_update', status='completed', title=None, toolCallId='toolu_vrtx_01MNjS7KhHe7VHTeEVopH7Ts')
{"type": "ThinkingBlock", "message": {"thinking": "Great! Both print statements have been successfully removed from the file. The edits were applied successfully as shown in the diff output."}}
{"type": "TextBlock", "message": {"text": "Done! I've removed both print statements from `mini_terminal.py`:\n- Removed `print(\"Test 3: Echo with variable\")` at line 37\n- Removed `print(\"Test 5: Piping commini_terminal.pymands\")` at line 56"}}

> [line]:
{"type": "ThinkingBlock", "message": {"thinking": "The user sent an empty message. This might be:\n1. An accidental send\n2. They're waiting for me to continue\n3. They want me to acknowledge completion\n\nSince I just completed their task of removing print statements, I should probably just acknowledge that I'm ready for the next task or confirm that the work is complete."}}
{"type": "TextBlock", "message": {"text": "The print statements have been removed from `mini_terminal.py`. Is there anything else you'd like me to help with?"}}

>
Exiting.
```

### Broken Example: `uv run examples/claude_smoketest_workflow.py`

```
>> uv run examples/claude_smoketest_workflow.py
================================================================================
Claude Smoketest Workflow Example
================================================================================

Working directory: /Users/ohadr/pyacp/scripts
Files: mini_terminal.py, mini_terminal_w_prints.py


================================================================================
TASK 1: Remove print statements from mini_terminal.py
================================================================================

Sending: 'please remove all the print statements from mini_terminal.py'

[DEBUG] About to send query...
[DEBUG] Query sent, starting to receive responses...
^C

Interrupted by user
```

Note: The Python workflow hangs after sending the query because no messages are being received from the agent.
