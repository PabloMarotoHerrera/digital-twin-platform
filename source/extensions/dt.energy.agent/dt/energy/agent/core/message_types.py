from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentAction:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentAction":
        return cls(
            tool=str(data.get("tool", "")).strip(),
            args=dict(data.get("args") or {}),
            requires_confirmation=bool(data.get("requires_confirmation", False)),
        )

