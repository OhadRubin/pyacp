from __future__ import annotations

from pathlib import Path

from acp import RequestError
from acp.schema import (
    ReadTextFileRequest,
    ReadTextFileResponse,
    WriteTextFileRequest,
    WriteTextFileResponse,
)


def _slice_text(content: str, line: int | None, limit: int | None) -> str:
    lines = content.splitlines()
    start = 0
    if line:
        start = max(line - 1, 0)
    end = len(lines)
    if limit:
        end = min(start + limit, end)
    return "\n".join(lines[start:end])


class FileSystemController:
    async def writeTextFile(
        self,
        params: WriteTextFileRequest,
    ) -> WriteTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params.content)
        # Intentionally quiet; WorkerFormat emission handled elsewhere
        return WriteTextFileResponse()

    async def readTextFile(
        self,
        params: ReadTextFileRequest,
    ) -> ReadTextFileResponse:  # type: ignore[override]
        path = Path(params.path)
        if not path.is_absolute():
            raise RequestError.invalid_params({"path": params.path, "reason": "path must be absolute"})
        text = path.read_text()
        # Intentionally quiet; WorkerFormat emission handled via hooks
        if params.line is not None or params.limit is not None:
            text = _slice_text(text, params.line, params.limit)
        return ReadTextFileResponse(content=text)


