from __future__ import annotations
import shlex
from dataclasses import dataclass, field
from typing import Any
from . import register


@dataclass
class RunTest:
    name: str = "run_test"
    description: str = (
        "Run tests inside /testbed to confirm whether a fix works. Use this after applying patches or rewriting files to validate behavior; pair with apply_diff or write_file as part of an edit–test cycle."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to run the test (e.g., 'pytest tests/test_models.py' or 'python manage.py test apps.core').",
                }
            },
            "required": ["command"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        command = args.get("command")

        if not command:
            return {"output": "Test command cannot be empty.", "returncode": 2}

        # Sandbox Environment (Docker)
        if env is not None:
            # Treat this just like a bash command, but semantically it's for testing.
            return env.execute(command)

        # Fallback: Local Execution
        import subprocess

        try:
            # splitting the command for subprocess.run is safer
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {
                "output": result.stdout + result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"output": f"Failed to run test: {e}", "returncode": 1}


register(RunTest())
