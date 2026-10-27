from __future__ import annotations
import shlex
from dataclasses import dataclass, field
from typing import Any
from . import register

@dataclass
class SearchFiles:
    # Metadata for the agent
    name: str = "search_files"
    description: str = "Recursively search files for a text pattern and show matching lines with numbers. Use this to locate code before editing; pair with read_file for context checks and with replace or apply_diff when preparing targeted fixes."
    
    # Schema for the AI to understand how to use this tool
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "The text string to search for"
                },
                "path": {
                    "type": "string", 
                    "description": "Directory to search in (defaults to current directory .)",
                    "default": "."
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        query = args.get("query")
        path = args.get("path", ".")

        if not query:
            return {"output": "Query cannot be empty.", "returncode": 2}

        # Prepare the grep command
        # -r: recursive
        # -n: show line numbers
        # -I: ignore binary files
        cmd = f"grep -rnI {shlex.quote(query)} {shlex.quote(path)} | head -n 20"

        if env:
            # Run inside the SWE-bench sandbox
            return env.execute(cmd)
        else:
            # Run locally
            import subprocess
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                output = result.stdout + result.stderr
                if not output:
                    output = f"No matches found for '{query}'."
                return {"output": output, "returncode": result.returncode}
            except Exception as e:
                return {"output": str(e), "returncode": 1}

register(SearchFiles())