from __future__ import annotations

import math
import os
from pathlib import Path

import carb
import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .results import not_implemented, tool_result


DXF_ROOT = Sdf.Path("/World/Building/DXFReferences")
_EZDXF_AVAILABLE = None


def import_dxf_reference(file_path: str, scale: float = 1.0, z: float = 0.01) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    ok, resolved_or_error = _validate_input_path(file_path)
    if not ok:
        return tool_result(False, "No puedo importar el DXF.", errors=[resolved_or_error])
    scale = max(float(scale), 1e-9)
    z = float(z)

    entities, parser_name, parser_warnings = _read_dxf_entities(resolved_or_error)
    if not entities:
        return tool_result(
            False,
            "No se encontraron entidades DXF importables.",
            {"source_file": resolved_or_error},
            parser_warnings,
            ["El DXF no contiene LINE/LWPOLYLINE/POLYLINE/ARC/CIRCLE legibles en esta fase."],
        )

    root = _ensure_dxf_root(stage)
    reference_name = _safe_name(Path(resolved_or_error).stem or "DXFReference")
    reference_path = Sdf.Path(omni.usd.get_stage_next_free_path(stage, root.GetPath().AppendChild(reference_name).pathString, False))
    reference = UsdGeom.Xform.Define(stage, reference_path).GetPrim()
    reference.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFReference")
    reference.CreateAttribute("aec:sourceFile", Sdf.ValueTypeNames.String).Set(resolved_or_error)
    reference.CreateAttribute("aec:scale", Sdf.ValueTypeNames.Float).Set(float(scale))
    reference.CreateAttribute("aec:snapEnabled", Sdf.ValueTypeNames.Bool).Set(True)
    reference.CreateAttribute("aec:parser", Sdf.ValueTypeNames.String).Set(parser_name)

    geometry_root = UsdGeom.Xform.Define(stage, reference_path.AppendChild("Geometry")).GetPrim()
    geometry_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFGeometry")
    snap_root = UsdGeom.Xform.Define(stage, reference_path.AppendChild("SnapPoints")).GetPrim()
    snap_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFSnapPoints")

    snap_points = []
    for index, entity in enumerate(entities, start=1):
        points = [_scaled_point(point, scale, z) for point in entity["points"]]
        if len(points) < 2:
            continue
        entity_path = geometry_root.GetPath().AppendChild(f"{entity['type']}_{index:04d}")
        _define_curve(stage, entity_path, points, bool(entity.get("closed")))
        entity_prim = stage.GetPrimAtPath(entity_path)
        entity_prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFEntity")
        entity_prim.CreateAttribute("aec:dxfEntityType", Sdf.ValueTypeNames.String).Set(entity["type"])
        entity_prim.CreateAttribute("aec:entityId", Sdf.ValueTypeNames.String).Set(entity.get("id") or str(index))
        for point in points:
            snap_points.append({"point": point, "entity_path": entity_path.pathString})

    unique_snap_points = _unique_snap_points(snap_points)
    _write_snap_points(stage, snap_root.GetPath(), unique_snap_points)
    reference.CreateAttribute("aec:lineCount", Sdf.ValueTypeNames.Int).Set(len(entities))
    reference.CreateAttribute("aec:snapPointCount", Sdf.ValueTypeNames.Int).Set(len(unique_snap_points))
    carb.log_info(f"[Energy Twin Agent] Imported DXF reference {resolved_or_error} to {reference_path}")
    return tool_result(
        True,
        "He importado el DXF como referencia de croquizado:",
        {
            "reference_path": reference_path.pathString,
            "source_file": resolved_or_error,
            "line_count": len(entities),
            "snap_point_count": len(unique_snap_points),
            "details": [
                f"Parser: {parser_name}",
                "Jerarquia: /World/Building/DXFReferences/{NombrePlano}",
                "Snap: vertices y endpoints bajo SnapPoints",
                "Z offset: %.4f m" % z,
            ],
        },
        parser_warnings,
    )


def list_dxf_references() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    root = stage.GetPrimAtPath(DXF_ROOT)
    references = []
    if root and root.IsValid():
        references = [prim for prim in root.GetChildren() if _attr(prim, "aec:type", "") == "DXFReference"]
    details = []
    for prim in references:
        details.append(
            f"{prim.GetPath()} source={_attr(prim, 'aec:sourceFile', 'unknown')} "
            f"lines={_attr(prim, 'aec:lineCount', 0)} snap={_attr(prim, 'aec:snapPointCount', 0)} "
            f"enabled={_attr(prim, 'aec:snapEnabled', False)}"
        )
    return tool_result(
        True,
        "Planos DXF importados:",
        {"dxf_reference_count": len(references), "details": details},
        [] if references else ["No hay referencias DXF bajo /World/Building/DXFReferences."],
    )


