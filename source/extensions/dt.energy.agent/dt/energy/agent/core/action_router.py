from __future__ import annotations

import carb

from .message_types import AgentAction
from .safety import is_tool_allowed
from ..tools.registry import get_tool


class ActionRouter:
    def execute(self, action_json: dict) -> dict:
        action = AgentAction.from_dict(action_json)
        allowed, reason = is_tool_allowed(action.tool)
        if not allowed:
            carb.log_warn(f"[Energy Twin Agent] Blocked action {action.tool}: {reason}")
            return {"ok": False, "tool": action.tool, "error": reason}
        tool_spec = get_tool(action.tool)
        if tool_spec is None:
            return {"ok": False, "tool": action.tool, "error": f"Unknown tool: {action.tool}"}
        if not tool_spec.implemented:
            return {
                "ok": False,
                "tool": action.tool,
                "message": f"{action.tool} is planned but not implemented yet.",
                "data": {},
                "warnings": [],
                "errors": [f"{action.tool} is not implemented yet."],
            }
        try:
            result = tool_spec.callable(**action.args)
            result.setdefault("ok", True)
            result.setdefault("message", "Done.")
            result.setdefault("data", {})
            result.setdefault("warnings", [])
            result.setdefault("errors", [])
            result["tool"] = action.tool
            return result
        except Exception as exc:
            carb.log_error(f"[Energy Twin Agent] Tool {action.tool} failed: {exc}")
            return {"ok": False, "tool": action.tool, "message": "Tool failed.", "data": {}, "warnings": [], "errors": [str(exc)], "error": str(exc)}
