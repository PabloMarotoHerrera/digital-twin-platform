from __future__ import annotations

import os

from .base_provider import LLMProvider


class NvidiaNIMProvider(LLMProvider):
    def __init__(self):
        self._api_key = os.environ.get("NVIDIA_API_KEY", "")

    def generate_action(self, user_message: str, context: dict) -> dict:
        # TODO: Call NVIDIA NIM with a constrained tool-calling prompt.
        # TODO: Validate the returned JSON against mcp.tool_schema before routing.
        if not self._api_key:
            return {"tool": "inspect_current_stage", "args": {}}
        return {"tool": "inspect_current_stage", "args": {}}

