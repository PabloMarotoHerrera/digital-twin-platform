from __future__ import annotations

import carb
import omni.usd
from custom_aec.modeling import api as aec_api
from pxr import Sdf

from .aec_inspection import collect_aec_inventory
from .results import tool_result


DEFAULT_BLOCK_PATH = "/World/Building/Block_01"


def create_aec_block(width: float = 10.0, depth: float = 8.0, height: float = 3.0, name: str | None = None) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    width = _positive(width, "width")
    depth = _positive(depth, "depth")
    height = _positive(height, "height")
    block = aec_api.create_aec_block(stage, width=width, depth=depth, height=height, name=name or "Block_01")
    omni.usd.get_context().get_selection().set_selected_prim_paths([block.GetPath().pathString], True)
    inventory = collect_aec_inventory(stage)
    block_surfaces = [surface.GetPath().pathString for surface in inventory["surfaces"] if surface.GetPath().HasPrefix(block.GetPath())]
    carb.log_info(f"[Energy Twin Agent] Created AEC block through native AEC API: {block.GetPath()}")
    return tool_result(
        True,
        "He creado un bloque de prueba usando la misma estructura que AEC Modelling:",
        {
            "block_path": block.GetPath().pathString,
            "dimensions": f"{width} x {depth} x {height} m",
            "surface_count": len(block_surfaces),
            "idf_exportable": "yes (placeholder; real IDF materials still pending)",
            "details": [
                f"Mass mesh: {block.GetPath().AppendPath('Mass/PrimitiveMesh')}",
                f"Spaces root: {block.GetPath().AppendPath('Spaces')}",
                "Atributos energeticos: aec:energyModel, aec:constructionName, aec:uValue",
                "ThermalViz: sincronizado",
            ],
        },
    )


def assign_basic_energy_metadata(prim_path: str) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return tool_result(False, "No se encontro el prim indicado.", errors=[f"Prim not found: {prim_path}"])
    aec_api.assign_default_energy_metadata(stage, Sdf.Path(prim_path))
    carb.log_info(f"[Energy Twin Agent] Assigned AEC energy metadata to {prim_path}")
    return tool_result(True, "Metadatos energeticos basicos asignados.", {"block_path": prim_path})


def _positive(value, label: str) -> float:
    number = float(value)
    if number <= 0.0:
        raise ValueError(f"{label} must be greater than zero.")
    return number
