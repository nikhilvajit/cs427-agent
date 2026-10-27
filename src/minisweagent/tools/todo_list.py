from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import REGISTRY, register


@dataclass
class ToDoList:
    # Tool metadata exposed to the agent
    name: str = "todo_list"
    description: str = "Maintain a simple to-do list inside the sandbox. Use this to track multi-step fixes or follow-up tasks across tool calls; pair with search_files, read_file, and apply_diff to keep a running plan while modifying the codebase."

    # Input schema the agent uses to call this tool
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: add, remove, list, clear",
                    "enum": ["add", "remove", "list", "clear"],
                },
                "item": {
                    "type": "string",
                    "description": "Item to add to the to-do list",
                },
                "index": {
                    "type": "integer",
                    "description": "1-based index of the item to remove from the to-do list",
                },
            },
            "required": ["action"],
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

        # Try to read the existing list; fall back to an empty list if the file doesn't exist or contains invalid JSON
        read_result = REGISTRY["read_file"]({"path": "/testbed/todo_list.json"}, env)

        if read_result["returncode"] != 0:
            todo_list = []
        else:
            try:
                todo_list = json.loads(read_result["output"])
            except:
                todo_list = []

        action = args.get("action")

        # Handle actions

        if action == "add":
            # Normalize the provided item so blank/None doesn't break
            item = (args.get("item") or "").strip()
            if not item:
                return {"output": "Item cannot be empty.", "returncode": 1}
            todo_list.append(item)

        elif action == "remove":
            # Expecting a 1-based index from the agent
            index = args.get("index")
            if index is None or not (1 <= index <= len(todo_list)):
                return {"output": "Invalid index.", "returncode": 1}
            todo_list.pop(index - 1)

        elif action == "list":
            # Show a message if there's nothing to list
            if not todo_list:
                return {"output": "To-do list is empty.", "returncode": 0}
            output = "\n".join(f"{i+1}: {item}" for i, item in enumerate(todo_list))
            return {"output": output, "returncode": 0}

        elif action == "clear":
            todo_list = []

        save_args = {
            "path": "/testbed/todo_list.json",
            "content": json.dumps(todo_list),
        }
        save_result = REGISTRY["write_file"](save_args, env)

        return {
            "output": f"Action '{action}' completed.",
            "returncode": save_result["returncode"],
        }


register(ToDoList())
