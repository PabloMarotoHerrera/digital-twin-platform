from __future__ import annotations


def tool_result(ok: bool, message: str, data: dict | None = None, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict:
    return {
        "ok": bool(ok),
        "message": message,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def not_implemented(message: str) -> dict:
    return tool_result(False, message, {}, [], ["Tool not implemented yet."])

