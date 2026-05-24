from __future__ import annotations

from .results import tool_result


def run_energyplus(idf_path: str, weather_path: str) -> dict:
    # TODO: Add explicit user confirmation and a locked-down subprocess wrapper.
    # TODO: Validate EnergyPlus executable path, input paths, weather file, and output folder.
    return tool_result(
        False,
        "EnergyPlus todavia no esta conectado.",
        {"details": [f"IDF: {idf_path}", f"Weather: {weather_path}"]},
        errors=["EnergyPlus execution is disabled in this MVP."],
    )
