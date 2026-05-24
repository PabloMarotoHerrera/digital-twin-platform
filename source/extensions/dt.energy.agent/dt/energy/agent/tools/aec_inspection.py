from __future__ import annotations

import omni.usd
from pxr import Gf, Usd, UsdGeom

from .results import tool_result
from .thermal_sync_tools import is_block_synced_to_thermalviz, thermalviz_sync_state, unsynced_block_reasons


ENERGY_ATTRS = ("aec:constructionName", "aec:uValue", "aec:thermalConductivity", "aec:density", "aec:specificHeat")


def analyze_scene() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    inventory = collect_aec_inventory(stage)
    warnings = []
    if not inventory["blocks"]:
        warnings.append("No hay bloques AEC. Crea un bloque parametrico antes de exportar energia.")
    if inventory["blocks"] and not inventory["spaces"]:
        warnings.append("Hay bloques, pero no se detectaron espacios bajo Spaces/Space_XX.")
    if inventory["surfaces"] and not inventory["surfaces_with_boundary"]:
        warnings.append("Hay superficies, pero ninguna tiene condicion de contorno energetica.")
    for block in inventory["blocks"]:
        reasons = unsynced_block_reasons(stage, block)
        if reasons:
            warnings.append(f"Bloque {block.GetPath()} no esta sincronizado con ThermalViz: {', '.join(reasons)}.")
    data = _summary_data(inventory)
    data["details"] = _world_details(inventory)
    return tool_result(True, "He analizado la escena. He encontrado:", data, warnings)


def list_aec_blocks() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    inventory = collect_aec_inventory(stage)
    details = []
    for block in inventory["blocks"]:
        details.append(f"{block.GetPath()} ({_attr(block, 'aec:blockKind', 'Unknown')}, {_dimensions_text(block)})")
    return tool_result(True, "Bloques AEC detectados:", {"block_count": len(inventory["blocks"]), "details": details})


def validate_aec_blocks() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    inventory = collect_aec_inventory(stage)
    warnings = []
    errors = []
    if not inventory["blocks"]:
        errors.append("No hay bloques AEC exportables.")
    for block in inventory["blocks"]:
        path = block.GetPath().pathString
        dimensions = block_dimensions(stage, block)
        footprint = _block_footprint_info(stage, block)
        if not dimensions["has_mass_mesh"]:
            errors.append(f"{path} no tiene Mass/PrimitiveMesh ni Mass/BlockMesh.")
        if not dimensions["valid"]:
            errors.append(f"{path} no tiene dimensiones validas ni atributos ni mesh de masa inferible.")
        elif dimensions["source"] == "mass_mesh":
            missing = ", ".join(dimensions["missing_attrs"])
            warnings.append(f"{path} no tiene {missing}; dimensiones inferidas desde el mesh de masa.")
        spaces = [space for space in inventory["spaces"] if _target_contains(space, "aec:block", block.GetPath())]
        if not spaces:
            errors.append(f"{path} no tiene espacios AEC generados.")
        block_surfaces = [surface for surface in inventory["surfaces"] if _is_descendant(surface, block)]
        if not block_surfaces:
            errors.append(f"{path} no tiene superficies exportables.")
        if footprint["kind"] == "Polygon":
            if footprint["wall_count"] != footprint["point_count"]:
                warnings.append(
                    f"{path} tiene footprint poligonal de {footprint['point_count']} puntos, "
                    f"pero {footprint['wall_count']} walls generadas."
                )
            if not footprint["floor_matches"] or not footprint["ceiling_matches"]:
                warnings.append(f"{path} tiene Floor/Ceiling que no parecen seguir la huella poligonal.")
        sync_state = thermalviz_sync_state(stage, block)
        if not sync_state["has_energy_metadata"]:
            errors.append(f"{path} no tiene metadata energetica minima.")
        if not sync_state["has_thermal_material"]:
            errors.append(f"{path} no tiene material termico asignado.")
        if not sync_state["thermalviz_registered"]:
            warnings.append(f"{path} no esta registrado en ThermalViz.")
        if not sync_state["has_spaces"]:
            errors.append(f"{path} no tiene Spaces AEC para ThermalViz.")
    for surface in inventory["surfaces"]:
        if _attr(surface, "aec:outsideBoundaryCondition", None) is None and _attr(surface, "aec:thermalBoundary", None) is None:
            warnings.append(f"{surface.GetPath()} no tiene boundary condition energetica.")
    if inventory["surfaces"] and not inventory["thermal_materials"]:
        warnings.append("No se detectaron materiales termicos completos; el IDF sera placeholder.")
    data = _summary_data(inventory)
    data["idf_exportable"] = "yes (placeholder)" if inventory["blocks"] and inventory["surfaces"] and not errors else "no"
    return tool_result(not errors, "Validacion energetica:", data, warnings, errors)


