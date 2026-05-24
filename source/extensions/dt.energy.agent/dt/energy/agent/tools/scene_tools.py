from __future__ import annotations

import carb
import omni.usd

from .results import tool_result


def inspect_current_stage() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        carb.log_warn("[Energy Twin Agent] inspect_current_stage: no stage available")
        return tool_result(False, "No hay ningun stage abierto.", {"prim_count": 0, "world_children": []}, errors=["No stage is currently open."])
    prim_count = sum(1 for _ in stage.Traverse())
    world = stage.GetPrimAtPath("/World")
    world_children = []
    if world and world.IsValid():
        world_children = [child.GetPath().pathString for child in world.GetChildren()]
    return tool_result(True, "Stage inspeccionado.", {"prim_count": prim_count, "details": [f"/World children: {', '.join(world_children) or 'none'}"]})


def get_selected_prims() -> dict:
    selection = omni.usd.get_context().get_selection()
    if selection is None:
        return tool_result(True, "Seleccion actual:", {"selected": []})
    return tool_result(True, "Seleccion actual:", {"selected": list(selection.get_selected_prim_paths())})
