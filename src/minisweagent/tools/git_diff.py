from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from . import register

@dataclass
class GitDiff:
    name: str = "git_diff"
    description: str = "Show the current uncommitted changes in /testbed using git diff. Use this to inspect what has been modified before generating or applying patches."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},  # No arguments needed
            "required": [],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        # Standard git diff command
        cmd = "git diff"
        
        if env:
            return env.execute(cmd)
        
        import subprocess
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout
            if not output:
                output = "No changes detected."
            return {"output": output, "returncode": 0}
        except Exception as e:
            return {"output": str(e), "returncode": 1}

register(GitDiff())