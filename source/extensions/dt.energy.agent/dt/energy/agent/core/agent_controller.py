from __future__ import annotations

import carb

from .action_router import ActionRouter
from ..llm.mock_provider import MockLLMProvider


class AgentController:
    def __init__(self, llm_provider=None, router=None):
        self._llm_provider = llm_provider or MockLLMProvider()
        self._router = router or ActionRouter()

    def handle_user_message(self, text: str) -> dict:
        context = self._build_context()
        action_json = self._llm_provider.generate_action(text, context)
        carb.log_info(f"[Energy Twin Agent] Mock action: {action_json}")
        return self._with_text(self._router.execute(action_json))

    def execute_direct_tool(self, tool_name: str, args: dict | None = None) -> dict:
        return self._with_text(self._router.execute({"tool": tool_name, "args": args or {}}))

    def _build_context(self) -> dict:
        return {
            "phase": "mvp",
            "llm": "mock",
            "destructive_actions_enabled": False,
        }

    def _with_text(self, result: dict) -> dict:
        result["text"] = _result_to_text(result)
        return result


def _result_to_text(result: dict) -> str:
    message = result.get("message") or ("Done." if result.get("ok") else "Action failed.")
    lines = [message]
    data = result.get("data") or {}
    warnings = result.get("warnings") or []
    errors = result.get("errors") or []

    if data:
        for line in _data_lines(data):
            lines.append(f"- {line}")
    if warnings:
        lines.append("Advertencias:")
        lines.extend(f"- {item}" for item in warnings)
    if errors:
        lines.append("Errores:")
        lines.extend(f"- {item}" for item in errors)
    return "\n".join(lines)


def _data_lines(data: dict) -> list[str]:
    preferred = [
        "block_count",
        "space_count",
        "surface_count",
        "exportable_surface_count",
        "thermal_material_count",
        "thermalviz_synced_block_count",
        "thermalviz_unsynced_block_count",
        "selected",
        "sketch_count",
        "sketch_path",
        "sketch_kind",
        "closed",
        "extrudable",
        "block_path",
        "dimensions",
        "height",
        "footprint_points",
        "status",
        "idf_exportable",
        "output_path",
        "reference_path",
        "source_file",
        "line_count",
        "snap_point_count",
        "dxf_reference_count",
        "point",
        "distance",
        "entity_path",
        "within_tolerance",
        "surface_path",
        "vertex_count",
        "face_vertex_counts",
        "face_vertex_indices",
        "bbox",
        "approx_normal",
        "surface_kind",
        "matches_footprint",
    ]
    lines = []
    for key in preferred:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(item) for item in value) if value else "none"
        lines.append(f"{_label(key)}: {value}")
    details = data.get("details")
    if isinstance(details, list):
        lines.extend(str(item) for item in details)
    return lines


def _label(key: str) -> str:
    labels = {
        "block_count": "Bloques AEC",
        "space_count": "Zonas termicas / AEC Spaces",
        "surface_count": "Superficies AEC",
        "exportable_surface_count": "Superficies con boundary",
        "thermal_material_count": "Materiales termicos completos",
        "thermalviz_synced_block_count": "Bloques sincronizados ThermalViz",
        "thermalviz_unsynced_block_count": "Bloques pendientes ThermalViz",
        "selected": "Seleccion",
        "sketch_count": "Sketches",
        "sketch_path": "Sketch",
        "sketch_kind": "Tipo de sketch",
        "closed": "Cerrado",
        "extrudable": "Extruible",
        "block_path": "Prim principal",
        "dimensions": "Dimensiones",
        "height": "Altura",
        "footprint_points": "Huella",
        "status": "Estado",
        "idf_exportable": "Estado exportable IDF",
        "output_path": "Archivo",
        "reference_path": "Referencia DXF",
        "source_file": "Archivo fuente",
        "line_count": "Lineas DXF",
        "snap_point_count": "Puntos snap",
        "dxf_reference_count": "Referencias DXF",
        "point": "Punto",
        "distance": "Distancia",
        "entity_path": "Entidad DXF",
        "within_tolerance": "Dentro de tolerancia",
        "surface_path": "Superficie",
        "vertex_count": "Vertices",
        "face_vertex_counts": "Face counts",
        "face_vertex_indices": "Face indices",
        "bbox": "BBox",
        "approx_normal": "Normal aprox.",
        "surface_kind": "Tipo geom.",
        "matches_footprint": "Coincide con huella",
    }
    return labels.get(key, key.replace("_", " ").capitalize())
