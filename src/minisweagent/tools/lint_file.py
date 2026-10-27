from __future__ import annotations
import shlex
from dataclasses import dataclass, field
from typing import Any
from . import register

@dataclass
class LintFile:
    name: str = "lint_file"
    description: str = "Check a Python file for syntax errors. Use this to validate code before applying patches or running tests; pairs well with apply_diff and run_test to catch issues early in the fix cycle."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the python file to lint."
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        path = args.get("path")
        
        if not path:
            return {"output": "Path cannot be empty.", "returncode": 2}

        # Use python's built-in py_compile module to check syntax
        # -q quiets output on success
        cmd = f"python3 -m py_compile {shlex.quote(path)}"

        if env is not None:
            result = env.execute(cmd)
            if result['returncode'] == 0:
                return {"output": f"No syntax errors found in {path}.", "returncode": 0}
            else:
                # The error output usually contains the syntax error details
                return {"output": f"Syntax error detected:\n{result['output']}", "returncode": result['returncode']}

        # Fallback: Local Execution
        import subprocess
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                 return {"output": f"No syntax errors found in {path}.", "returncode": 0}
            else:
                 return {"output": f"Syntax error detected:\n{result.stderr}", "returncode": result.returncode}
        except Exception as e:
            return {"output": f"Failed to lint file: {e}", "returncode": 1}

register(LintFile())