def extract_dxf_snap_points(reference_path: str | None = None) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    reference = _resolve_reference(stage, reference_path)
    if reference is None:
        return tool_result(False, "No se encontro una referencia DXF valida.", errors=["Select or provide a DXFReference path."])
    points = _snap_points_from_reference(stage, reference)
    return tool_result(
        True,
        "Puntos snap DXF disponibles:",
        {
            "reference_path": reference.GetPath().pathString,
            "snap_point_count": len(points),
            "snap_points": [_point_text(item["point"]) for item in points[:40]],
            "details": ["Coordenadas: stage/world", "Intersecciones DXF quedan pendientes para una fase posterior."],
        },
    )


def get_nearest_snap_point(world_position, max_distance: float = 0.25) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    position = _coerce_point(world_position)
    if position is None:
        return tool_result(False, "Posicion invalida para snap.", errors=["world_position must be [x, y, z]."])
    max_distance = max(float(max_distance), 0.0)
    candidates = []
    root = stage.GetPrimAtPath(DXF_ROOT)
    if root and root.IsValid():
        for reference in root.GetChildren():
            if _attr(reference, "aec:type", "") == "DXFReference" and _attr(reference, "aec:snapEnabled", False):
                candidates.extend(_snap_points_from_reference(stage, reference))
    nearest = None
    for candidate in candidates:
        distance = (candidate["point"] - position).GetLength()
        if nearest is None or distance < nearest["distance"]:
            nearest = {"point": candidate["point"], "distance": distance, "entity_path": candidate["entity_path"]}
    if nearest is None or nearest["distance"] > max_distance:
        return tool_result(
            False,
            "No encontre un punto snap dentro de la tolerancia.",
            {"max_distance": max_distance},
            errors=["No DXF snap point is within tolerance."],
        )
    return tool_result(
        True,
        "Punto snap DXF mas cercano:",
        {
            "point": _point_text(nearest["point"]),
            "distance": round(float(nearest["distance"]), 5),
            "entity_path": nearest["entity_path"],
            "within_tolerance": True,
        },
    )


def create_sketch_from_dxf_polyline(reference_path: str, polyline_id: str) -> dict:
    return not_implemented("Crear sketch desde polilinea DXF queda preparado, pero aun no interpreta entidades concretas.")


def trace_dxf_outline_to_sketch(reference_path: str | None = None) -> dict:
    return not_implemented("Trazar automaticamente un contorno DXF a sketch queda pendiente de la fase de reconocimiento.")


def ezdxf_available() -> bool:
    global _EZDXF_AVAILABLE
    if _EZDXF_AVAILABLE is not None:
        return _EZDXF_AVAILABLE
    try:
        import ezdxf  # noqa: F401
        _EZDXF_AVAILABLE = True
    except Exception:
        _EZDXF_AVAILABLE = False
    return _EZDXF_AVAILABLE


def _read_dxf_entities(path: str):
    if ezdxf_available():
        try:
            return _read_with_ezdxf(path), "ezdxf", []
        except Exception as exc:
            carb.log_warn(f"[Energy Twin Agent] ezdxf failed, using fallback parser: {exc}")
            entities = _read_ascii_dxf(path)
            return entities, "ascii-fallback", [f"ezdxf fallo y se uso parser fallback: {exc}"]
    return _read_ascii_dxf(path), "ascii-fallback", ["ezdxf no esta instalado; se uso parser DXF ASCII limitado."]


def _read_with_ezdxf(path: str):
    import ezdxf

    doc = ezdxf.readfile(path)
    entities = []
    for entity in doc.modelspace():
        dxftype = entity.dxftype()
        if dxftype == "LINE":
            entities.append({"type": "LINE", "id": str(entity.dxf.handle), "points": [_dxf_point(entity.dxf.start), _dxf_point(entity.dxf.end)]})
        elif dxftype in ("LWPOLYLINE", "POLYLINE"):
            points = [Gf.Vec3f(float(point[0]), float(point[1]), float(point[2]) if dxftype == "POLYLINE" and len(point) > 2 else 0.0) for point in entity.get_points()]
            entities.append({"type": dxftype, "id": str(entity.dxf.handle), "points": points, "closed": bool(entity.closed)})
        elif dxftype == "CIRCLE":
            entities.append({"type": "CIRCLE", "id": str(entity.dxf.handle), "points": _arc_points(entity.dxf.center, entity.dxf.radius, 0.0, 360.0), "closed": True})
        elif dxftype == "ARC":
            entities.append({"type": "ARC", "id": str(entity.dxf.handle), "points": _arc_points(entity.dxf.center, entity.dxf.radius, entity.dxf.start_angle, entity.dxf.end_angle)})
    return entities


