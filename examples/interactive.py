from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys

from acp import RequestError
from pyacp.sdk.client import PyACPSDKClient, PyACPAgentOptions


async def interactive_loop(client: PyACPSDKClient) -> None:
    """
    Interactive loop for CLI usage with PyACPSDKClient.

    Args:
        client: Connected PyACPSDKClient instance
    """
    print("Type a message and press Enter to send.")
    print("Commands: :cancel, :exit")

    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, lambda: input("\n> ").strip())
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not line:
            continue
        if line in {":exit", ":quit"}:
            break
        if line == ":cancel":
            try:
                await client.interrupt()
                print("[Cancelled]")
            except Exception as exc:
                print(f"Cancel failed: {exc}", file=sys.stderr)
            continue

        try:
            if not line.strip():
                continue
            print(f"[line]: {line}")

            await client.query(line)
            async for message in client.receive_messages():
                
                print(f"[message in interactive_loop]: {message}")
        except RequestError as err:
            _print_request_error("prompt", err)
        except Exception as exc:  # noqa: BLE001
            print(f"Prompt failed: {exc}", file=sys.stderr)


async def run(argv: list[str]) -> int:
    """
    Standalone CLI runner that uses PyACPSDKClient for all protocol operations.

    Args:
        argv: Command line arguments (program name, agent command, agent args)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if len(argv) < 2:
        print("Usage: python acp_client.py AGENT_PROGRAM [ARGS...]", file=sys.stderr)
        return 2

    model_id = os.environ.get("ACP_MODEL", None)
    program = argv[1]
    args = argv[2:]

    # Build agent command
    agent_command = [program] + args

    # Create options
    options = PyACPAgentOptions(
        model=model_id,
        cwd=os.getcwd(),
    )

    # Create and connect client
    client = PyACPSDKClient(options)

    try:
        # Connect to agent (this handles all initialization)
        await client.connect(agent_command)

        # Run interactive loop
        await interactive_loop(client)

        # Disconnect gracefully
        await client.disconnect()

        return 0

    except FileNotFoundError as exc:
        print(f"Failed to start agent process: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1
    finally:
        # Ensure cleanup even on error
        if client._connected:
            with contextlib.suppress(Exception):
                await client.disconnect()


def _print_request_error(stage: str, err: RequestError) -> None:
    payload = err.to_error_obj()
    message = payload.get("message", "")
    code = payload.get("code")
    data = payload.get("data")
    print(f"{stage} request error: code={code} message={message} data={data}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    # Keep logging quiet; emission happens directly from ACPClient
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.ERROR)

    args = sys.argv if argv is None else argv
    return asyncio.run(run(list(args)))


if __name__ == "__main__":
    raise SystemExit(main())