def get_selected_aec_element() -> dict:
    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    selected = list(context.get_selection().get_selected_prim_paths())
    details = []
    for path in selected:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            details.append(f"{path}: aec:type={_attr(prim, 'aec:type', 'none')}")
    return tool_result(True, "Seleccion actual:", {"selected": selected, "details": details})


def inspect_surface_geometry(surface_path: str | None = None) -> dict:
    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    path = surface_path or (context.get_selection().get_selected_prim_paths() or [None])[0]
    if not path:
        return tool_result(False, "No hay ninguna superficie seleccionada.", errors=["Select or provide a Mesh surface path."])
    prim = stage.GetPrimAtPath(path)
    if not prim or not prim.IsValid() or not prim.IsA(UsdGeom.Mesh):
        return tool_result(False, "El prim indicado no es una superficie Mesh.", errors=[f"Not a UsdGeom.Mesh: {path}"])
    mesh = UsdGeom.Mesh(prim)
    points = [point for point in mesh.GetPointsAttr().Get() or []]
    counts = [int(value) for value in mesh.GetFaceVertexCountsAttr().Get() or []]
    indices = [int(value) for value in mesh.GetFaceVertexIndicesAttr().Get() or []]
    bbox = _points_bbox(points)
    normal = _approx_normal(points, indices[:3] if len(indices) >= 3 else [])
    source_block = _ancestor_block(stage, prim)
    footprint = _block_footprint_info(stage, source_block) if source_block else None
    expected = footprint["point_count"] if footprint else 0
    return tool_result(
        True,
        "Geometria de superficie:",
        {
            "surface_path": prim.GetPath().pathString,
            "vertex_count": len(points),
            "face_vertex_counts": counts,
            "face_vertex_indices": indices,
            "bbox": bbox,
            "approx_normal": normal,
            "surface_kind": "Polygonal triangulated" if len(counts) > 1 else ("Polygonal n-gon" if counts and counts[0] > 4 else "Quad/Triangle"),
            "matches_footprint": bool(expected and len(points) == expected) if _attr(prim, "aec:surfaceType", "") in ("Floor", "Ceiling") else None,
            "details": [
                f"aec:surfaceType={_attr(prim, 'aec:surfaceType', 'none')}",
                f"footprint esperado={expected or 'unknown'}",
            ],
        },
    )


def collect_aec_inventory(stage) -> dict:
    world = stage.GetPrimAtPath("/World")
    world_children = [child.GetPath().pathString for child in world.GetChildren()] if world and world.IsValid() else []
    blocks = []
    spaces = []
    surfaces = []
    meshes = []
    thermal_materials = []
    for prim in stage.Traverse():
        aec_type = _attr(prim, "aec:type", "")
        if aec_type == "Block":
            blocks.append(prim)
        elif aec_type == "Space":
            spaces.append(prim)
        elif aec_type == "Surface":
            surfaces.append(prim)
        if prim.IsA(UsdGeom.Mesh):
            meshes.append(prim)
        if all(_attr(prim, name, None) is not None for name in ENERGY_ATTRS):
            thermal_materials.append(prim)
    selected = list(omni.usd.get_context().get_selection().get_selected_prim_paths())
    return {
        "world_children": world_children,
        "blocks": blocks,
        "spaces": spaces,
        "surfaces": surfaces,
        "meshes": meshes,
        "surfaces_with_boundary": [s for s in surfaces if _attr(s, "aec:outsideBoundaryCondition", None) is not None or _attr(s, "aec:thermalBoundary", None) is not None],
        "thermal_materials": thermal_materials,
        "selected": selected,
        "thermalviz_synced_blocks": [block for block in blocks if is_block_synced_to_thermalviz(stage, block)],
        "thermalviz_unsynced_blocks": [block for block in blocks if not is_block_synced_to_thermalviz(stage, block)],
    }


