from __future__ import annotations

import os
from pathlib import Path


def is_tool_allowed(tool_name: str) -> tuple[bool, str]:
    if not tool_name:
        return False, "Missing tool name."
    from ..tools.registry import get_tool

    tool = get_tool(tool_name)
    if tool is None:
        return True, ""
    if tool.requires_confirmation:
        return False, f"{tool_name} requires confirmation and is not enabled yet."
    return True, ""


def validate_output_path(path_text: str) -> tuple[bool, str]:
    if not path_text or not str(path_text).strip():
        return False, "Output path is empty."
    path = Path(str(path_text)).expanduser()
    if not path.is_absolute():
        return False, "Output path must be absolute."
    try:
        resolved = path.resolve()
    except OSError as exc:
        return False, f"Output path could not be resolved: {exc}"
    allowed_roots = _allowed_roots()
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        roots = ", ".join(str(root) for root in allowed_roots)
        return False, f"Output path is outside allowed folders: {roots}"
    return True, str(resolved)


def _allowed_roots() -> list[Path]:
    roots = [Path("C:/temp"), Path("C:/tmp")]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        roots.append(Path(user_profile) / "Documents")
        roots.append(Path(user_profile) / "Desktop")
    return [root.resolve() for root in roots]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
