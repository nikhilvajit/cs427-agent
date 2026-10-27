from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any
from . import register


@dataclass
class ListDirectory:
    name: str = "list_directory"
    description: str = (
        "List files in a directory up to a chosen depth. Use this to understand project layout before searching or editing code; pairs well with search_files and read_file when locating where a fix should occur."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory to list (default: .)",
                    "default": ".",
                },
                "depth": {
                    "type": "integer",
                    "description": "How many levels deep to list (default: 2)",
                    "default": 2,
                },
            },
            "required": [],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        path = args.get("path", ".")
        depth = args.get("depth", 2)

        # Docker/Sandbox execution
        if env:
            # Uses 'find' command with maxdepth
            cmd = f"find {path} -maxdepth {depth} -not -path '*/.*'"
            return env.execute(cmd)

        # Local fallback
        output = []
        try:
            path = os.path.normpath(path)
            start_level = path.count(os.sep)
            for root, dirs, files in os.walk(path):
                # Calculate current depth
                level = root.count(os.sep) - start_level
                if level >= depth:
                    # Modify dirs in-place to stop os.walk from going deeper
                    dirs[:] = []
                    continue

                # Filter hidden directories (like .git)
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                indent = "  " * level
                output.append(f"{indent}{os.path.basename(root)}/")
                for f in files:
                    if not f.startswith("."):
                        output.append(f"{indent}  {f}")

            return {
                "output": "\n".join(output) if output else "Empty directory",
                "returncode": 0,
            }
        except Exception as e:
            return {"output": str(e), "returncode": 1}


register(ListDirectory())
