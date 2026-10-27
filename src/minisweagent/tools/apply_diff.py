from __future__ import annotations

from dataclasses import dataclass, field

from . import REGISTRY, register


@dataclass
class ApplyDiff:
    # Tool metadata exposed to the agent
    name: str = "apply_diff"
    description: str = "Apply a unified diff to modify files in /testbed. Use this for structured, multi-file edits after inspecting code with search_files or read_file; ideal when producing precise patches instead of rewriting entire files."

    # Input schema the agent uses to call this tool
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "patch": {
                    "type": "string",
                    "description": "Patch to apply in unified diff format.",
                },
                "strip": {
                    "type": "integer",
                    "description": "Number of leading components to strip from file paths in the patch.",
                    "default": 1,
                },
            },
            "required": ["patch"],
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

        # Get the patch content from args

        patch_content = (args.get("patch") or "").strip()
        if not patch_content:
            return {"output": "Patch cannot be empty.", "returncode": 2}
        
        # Normalize line endings

        patch_content = patch_content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove fenced code block markers if present

        if patch_content.startswith("```"):
            while patch_content.startswith("```"):
                first_newline = patch_content.find("\n")
                if first_newline == -1:
                    return {"output": "Invalid fenced patch block.", "returncode": 2}
                patch_content = patch_content[first_newline + 1:].strip()
            if patch_content.endswith("```"):
                patch_content = patch_content.rsplit("```", 1)[0].strip()

        # Basic validation of unified diff format

        if "@@" not in patch_content:
            return {"output": "Invalid patch: missing hunk markers (@@).", "returncode": 2}

        if "---" not in patch_content or "+++" not in patch_content:
            return {"output": "Invalid patch: missing file headers.", "returncode": 2}
        
        # Write the patch content to a temporary file in the sandbox

        write_args = {
            "path": "/tmp/patch.diff",
            "content": patch_content,
        }
        write_result = REGISTRY["write_file"](write_args, env)

        if write_result["returncode"] != 0:
            return {
                "output": f"Failed to write patch file: {write_result['output']}",
                "returncode": write_result["returncode"],
            }

        strip = args.get("strip", 1)

        # Attempt to apply the patch with dry-run first

        dry_cmd = f"cd /testbed && patch --dry-run -p{strip} < /tmp/patch.diff"
        dry_result = env.execute(dry_cmd)

        if dry_result["returncode"] != 0:
            dry_cmd_l = f"cd /testbed && patch --dry-run -l -p{strip} < /tmp/patch.diff"
            dry_result_l = env.execute(dry_cmd_l)

            if dry_result_l["returncode"] != 0:
                return {
                    "output": f"Failed to apply patch: {dry_result['output']}",
                    "returncode": dry_result["returncode"],
                }

            # If dry-run with -l succeeded, use that to apply
            patch_cmd = f"cd /testbed && patch -l -p{strip} < /tmp/patch.diff"
            patch_result = env.execute(patch_cmd)
        else:
            # Apply the patch for real
            patch_cmd = f"cd /testbed && patch -p{strip} < /tmp/patch.diff"
            patch_result = env.execute(patch_cmd)

        # Check if patch application succeeded
        if patch_result["returncode"] != 0:
            return {
                "output": f"Failed to apply patch: {patch_result['output']}",
                "returncode": patch_result["returncode"],
            }

        # Success
        return {
            "output": "Patch applied successfully.",
            "returncode": patch_result["returncode"],
        }


register(ApplyDiff())
