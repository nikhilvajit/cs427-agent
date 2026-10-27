from __future__ import annotations

from dataclasses import dataclass, field

from . import REGISTRY, register


@dataclass
class SummarizeFile:
    # Tool metadata exposed to the agent
    name: str = "summarize_file"
    description: str = "Generate a concise summary of a file’s contents. Use this to quickly understand large files before deciding where to inspect further; pair with search_files or read_file when narrowing down what needs to be fixed."

    # Input schema the agent uses to call this tool
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the text file to summarize.",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of the summary.",
                    "default": 100,
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        """
        Entry point for the tool. The agent passes `args`, and `env` gives
        access to the sandbox for reading/writing files.
        """

        # Tool should never run outside the sandbox
        if env is None:
            return {"output": "This tool must run inside the sandbox.", "returncode": 2}

        path = str(args.get("path", "")).strip()
        if not path:
            return {"output": "Path cannot be empty.", "returncode": 2}

        # Read the file content
        read_result = REGISTRY["read_file"]({"path": path}, env)

        if read_result["returncode"] != 0:
            return {
                "output": f"Failed to read file: {read_result['output']}",
                "returncode": read_result["returncode"],
            }

        content = read_result["output"]
        max_length = args.get("max_length", 100)

        # Generate a summary
        summary = content.strip()[:max_length]

        return {"output": summary, "returncode": 0}


register(SummarizeFile())
