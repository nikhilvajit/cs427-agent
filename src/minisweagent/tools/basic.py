"""Basic, safe local tools: read_file and write_file.

Both tools are synchronous and return a dict matching the environment
execute result shape: {"output": str, "returncode": int}.

Safety considerations (kept simple on purpose for a starter set):
- Paths are resolved to absolute paths.
- write_file creates parent directories as needed.
"""

from __future__ import annotations

import shlex
import os
import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import register


@dataclass
class ReadFile:
    name: str = "read_file"
    description: str = (
        "Read a UTF-8 text file, optionally by line range. Use this to inspect code before applying edits; pair with search, summarize_file, or replace/apply_diff when you need context-aware modifications."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "start_line": {
                    "type": "integer",
                    "description": "Line number to start reading (1-indexed)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line number to stop reading (inclusive)",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        path_arg = str(args.get("path", ""))
        start = args.get("start_line")
        end = args.get("end_line")

        if not path_arg:
            return {"output": "Missing 'path'", "returncode": 2}

        # Validate line numbers
        if (start is not None and end is None) or (start is None and end is not None):
            return {
                "output": "If you provide start_line or end_line, you must provide both.",
                "returncode": 1,
            }

        # Sandbox Environment (Docker)
        if env is not None:
            if start is not None and end is not None:
                # Use sed to read specific lines inside the container
                cmd = f"sed -n '{start},{end}p' {shlex.quote(path_arg)}"
            else:
                cmd = f"sed -n '1,99999p' {shlex.quote(path_arg)}"

            result = env.execute(cmd)

            if result.get("returncode", 1) != 0:
                # return container error as-is
                return result

            raw_text = result.get("output", "")

            # Convert to numbered lines
            if raw_text and not raw_text.endswith("\n"):
                raw_text += "\n"

            lines = raw_text.splitlines(keepends=True)

            # Use the start offset to properly number within the file
            base = start if start is not None else 1
            numbered = [
                {"number": base + idx, "text": line}
                for idx, line in enumerate(lines)
            ]

            meta = {
                "total_lines": len(lines),
                "bytes": len(raw_text.encode("utf-8")),
            }

            return {
                "output": raw_text,
                "lines": numbered,
                "meta": meta,
                "returncode": 0,
            }

        # Fallback: Local Filesystem
        try:
            p = Path(path_arg).expanduser().resolve()
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()

            if start is not None and end is not None:
                # Python uses 0-indexing, users use 1-indexing
                start_idx = max(0, start - 1)
                end_idx = min(len(all_lines), end)
                selected = all_lines[start_idx:end_idx]
                base = start
            else:
                selected = all_lines
                base = 1

            raw_text = "".join(selected)
            if raw_text and not raw_text.endswith("\n"):
                raw_text += "\n"

            numbered = [
                {"number": base + idx, "text": line}
                for idx, line in enumerate(selected)
            ]

            meta = {
                "total_lines": len(selected),
                "bytes": len(raw_text.encode("utf-8")),
            }

            return {
                "output": raw_text,
                "lines": numbered,
                "meta": meta,
                "returncode": 0,
            }

        except Exception as e:
            return {"output": f"Error reading file: {e}", "returncode": 1}


@dataclass
class WriteFile:
    name: str = "write_file"
    description: str = (
        "Write UTF-8 text to a file, overwriting its contents. Use this for direct rewrites or for creating helper files (like temporary patches) before calling apply_diff; pair with read_file when validating changes."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        path_arg = str(args.get("path", ""))
        content = str(args.get("content", ""))

        if not path_arg or content is None:
            return {"output": "Missing path or content", "returncode": 2}

        # Sandbox Environment
        if env is not None:
            # Use base64 to prevent issues with special characters in the content
            b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            cmd = (
                f"mkdir -p {shlex.quote(os.path.dirname(path_arg))} && "
                f"printf '{b64_content}' | base64 -d > {shlex.quote(path_arg)}"
            )
            return env.execute(cmd)

        # Fallback: Local Filesystem
        try:
            p = Path(path_arg).expanduser().resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8", errors="replace")
            return {"output": f"Wrote file: {path_arg}", "returncode": 0}
        except Exception as e:
            return {"output": f"Error writing file: {e}", "returncode": 1}


register(ReadFile())
register(WriteFile())