def _read_ascii_dxf(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as stream:
        raw = [line.rstrip("\r\n") for line in stream]
    pairs = []
    for index in range(0, len(raw) - 1, 2):
        pairs.append((raw[index].strip(), raw[index + 1].strip()))

    entities = []
    index = 0
    while index < len(pairs):
        code, value = pairs[index]
        if code == "0" and value == "LINE":
            entity, index = _parse_line(pairs, index + 1)
            entities.append(entity)
            continue
        if code == "0" and value == "LWPOLYLINE":
            entity, index = _parse_lwpolyline(pairs, index + 1)
            entities.append(entity)
            continue
        if code == "0" and value == "POLYLINE":
            entity, index = _parse_polyline(pairs, index + 1)
            entities.append(entity)
            continue
        if code == "0" and value in ("ARC", "CIRCLE"):
            entity, index = _parse_arc_or_circle(pairs, index + 1, value)
            if entity:
                entities.append(entity)
            continue
        index += 1
    return entities


def _parse_line(pairs, index):
    values = {}
    while index < len(pairs) and pairs[index][0] != "0":
        values[pairs[index][0]] = pairs[index][1]
        index += 1
    return {
        "type": "LINE",
        "id": values.get("5", str(index)),
        "points": [
            Gf.Vec3f(_float(values.get("10")), _float(values.get("20")), _float(values.get("30"))),
            Gf.Vec3f(_float(values.get("11")), _float(values.get("21")), _float(values.get("31"))),
        ],
    }, index


def _parse_lwpolyline(pairs, index):
    points = []
    flags = 0
    current_x = None
    handle = str(index)
    while index < len(pairs) and pairs[index][0] != "0":
        code, value = pairs[index]
        if code == "5":
            handle = value
        elif code == "70":
            flags = int(_float(value))
        elif code == "10":
            current_x = _float(value)
        elif code == "20" and current_x is not None:
            points.append(Gf.Vec3f(current_x, _float(value), 0.0))
            current_x = None
        index += 1
    return {"type": "LWPOLYLINE", "id": handle, "points": points, "closed": bool(flags & 1)}, index


def _parse_polyline(pairs, index):
    points = []
    flags = 0
    handle = str(index)
    while index < len(pairs):
        code, value = pairs[index]
        if code == "0" and value == "SEQEND":
            return {"type": "POLYLINE", "id": handle, "points": points, "closed": bool(flags & 1)}, index + 1
        if code == "70":
            flags = int(_float(value))
        if code == "5":
            handle = value
        if code == "0" and value == "VERTEX":
            vertex = {}
            index += 1
            while index < len(pairs) and pairs[index][0] != "0":
                vertex[pairs[index][0]] = pairs[index][1]
                index += 1
            points.append(Gf.Vec3f(_float(vertex.get("10")), _float(vertex.get("20")), _float(vertex.get("30"))))
            continue
        index += 1
    return {"type": "POLYLINE", "id": handle, "points": points, "closed": bool(flags & 1)}, index


def _parse_arc_or_circle(pairs, index, entity_type):
    values = {}
    while index < len(pairs) and pairs[index][0] != "0":
        values[pairs[index][0]] = pairs[index][1]
        index += 1
    center = Gf.Vec3f(_float(values.get("10")), _float(values.get("20")), _float(values.get("30")))
    radius = _float(values.get("40"))
    if radius <= 0.0:
        return None, index
    start = 0.0 if entity_type == "CIRCLE" else _float(values.get("50"))
    end = 360.0 if entity_type == "CIRCLE" else _float(values.get("51"))
    return {
        "type": entity_type,
        "id": values.get("5", str(index)),
        "points": _arc_points(center, radius, start, end),
        "closed": entity_type == "CIRCLE",
    }, index


def _arc_points(center, radius, start_angle, end_angle, segments=32):
    center = _dxf_point(center)
    start = math.radians(float(start_angle))
    end = math.radians(float(end_angle))
    if end <= start:
        end += math.tau
    step_count = max(4, int(segments * (end - start) / math.tau))
    return [
        Gf.Vec3f(center[0] + math.cos(start + (end - start) * index / step_count) * radius,
                 center[1] + math.sin(start + (end - start) * index / step_count) * radius,
                 center[2])
        for index in range(step_count + 1)
    ]


def _ensure_dxf_root(stage):
    UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/Building"))
    root = UsdGeom.Xform.Define(stage, DXF_ROOT).GetPrim()
    root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFReferences")
    return root


def _define_curve(stage, path, points, closed):
    curve = UsdGeom.BasisCurves.Define(stage, path)
    curve.GetTypeAttr().Set(UsdGeom.Tokens.linear)
    curve.GetWrapAttr().Set(UsdGeom.Tokens.periodic if closed else UsdGeom.Tokens.nonperiodic)
    curve.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
    curve.GetCurveVertexCountsAttr().Set(Vt.IntArray([len(points)]))
    curve.GetPointsAttr().Set(Vt.Vec3fArray(points))
    curve.CreateWidthsAttr().Set(Vt.FloatArray([0.015] * len(points)))
    UsdGeom.Gprim(curve.GetPrim()).CreateDisplayColorAttr().Set(Vt.Vec3fArray([Gf.Vec3f(0.1, 0.8, 0.95)]))
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())
    if extent:
        curve.GetExtentAttr().Set(extent)
    return curve


