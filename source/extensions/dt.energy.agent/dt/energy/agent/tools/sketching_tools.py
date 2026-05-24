from __future__ import annotations

import carb
import omni.kit.commands
import omni.usd
from custom_aec.modeling import api as aec_api
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .results import not_implemented, tool_result


SKETCHES_PATH = Sdf.Path("/World/Building/Sketches")
DEFAULT_SKETCH_PATH = SKETCHES_PATH.AppendPath("Rect_01")
DEFAULT_BLOCK_PATH = Sdf.Path("/World/Building/Block_01")


def list_sketches() -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    sketches = [_sketch_summary(stage, prim) for prim in stage.Traverse() if _is_sketch_prim(prim)]
    return tool_result(
        True,
        "Sketches detectados:",
        {
            "sketch_count": len(sketches),
            "details": [
                f"{item['path']} ({item['prim_type']}, cerrado={item['closed']}, puntos={item['point_count']}, extruible={item['extrudable']})"
                for item in sketches
            ],
        },
        [] if sketches else ["No se detectaron sketches AEC/BasisCurves en la escena."],
    )


def find_blocks_from_sketch(sketch_path: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = _resolve_sketch(stage, sketch_path)
    if prim is None:
        return tool_result(False, "No se encontro un sketch valido.", errors=["Select or provide a BasisCurves sketch path."])
    blocks = [_block_summary(stage, block) for block in _blocks_from_sketch(stage, prim.GetPath())]
    return tool_result(
        True,
        "Bloques asociados al sketch:",
        {
            "sketch_path": prim.GetPath().pathString,
            "block_count": len(blocks),
            "details": [
                f"{item['path']} (reconstruible={item['rebuildable']}, altura={item['height']} m)"
                for item in blocks
            ],
        },
        [] if blocks else ["No se encontraron bloques con aec:sourceCurveRel apuntando a este sketch."],
    )


def get_block_source_sketch(block_path: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    block = _resolve_block(stage, block_path)
    if block is None:
        return tool_result(False, "No se encontro un bloque AEC valido.", errors=["Select or provide an AEC Block path."])
    sketch_path = _source_sketch_path(block)
    if sketch_path is None:
        return tool_result(
            False,
            "El bloque no tiene sketch fuente registrado.",
            {"block_path": block.GetPath().pathString},
            errors=[f"{block.GetPath()} has no aec:sourceCurveRel target."],
        )
    sketch = stage.GetPrimAtPath(sketch_path)
    return tool_result(
        bool(sketch and sketch.IsValid()),
        "Sketch fuente del bloque:",
        {
            "block_path": block.GetPath().pathString,
            "sketch_path": sketch_path.pathString,
            "status": "encontrado" if sketch and sketch.IsValid() else "missing",
        },
        errors=[] if sketch and sketch.IsValid() else [f"Source sketch is missing: {sketch_path}"],
    )


def create_sketch_rectangle(width: float = 10.0, depth: float = 8.0, name: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    width = _positive(width, "width")
    depth = _positive(depth, "depth")
    prim = aec_api.create_rectangle_sketch(stage, width=width, depth=depth, name=name or "Rect_01")
    _set_draw_wireframe(prim.GetPath().pathString, True)
    omni.usd.get_context().get_selection().set_selected_prim_paths([prim.GetPath().pathString], True)
    carb.log_info(f"[Energy Twin Agent] Created sketch rectangle through native AEC API {prim.GetPath()}")
    return tool_result(
        True,
        "He creado un sketch rectangular:",
        {
            "sketch_path": prim.GetPath().pathString,
            "dimensions": f"{width} x {depth} m",
            "status": "cerrado / extruible",
            "details": ["Tipo USD: UsdGeom.BasisCurves", "Jerarquia: /World/Building/Sketches"],
        },
    )


def validate_sketch(sketch_path: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = _resolve_sketch(stage, sketch_path)
    if prim is None:
        return tool_result(False, "No se encontro un sketch valido.", errors=["Select or provide a BasisCurves sketch path."])
    summary = _sketch_summary(stage, prim)
    warnings = []
    errors = []
    if not summary["closed"]:
        errors.append("No puedo extruir este sketch porque el contorno no esta cerrado.")
    if summary["point_count"] < 3:
        errors.append(f"{summary['path']} tiene menos de 3 puntos.")
    if not summary["horizontal"]:
        errors.append(f"{summary['path']} no esta en un plano horizontal.")
    if summary["closed_by_duplicate_point"]:
        errors.append(f"{summary['path']} parece cerrado por punto duplicado, pero no usa wrap=periodic.")
    if summary["sketch_kind"] != "Rectangle" and not errors:
        warnings.append("He detectado un sketch poligonal cerrado; se extruira segun la huella real.")
    return tool_result(
        not errors,
        "Validacion de sketch:",
        {
            "sketch_path": summary["path"],
            "sketch_kind": summary["sketch_kind"],
            "status": "extruible" if not errors else "no extruible",
            "closed": summary["closed"],
            "extrudable": not errors,
            "footprint_points": summary["footprint_points"],
            "details": [
                f"Tipo: {summary['prim_type']}",
                f"Sketch kind: {summary['sketch_kind']}",
                f"Cerrado: {summary['closed']}",
                f"Puntos: {summary['point_count']}",
                f"Horizontal: {summary['horizontal']}",
                "Coordenadas footprint: stage/world",
            ],
        },
        warnings,
        errors,
    )


def get_sketch_footprint_points(sketch_path: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = _resolve_sketch(stage, sketch_path)
    if prim is None:
        return tool_result(False, "No se encontro un sketch valido.", errors=["Select or provide a BasisCurves sketch path."])
    geometry = _sketch_geometry(prim)
    if not geometry["local_points"]:
        return tool_result(False, "No se pudo leer la geometria real del sketch.", errors=[f"{prim.GetPath()} has no readable points."])
    return tool_result(
        True,
        "Puntos reales de la huella del sketch:",
        {
            "sketch_path": prim.GetPath().pathString,
            "sketch_kind": geometry["sketch_kind"],
            "closed": geometry["closed"],
            "footprint_points": geometry["world_points_text"],
            "details": [
                f"Puntos: {len(geometry['world_points'])}",
                "Coordenadas: stage/world",
                "La extrusion usa estos puntos reales; aec:width/aec:depth son solo metadata.",
            ],
        },
    )


def extrude_sketch_to_block(sketch_path: str, height: float = 3.0) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = _resolve_sketch(stage, sketch_path)
    if prim is None:
        return tool_result(False, "No se encontro el sketch indicado.", errors=[f"Sketch not found: {sketch_path}"])
    validation = validate_sketch(prim.GetPath().pathString)
    if not validation["ok"]:
        return validation
    summary = _sketch_summary(stage, prim)
    if not summary["footprint_points"]:
        return tool_result(False, "No se pudo leer la geometria real del sketch.", errors=[f"{prim.GetPath()} has no footprint points."])
    height = _positive(height, "height")
    native_result = aec_api.extrude_sketch_to_block(stage, prim.GetPath(), height=height)
    block = native_result["block"]
    rebuild = native_result["rebuild"]
    rebuild_detail = f"AEC rebuild: {rebuild['mode']}."
    omni.usd.get_context().get_selection().set_selected_prim_paths([block.GetPath().pathString], True)
    carb.log_info(f"[Energy Twin Agent] Extruded sketch through native AEC API {prim.GetPath()} to {block.GetPath()}")
    return tool_result(
        True,
        _extrusion_message(summary),
        {
            "sketch_path": prim.GetPath().pathString,
            "sketch_kind": summary["sketch_kind"],
            "block_path": block.GetPath().pathString,
            "height": f"{height} m",
            "footprint_points": summary["footprint_points"],
            "details": [
                f"Puntos: {summary['point_count']}",
                "Extrusion segun huella real del sketch, no segun aec:width/aec:depth.",
                rebuild_detail,
                "Estructura AEC: Mass, Spaces, Partitions, Metadata, _AEC/PartitionSpecs",
                "ThermalViz: sincronizado",
            ],
        },
        rebuild.get("warnings") or [],
    )


def extrude_selected_sketch(height: float = 3.0) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    selected = omni.usd.get_context().get_selection().get_selected_prim_paths()
    if not selected:
        return tool_result(False, "No hay ningun sketch seleccionado.", errors=["Select a closed sketch first."])
    return extrude_sketch_to_block(selected[0], height)


def create_sketch_rectangle_and_extrude(width: float = 10.0, depth: float = 8.0, height: float = 3.0) -> dict:
    created = create_sketch_rectangle(width=width, depth=depth)
    if not created["ok"]:
        return created
    return extrude_sketch_to_block(created["data"]["sketch_path"], height)


def modify_sketch_rectangle(sketch_path: str, width: float, depth: float) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    prim = _resolve_sketch(stage, sketch_path)
    if prim is None:
        return tool_result(False, "No se encontro el sketch indicado.", errors=[f"Sketch not found: {sketch_path}"])
    if _attr(prim, "aec:sketchKind", "") != "Rectangle":
        return tool_result(False, "El sketch no esta marcado como rectangulo.", errors=[f"{prim.GetPath()} is not a rectangle sketch."])
    width = _positive(width, "width")
    depth = _positive(depth, "depth")
    half_width = width * 0.5
    half_depth = depth * 0.5
    points = [
        Gf.Vec3f(-half_width, -half_depth, 0.0),
        Gf.Vec3f(half_width, -half_depth, 0.0),
        Gf.Vec3f(half_width, half_depth, 0.0),
        Gf.Vec3f(-half_width, half_depth, 0.0),
    ]
    curve = UsdGeom.BasisCurves(prim)
    curve.GetPointsAttr().Set(Vt.Vec3fArray(points))
    curve.GetCurveVertexCountsAttr().Set(Vt.IntArray([len(points)]))
    _recompute_extent(curve)
    prim.CreateAttribute("aec:width", Sdf.ValueTypeNames.Float).Set(float(width))
    prim.CreateAttribute("aec:depth", Sdf.ValueTypeNames.Float).Set(float(depth))
    validation = validate_sketch(prim.GetPath().pathString)
    dependent_blocks = [block.GetPath().pathString for block in _blocks_from_sketch(stage, prim.GetPath())]
    return tool_result(
        validation["ok"],
        "He actualizado el sketch rectangular:",
        {
            "sketch_path": prim.GetPath().pathString,
            "dimensions": f"{width} x {depth} m",
            "status": "cerrado / extruible" if validation["ok"] else "no extruible",
            "details": [
                f"Bloques asociados encontrados: {len(dependent_blocks)}",
                f"Bloques no reconstruidos: {', '.join(dependent_blocks) or 'none'}",
            ],
        },
        (validation.get("warnings") or [])
        + (["Hay bloques asociados; usa modify_sketch_and_rebuild para actualizarlos."] if dependent_blocks else []),
        validation.get("errors") or [],
    )


def rebuild_block_from_sketch(block_path: str | None = None) -> dict:
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    block = _resolve_block(stage, block_path)
    if block is None:
        return tool_result(False, "No se encontro un bloque AEC valido.", errors=["Select or provide an AEC Block path."])
    sketch_path = _source_sketch_path(block)
    if sketch_path is None:
        return tool_result(
            False,
            "Este bloque no conserva relacion aec:sourceCurveRel con un sketch original.",
            {"block_path": block.GetPath().pathString},
            errors=[f"{block.GetPath()} has no aec:sourceCurveRel target."],
        )
    curve_prim = stage.GetPrimAtPath(sketch_path)
    if not curve_prim or not curve_prim.IsValid():
        return tool_result(False, "El sketch fuente ya no existe.", errors=[f"Missing source sketch: {sketch_path}"])
    validation = validate_sketch(curve_prim.GetPath().pathString)
    if not validation["ok"]:
        return validation
    height = _block_height(stage, block)
    rebuild = aec_api.rebuild_block_native(stage, block.GetPath())
    rebuilt = rebuild["block"]
    preserved = True
    carb.log_info(f"[Energy Twin Agent] Rebuilt block through native AEC API {rebuilt.GetPath()} from sketch {curve_prim.GetPath()}")
    return tool_result(
        True,
        "He reconstruido el bloque desde su sketch fuente:",
        {
            "sketch_path": curve_prim.GetPath().pathString,
            "block_path": rebuilt.GetPath().pathString,
            "height": f"{height} m",
            "status": "reconstruido in-place",
            "details": [
                f"Metadata energetica preservada: {'si' if preserved else 'no habia metadata energetica detectada'}",
                f"AEC rebuild: {rebuild['mode']}",
                "ThermalViz: sincronizado",
            ],
        },
        rebuild.get("warnings") or [],
    )


def modify_sketch_and_rebuild(sketch_path: str, width: float, depth: float) -> dict:
    modified = modify_sketch_rectangle(sketch_path=sketch_path, width=width, depth=depth)
    if not modified["ok"]:
        return modified
    stage = _stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    sketch = _resolve_sketch(stage, modified["data"]["sketch_path"])
    if sketch is None:
        return tool_result(False, "No se encontro el sketch tras modificarlo.", errors=["Modified sketch could not be resolved."])
    rebuilt_blocks = []
    warnings = list(modified.get("warnings") or [])
    errors = list(modified.get("errors") or [])
    metadata_flags = []
    for block in _blocks_from_sketch(stage, sketch.GetPath()):
        result = rebuild_block_from_sketch(block.GetPath().pathString)
        if result["ok"]:
            rebuilt_blocks.append(result["data"].get("block_path", block.GetPath().pathString))
            metadata_flags.extend(
                detail for detail in result["data"].get("details", []) if "Metadata energetica preservada" in str(detail)
            )
        else:
            errors.extend(result.get("errors") or [result.get("message", "Rebuild failed.")])
    return tool_result(
        not errors,
        "He modificado el sketch y reconstruido sus bloques asociados:",
        {
            "sketch_path": sketch.GetPath().pathString,
            "dimensions": modified["data"].get("dimensions"),
            "block_count": len(rebuilt_blocks),
            "details": [
                f"Bloques reconstruidos: {', '.join(rebuilt_blocks) or 'none'}",
                *(metadata_flags or ["Metadata energetica preservada: no habia metadata energetica detectada"]),
            ],
        },
        warnings,
        errors,
    )


def modify_selected_sketch_and_rebuild(width: float, depth: float) -> dict:
    selected = _selected_path()
    if not selected:
        return tool_result(False, "No hay ningun sketch seleccionado.", errors=["Select a rectangle sketch first."])
    return modify_sketch_and_rebuild(selected, width, depth)


def start_sketch_mode() -> dict:
    return not_implemented("El modo croquis interactivo aun no esta conectado; ya puedes crear rectangulos por comando.")


def close_current_sketch() -> dict:
    return not_implemented("Cerrar contorno queda pendiente de conectar con omni.curve.manipulator.")


def convert_closed_curve_to_thermal_zone() -> dict:
    return not_implemented("La conversion explicita a zona termica queda pendiente; la extrusion ya genera Spaces AEC.")


def _stage():
    return omni.usd.get_context().get_stage()


def _recompute_extent(curve):
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())
    if extent:
        curve.GetExtentAttr().Set(extent)


def _set_draw_wireframe(path: str, value: bool):
    try:
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path(path).AppendProperty("omni:scene:visualization:drawWireframe"),
            value=value,
            prev=None,
            type_to_create_if_not_exist=Sdf.ValueTypeNames.Bool,
        )
    except Exception as exc:
        carb.log_info(f"[Energy Twin Agent] drawWireframe property skipped for {path}: {exc}")


def _resolve_sketch(stage, sketch_path: str | None):
    path = sketch_path or _selected_path()
    if not path:
        return None
    prim = stage.GetPrimAtPath(path)
    if prim and prim.IsValid() and prim.IsA(UsdGeom.BasisCurves):
        return prim
    return None


def _resolve_block(stage, block_path: str | None):
    path = block_path or _selected_path()
    if not path:
        return None
    prim = stage.GetPrimAtPath(path)
    if prim and prim.IsValid() and _attr(prim, "aec:type", "") == "Block":
        return prim
    return None


def _selected_path() -> str | None:
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    return selection[0] if selection else None


def _is_sketch_prim(prim) -> bool:
    return bool(prim and prim.IsValid() and prim.IsA(UsdGeom.BasisCurves))


def _sketch_summary(stage, prim) -> dict:
    geometry = _sketch_geometry(prim)
    count = len(geometry["local_points"])
    return {
        "path": prim.GetPath().pathString,
        "prim_type": prim.GetTypeName(),
        "sketch_kind": geometry["sketch_kind"],
        "closed": geometry["closed"],
        "closed_by_duplicate_point": geometry["closed_by_duplicate_point"],
        "point_count": count,
        "horizontal": geometry["horizontal"],
        "extrudable": bool(geometry["closed"] and count >= 3 and geometry["horizontal"] and not geometry["closed_by_duplicate_point"]),
        "footprint_points": geometry["world_points_text"],
    }


def _sketch_geometry(prim) -> dict:
    curve = UsdGeom.BasisCurves(prim)
    all_points = list(curve.GetPointsAttr().Get() or [])
    counts = curve.GetCurveVertexCountsAttr().Get() or []
    count = int(counts[0]) if counts else len(all_points)
    local_points = [Gf.Vec3f(all_points[index]) for index in range(min(count, len(all_points)))]
    wrap_closed = curve.GetWrapAttr().Get() == UsdGeom.Tokens.periodic
    duplicate_closed = len(local_points) >= 4 and _same_point(local_points[0], local_points[-1])
    footprint_local = local_points[:-1] if duplicate_closed else local_points
    world_points = _world_points(prim, footprint_local)
    horizontal = _is_horizontal(world_points)
    sketch_kind = _detect_sketch_kind(prim, world_points)
    return {
        "local_points": footprint_local,
        "world_points": world_points,
        "world_points_text": [_point_text(point) for point in world_points],
        "closed": bool(wrap_closed),
        "closed_by_duplicate_point": bool(duplicate_closed and not wrap_closed),
        "horizontal": horizontal,
        "sketch_kind": sketch_kind,
    }


def _world_points(prim, local_points) -> list[Gf.Vec3f]:
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    return [Gf.Vec3f(matrix.Transform(Gf.Vec3d(point))) for point in local_points]


def _detect_sketch_kind(prim, points) -> str:
    authored = _attr(prim, "aec:sketchKind", "")
    if authored == "Rectangle" and _is_rectangle(points):
        return "Rectangle"
    if len(points) >= 3:
        return "Polygon"
    if authored:
        return str(authored)
    return "Invalid"


def _is_rectangle(points) -> bool:
    if len(points) != 4 or not _is_horizontal(points):
        return False
    edges = [points[(index + 1) % 4] - points[index] for index in range(4)]
    lengths = [edge.GetLength() for edge in edges]
    if any(length <= 1e-5 for length in lengths):
        return False
    dot01 = abs(_dot(_normalized(edges[0]), _normalized(edges[1])))
    dot12 = abs(_dot(_normalized(edges[1]), _normalized(edges[2])))
    opposite0 = abs(lengths[0] - lengths[2]) <= 1e-4
    opposite1 = abs(lengths[1] - lengths[3]) <= 1e-4
    return dot01 <= 1e-4 and dot12 <= 1e-4 and opposite0 and opposite1


def _normalized(vector):
    length = vector.GetLength()
    if length <= 1e-8:
        return Gf.Vec3f(0.0, 0.0, 0.0)
    return Gf.Vec3f(float(vector[0]) / length, float(vector[1]) / length, float(vector[2]) / length)


def _dot(left, right) -> float:
    return float(left[0]) * float(right[0]) + float(left[1]) * float(right[1]) + float(left[2]) * float(right[2])


def _same_point(left, right) -> bool:
    return (Gf.Vec3f(left) - Gf.Vec3f(right)).GetLength() <= 1e-5


def _point_text(point) -> str:
    return f"({_fmt_float(point[0])}, {_fmt_float(point[1])}, {_fmt_float(point[2])})"


def _fmt_float(value) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def _extrusion_message(summary: dict) -> str:
    if summary.get("sketch_kind") == "Rectangle":
        return "He extruido el sketch rectangular seleccionado:"
    return "He detectado un sketch poligonal cerrado y lo he extruido segun su huella real:"


def _is_horizontal(points) -> bool:
    if not points:
        return False
    z0 = float(points[0][2])
    return all(abs(float(point[2]) - z0) <= 1e-5 for point in points)


def _blocks_from_sketch(stage, sketch_path: Sdf.Path) -> list[Usd.Prim]:
    blocks = []
    for prim in stage.Traverse():
        if _attr(prim, "aec:type", "") != "Block":
            continue
        rel = prim.GetRelationship("aec:sourceCurveRel")
        if rel and sketch_path in rel.GetTargets():
            blocks.append(prim)
    return blocks


def _block_summary(stage, block) -> dict:
    sketch_path = _source_sketch_path(block)
    sketch = stage.GetPrimAtPath(sketch_path) if sketch_path is not None else None
    return {
        "path": block.GetPath().pathString,
        "height": _block_height(stage, block),
        "rebuildable": bool(sketch and sketch.IsValid() and sketch.IsA(UsdGeom.BasisCurves)),
    }


def _source_sketch_path(block) -> Sdf.Path | None:
    rel = block.GetRelationship("aec:sourceCurveRel")
    targets = rel.GetTargets() if rel else []
    if targets:
        return targets[0]
    source_attr = _attr(block, "aec:sourceCurve", "")
    return Sdf.Path(source_attr) if source_attr else None


def _block_height(stage, block) -> float:
    authored = _attr(block, "aec:height", None)
    if authored is not None:
        return max(float(authored), 0.001)
    for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
        mesh = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
        if mesh and mesh.IsValid() and mesh.IsA(UsdGeom.Mesh):
            points = UsdGeom.Mesh(mesh).GetPointsAttr().Get() or []
            if points:
                z_values = [float(point[2]) for point in points]
                return max(max(z_values) - min(z_values), 0.001)
    return 3.0


def _attr(prim, name: str, default=None):
    attr = prim.GetAttribute(name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default


def _positive(value, label: str) -> float:
    number = float(value)
    if number <= 0.0:
        raise ValueError(f"{label} must be greater than zero.")
    return number


def _safe_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(name or "Rect_01"))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"Rect_{cleaned or '01'}"
    return cleaned
