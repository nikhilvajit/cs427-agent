from __future__ import annotations

from dataclasses import dataclass, field

from . import REGISTRY, register

@dataclass
class Replace:
    name: str = "replace"
    description: str = "Search and replace text in a file. Use this for small, direct edits without generating a full diff."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "original": {"type": "string", "description": "String value to search for and replace"},
                "replacement": {"type": "string", "description": "String value to replace the original string with"}
            },
            "required": ["path", "original", "replacement"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        original = str(args.get("original", ""))
        replacement = str(args.get("replacement", ""))

        # Tool should never run outside the sandbox
        if env is None:
            return {"output": "This tool must run inside the sandbox.", "returncode": 2}

        if path_arg == "":
            return {"output": "Missing 'path' for replace mode", "returncode": 2}

        if original == "":
            return {"output": "Missing 'original' for replace mode", "returncode": 2}

        if replacement == "":
            return {"output": "Missing 'replacement' for replace mode", "returncode": 2}

        # Read the file using read_file tool
        read_res = REGISTRY["read_file"]({"path": path_arg}, env)
        if read_res["returncode"] != 0:
            return {
                "output": f"Failed to read file: {read_res['output']}",
                "returncode": read_res["returncode"],
            }

        # read_file returns the file content inside "output"
        text = read_res["output"]
        new_text = text.replace(original, replacement)

        if new_text == text:
            return {
                "output": "No occurrences found; file unchanged.",
                "returncode": 0,
            }

        # Write back using write_file tool
        write_res = REGISTRY["write_file"](
            {"path": path_arg, "content": new_text},
            env,
        )
        if write_res["returncode"] != 0:
            return {
                "output": f"Failed to write updated file: {write_res['output']}",
                "returncode": write_res["returncode"],
            }

        return {
            "output": "Replacement performed successfully.",
            "returncode": 0,
        }

register(Replace())
