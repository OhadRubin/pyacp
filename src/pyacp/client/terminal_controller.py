import asyncio
import os
import uuid

from acp import RequestError
from acp.schema import (
    CreateTerminalRequest,
    CreateTerminalResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
)
from pyacp.utils.terminal import TerminalInfo


class TerminalController:

    # Optional / terminal-related methods ---------------------------------
    async def _capture_terminal_output(self, terminal_info: TerminalInfo) -> None:
        """Background task to capture stdout and stderr from a terminal process."""
        try:
            # Capture both stdout and stderr
            tasks = []
            if terminal_info.process.stdout:
                tasks.append(self._read_stream(terminal_info, terminal_info.process.stdout))
            if terminal_info.process.stderr:
                tasks.append(self._read_stream(terminal_info, terminal_info.process.stderr))

            if tasks:
                await asyncio.gather(*tasks)

            # Wait for process to complete and capture exit status
            await terminal_info.process.wait()

            # Determine exit status
            if terminal_info.process.returncode is not None:
                if terminal_info.process.returncode < 0:
                    # Negative return codes typically indicate signals
                    import signal
                    try:
                        sig = signal.Signals(-terminal_info.process.returncode)
                        terminal_info.signal = sig.name
                    except (ValueError, AttributeError):
                        terminal_info.signal = f"SIGNAL_{-terminal_info.process.returncode}"
                else:
                    terminal_info.exit_code = terminal_info.process.returncode

        except Exception:
            pass

    async def _read_stream(self, terminal_info: TerminalInfo, stream: asyncio.StreamReader) -> None:
        """Read from a stream and add to terminal output buffer."""
        try:
            while True:
                chunk = await stream.read(4096)
                if not chunk:
                    break
                terminal_info.add_output(chunk)
        except Exception:
            pass

    async def createTerminal(
        self,
        params: CreateTerminalRequest,
    ) -> CreateTerminalResponse:  # type: ignore[override]
        # Generate unique terminal ID
        self._terminal_counter += 1
        terminal_id = f"term_{uuid.uuid4().hex[:8]}_{self._terminal_counter}"

        # Build environment
        env = dict(os.environ)
        if params.env:
            for env_var in params.env:
                env[env_var.name] = env_var.value

        # Build command - always run through shell like a real terminal
        full_command = params.command
        if params.args:
            full_command += ' ' + ' '.join(params.args)
        cmd = ['/bin/sh', '-c', full_command]

        # Determine working directory
        cwd = params.cwd if params.cwd else os.getcwd()

        try:
            # Spawn the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            # Create terminal info
            terminal_info = TerminalInfo(
                terminal_id=terminal_id,
                process=process,
                output_byte_limit=params.outputByteLimit,
            )

            # Start background task to capture output
            terminal_info._output_task = asyncio.create_task(
                self._capture_terminal_output(terminal_info)
            )

            # Register terminal
            self.terminals[terminal_id] = terminal_info

            return CreateTerminalResponse(terminalId=terminal_id)

        except Exception as exc:
            raise RequestError.internal_error({"message": f"Failed to create terminal: {exc}"})

    async def terminalOutput(
        self,
        params: TerminalOutputRequest,
    ) -> TerminalOutputResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        output = terminal_info.get_output()

        # Build response
        response_data = {
            "output": output,
            "truncated": terminal_info.truncated,
        }

        # Add exit status if process has completed
        if terminal_info.exit_code is not None or terminal_info.signal is not None:
            response_data["exitStatus"] = {
                "exitCode": terminal_info.exit_code,
                "signal": terminal_info.signal,
            }

        return TerminalOutputResponse(**response_data)

    async def releaseTerminal(
        self,
        params: ReleaseTerminalRequest,
    ) -> ReleaseTerminalResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Kill the process if it's still running
        if terminal_info.process.returncode is None:
            try:
                terminal_info.process.kill()
                # Wait briefly for the process to terminate
                try:
                    await asyncio.wait_for(terminal_info.process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
            except Exception as exc:
                pass

        # Cancel the output capture task if it's still running
        if terminal_info._output_task and not terminal_info._output_task.done():
            terminal_info._output_task.cancel()
            try:
                await terminal_info._output_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        # Remove from registry
        del self.terminals[params.terminalId]

        return ReleaseTerminalResponse()

    async def waitForTerminalExit(
        self,
        params: WaitForTerminalExitRequest,
    ) -> WaitForTerminalExitResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Wait for the process to complete
        await terminal_info.process.wait()

        return WaitForTerminalExitResponse(
            exitCode=terminal_info.exit_code,
            signal=terminal_info.signal
        )

    async def killTerminal(
        self,
        params: KillTerminalCommandRequest,
    ) -> KillTerminalCommandResponse:  # type: ignore[override]
        terminal_info = self.terminals.get(params.terminalId)
        if not terminal_info:
            raise RequestError.invalid_params({
                "terminalId": params.terminalId,
                "reason": "Terminal not found"
            })

        # Kill the process if it's still running
        if terminal_info.process.returncode is None:
            try:
                terminal_info.process.kill()
                pass
            except Exception:
                pass

        return KillTerminalCommandResponse()