def _write_snap_points(stage, snap_root_path, snap_points):
    for index, item in enumerate(snap_points, start=1):
        prim = UsdGeom.Xform.Define(stage, snap_root_path.AppendChild(f"Point_{index:04d}")).GetPrim()
        prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("DXFSnapPoint")
        prim.CreateAttribute("aec:snapPoint", Sdf.ValueTypeNames.Float3).Set(item["point"])
        prim.CreateAttribute("aec:entityPath", Sdf.ValueTypeNames.String).Set(item["entity_path"])
        xform = UsdGeom.Xformable(prim)
        xform.ClearXformOpOrder()
        xform.AddTranslateOp().Set(Gf.Vec3d(item["point"]))


def _snap_points_from_reference(stage, reference):
    snap_root = stage.GetPrimAtPath(reference.GetPath().AppendChild("SnapPoints"))
    if not snap_root or not snap_root.IsValid():
        return []
    points = []
    for prim in snap_root.GetChildren():
        point = _attr(prim, "aec:snapPoint", None)
        if point is not None:
            points.append({"point": Gf.Vec3f(point), "entity_path": _attr(prim, "aec:entityPath", "")})
    return points


def _resolve_reference(stage, reference_path):
    path = reference_path or _selected_path()
    if not path:
        root = stage.GetPrimAtPath(DXF_ROOT)
        refs = [child for child in root.GetChildren()] if root and root.IsValid() else []
        return refs[0] if len(refs) == 1 and _attr(refs[0], "aec:type", "") == "DXFReference" else None
    prim = stage.GetPrimAtPath(path)
    return prim if prim and prim.IsValid() and _attr(prim, "aec:type", "") == "DXFReference" else None


def _selected_path():
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    return selection[0] if selection else None


def _unique_snap_points(items):
    result = []
    seen = set()
    for item in items:
        key = tuple(round(float(item["point"][axis]), 5) for axis in range(3))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _validate_input_path(path_text):
    if not path_text or not str(path_text).strip():
        return False, "DXF path is empty."
    path = Path(str(path_text).strip()).expanduser()
    if not path.is_absolute():
        return False, "DXF path must be absolute."
    if path.suffix.lower() != ".dxf":
        return False, "DXF path must end with .dxf."
    try:
        resolved = path.resolve()
    except OSError as exc:
        return False, f"DXF path could not be resolved: {exc}"
    if not resolved.exists():
        return False, f"DXF file does not exist: {resolved}"
    allowed_roots = [Path("C:/temp"), Path("C:/tmp")]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        allowed_roots.extend([Path(user_profile) / "Documents", Path(user_profile) / "Desktop"])
    allowed = [root.resolve() for root in allowed_roots]
    if not any(_is_relative_to(resolved, root) for root in allowed):
        return False, "DXF path is outside allowed folders: " + ", ".join(str(root) for root in allowed)
    return True, str(resolved)


def _is_relative_to(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _scaled_point(point, scale, z):
    point = _dxf_point(point)
    return Gf.Vec3f(float(point[0]) * scale, float(point[1]) * scale, z + float(point[2]) * scale)


def _dxf_point(point):
    return Gf.Vec3f(float(point[0]), float(point[1]), float(point[2]) if len(point) > 2 else 0.0)


def _coerce_point(value):
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace("(", "").replace(")", "").split(",")]
    else:
        parts = list(value or [])
    if len(parts) < 2:
        return None
    try:
        return Gf.Vec3f(float(parts[0]), float(parts[1]), float(parts[2]) if len(parts) > 2 else 0.0)
    except (TypeError, ValueError):
        return None


def _point_text(point):
    return f"({_fmt(point[0])}, {_fmt(point[1])}, {_fmt(point[2])})"


def _fmt(value):
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def _float(value, default=0.0):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _attr(prim, name, default=None):
    attr = prim.GetAttribute(name) if prim and prim.IsValid() else None
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default


def _safe_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(name or "DXFReference"))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"DXF_{cleaned or 'Reference'}"
    return cleaned