def _summary_data(inventory: dict) -> dict:
    return {
        "block_count": len(inventory["blocks"]),
        "space_count": len(inventory["spaces"]),
        "surface_count": len(inventory["surfaces"]),
        "exportable_surface_count": len(inventory["surfaces_with_boundary"]),
        "thermal_material_count": len(inventory["thermal_materials"]),
        "thermalviz_synced_block_count": len(inventory.get("thermalviz_synced_blocks", [])),
        "thermalviz_unsynced_block_count": len(inventory.get("thermalviz_unsynced_blocks", [])),
        "selected": inventory["selected"],
    }


def _world_details(inventory: dict) -> list[str]:
    details = [f"/World children: {', '.join(inventory['world_children']) or 'none'}"]
    for block in inventory["blocks"]:
        footprint = _block_footprint_info(block.GetStage(), block)
        details.append(
            f"Block: {block.GetPath()} ({_dimensions_text(block)}, "
            f"footprint={footprint['kind']}, rebuild={footprint['rebuild_mode']}, walls={footprint['wall_count']})"
        )
    return details


def _dimensions_text(block) -> str:
    dimensions = block_dimensions(block.GetStage(), block)
    if dimensions["valid"]:
        suffix = "" if dimensions["source"] == "attrs" else " inferred"
        return f"{_fmt(dimensions['width'])} x {_fmt(dimensions['depth'])} x {_fmt(dimensions['height'])} m{suffix}"
    return "? x ? x ? m"


def block_dimensions(stage, block) -> dict:
    width = _positive_or_none(_attr(block, "aec:width", None))
    depth = _positive_or_none(_attr(block, "aec:depth", None))
    height = _positive_or_none(_attr(block, "aec:height", None))
    missing = []
    if width is None:
        missing.append("aec:width")
    if depth is None:
        missing.append("aec:depth")
    if height is None:
        missing.append("aec:height")
    if width is not None and depth is not None and height is not None:
        return {
            "valid": True,
            "source": "attrs",
            "width": width,
            "depth": depth,
            "height": height,
            "missing_attrs": [],
            "has_mass_mesh": _has_mass_mesh(stage, block),
        }

    mesh_dimensions = _mass_mesh_dimensions(stage, block)
    if mesh_dimensions is None:
        return {
            "valid": False,
            "source": "none",
            "width": width,
            "depth": depth,
            "height": height,
            "missing_attrs": missing,
            "has_mass_mesh": False,
        }

    return {
        "valid": True,
        "source": "mass_mesh",
        "width": width if width is not None else mesh_dimensions["width"],
        "depth": depth if depth is not None else mesh_dimensions["depth"],
        "height": height if height is not None else mesh_dimensions["height"],
        "missing_attrs": missing,
        "has_mass_mesh": True,
    }


def _mass_mesh_dimensions(stage, block) -> dict | None:
    mesh_prim = _mass_mesh(stage, block)
    if mesh_prim is None:
        return None
    points = UsdGeom.Mesh(mesh_prim).GetPointsAttr().Get() or []
    if not points:
        return None
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    zs = [float(point[2]) for point in points]
    width = max(xs) - min(xs)
    depth = max(ys) - min(ys)
    height = max(zs) - min(zs)
    if width <= 0.0 or depth <= 0.0 or height <= 0.0:
        return None
    return {"width": width, "depth": depth, "height": height}


def _mass_mesh(stage, block):
    for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
        prim = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
        if prim and prim.IsValid() and prim.IsA(UsdGeom.Mesh):
            return prim
    return None


def _positive_or_none(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0.0 else None


def _fmt(value) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def _has_mass_mesh(stage, block) -> bool:
    return _mass_mesh(stage, block) is not None


def _block_footprint_info(stage, block) -> dict:
    point_count = _positive_or_none(_attr(block, "aec:footprintPointCount", None))
    kind = _attr(block, "aec:footprintKind", None)
    rebuild_mode = _attr(block, "aec:rebuildMode", "unknown")
    source_curve = _source_curve(stage, block)
    if source_curve is not None:
        points = _curve_points(source_curve)
        if points:
            point_count = len(points)
            kind = kind or ("Rectangle" if len(points) == 4 else "Polygon")
    kind = kind or _kind_from_mass(stage, block)
    wall_count = len(_block_surfaces(stage, block, "Wall"))
    floor = _first_surface(stage, block, "Floor")
    ceiling = _first_surface(stage, block, "Ceiling")
    expected = int(point_count or 0)
    return {
        "kind": kind or "Unknown",
        "rebuild_mode": rebuild_mode,
        "point_count": expected,
        "wall_count": wall_count,
        "floor_matches": _surface_vertex_count(floor) == expected if expected and floor else True,
        "ceiling_matches": _surface_vertex_count(ceiling) == expected if expected and ceiling else True,
    }


def _source_curve(stage, block):
    rel = block.GetRelationship("aec:sourceCurveRel")
    for target in rel.GetTargets() if rel else []:
        prim = stage.GetPrimAtPath(target)
        if prim and prim.IsValid() and prim.IsA(UsdGeom.BasisCurves):
            return prim
    return None


def _curve_points(curve_prim):
    curve = UsdGeom.BasisCurves(curve_prim)
    points = list(curve.GetPointsAttr().Get() or [])
    counts = curve.GetCurveVertexCountsAttr().Get() or []
    count = int(counts[0]) if counts else len(points)
    result = points[:count]
    if len(result) >= 4 and _distance(result[0], result[-1]) <= 1e-5:
        result = result[:-1]
    return result


def _kind_from_mass(stage, block):
    mesh = _mass_mesh(stage, block)
    if mesh is None:
        return "Unknown"
    counts = list(UsdGeom.Mesh(mesh).GetFaceVertexCountsAttr().Get() or [])
    cap_counts = [count for count in counts if int(count) > 4]
    if cap_counts:
        return "Polygon"
    return "Rectangle" if counts else "Unknown"


def _block_surfaces(stage, block, surface_type):
    return [
        prim
        for prim in Usd.PrimRange(block)
        if _attr(prim, "aec:type", "") == "Surface" and _attr(prim, "aec:surfaceType", "") == surface_type
    ]


def _first_surface(stage, block, surface_type):
    surfaces = _block_surfaces(stage, block, surface_type)
    return surfaces[0] if surfaces else None


def _surface_vertex_count(surface):
    if not surface or not surface.IsValid() or not surface.IsA(UsdGeom.Mesh):
        return 0
    return len(UsdGeom.Mesh(surface).GetPointsAttr().Get() or [])


def _distance(left, right):
    return sum((float(left[index]) - float(right[index])) ** 2 for index in range(3)) ** 0.5


def _points_bbox(points):
    if not points:
        return "empty"
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    zs = [float(point[2]) for point in points]
    return f"min=({_fmt(min(xs))}, {_fmt(min(ys))}, {_fmt(min(zs))}), max=({_fmt(max(xs))}, {_fmt(max(ys))}, {_fmt(max(zs))})"


def _approx_normal(points, indices):
    if len(indices) < 3 or len(points) < 3:
        return "unknown"
    a = points[indices[0]]
    b = points[indices[1]]
    c = points[indices[2]]
    normal = Gf.Cross(b - a, c - a)
    if normal.GetLength() <= 1e-8:
        return "unknown"
    normal.Normalize()
    return f"({_fmt(normal[0])}, {_fmt(normal[1])}, {_fmt(normal[2])})"


def _ancestor_block(stage, prim):
    current = prim
    while current and current.IsValid():
        if _attr(current, "aec:type", "") == "Block":
            return current
        parent = current.GetParent()
        if not parent or parent == current:
            return None
        current = parent
    return None



def _target_contains(prim, rel_name: str, target) -> bool:
    rel = prim.GetRelationship(rel_name)
    return bool(rel and target in rel.GetTargets())


def _is_descendant(prim, ancestor) -> bool:
    return prim.GetPath().HasPrefix(ancestor.GetPath())


def _attr(prim, name: str, default=None):
    attr = prim.GetAttribute(name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default
