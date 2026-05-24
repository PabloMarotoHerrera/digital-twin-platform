from __future__ import annotations

import carb
from custom_aec.extrude.mesh_builder import extrude_closed_curve_to_mesh
from pxr import Gf, Sdf, Usd, UsdGeom

from .partition_specs import ensure_aec_container
from .rebuild import rebuild_block


def rebuild_block_for_footprint(stage, block_path, rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True):
    block = stage.GetPrimAtPath(block_path)
    if not block or not block.IsValid():
        raise ValueError(f"Block does not exist: {block_path}")

    curve_prim = _source_curve_prim(stage, block)
    if curve_prim is None:
        carb.log_warn(
            f"[AEC Modelling] {block.GetPath()} has no valid aec:sourceCurveRel; "
            "using rectangular rebuild only if mass bounds are available."
        )
        rebuilt = rebuild_block(
            stage,
            block.GetPath(),
            rebuild_partitions=rebuild_partitions,
            rebuild_spaces=rebuild_spaces,
            rebuild_surfaces=rebuild_surfaces,
        )
        return {"block": rebuilt, "mode": "rectangular", "warnings": ["No valid source curve; used legacy rebuild."]}

    footprint = footprint_from_curve(curve_prim)
    if not footprint["valid"]:
        raise ValueError(footprint["error"])

    if footprint["kind"] == "Rectangle":
        rebuilt = rebuild_block(
            stage,
            block.GetPath(),
            rebuild_partitions=rebuild_partitions,
            rebuild_spaces=rebuild_spaces,
            rebuild_surfaces=rebuild_surfaces,
        )
        rebuilt.CreateAttribute("aec:rebuildMode", Sdf.ValueTypeNames.String).Set("rectangular")
        return {"block": rebuilt, "mode": "rectangular", "warnings": []}

    rebuilt = rebuild_block_polygon_aware(stage, block.GetPath(), curve_prim=curve_prim, footprint=footprint)
    return {
        "block": rebuilt,
        "mode": "polygon-aware",
        "warnings": ["Partitions/Openings polygon-aware todavia limitado."],
    }


def rebuild_block_polygon_aware(stage, block_path, curve_prim=None, footprint=None):
    block = stage.GetPrimAtPath(block_path)
    if not block or not block.IsValid():
        raise ValueError(f"Block does not exist: {block_path}")

    curve_prim = curve_prim or _source_curve_prim(stage, block)
    if curve_prim is None:
        raise ValueError(f"{block.GetPath()} has no valid aec:sourceCurveRel.")
    footprint = footprint or footprint_from_curve(curve_prim)
    if not footprint["valid"] or footprint["kind"] == "Rectangle":
        raise ValueError(f"Polygon-aware rebuild requires a closed non-rectangular footprint: {footprint.get('error', '')}")

    height = _block_height(stage, block)
    metadata = _capture_preserved_metadata(stage, block)
    _remove_rebuild_targets(stage, block)
    rebuilt = extrude_closed_curve_to_mesh(stage, curve_prim, block.GetPath().pathString, height)
    _restore_preserved_metadata(stage, rebuilt, metadata)
    _ensure_basic_energy_metadata(rebuilt)
    ensure_aec_container(stage, rebuilt.GetPath())
    _mark_polygon_rebuild(stage, rebuilt, footprint, height)
    carb.log_info(
        "[AEC Modelling] rebuild_block_polygon_aware "
        f"block={rebuilt.GetPath()} points={len(footprint['points'])} height={height}"
    )
    return rebuilt


def footprint_from_curve(curve_prim):
    if not curve_prim or not curve_prim.IsValid() or not curve_prim.IsA(UsdGeom.BasisCurves):
        return {"valid": False, "error": "Source sketch is not a UsdGeom.BasisCurves prim."}
    curve = UsdGeom.BasisCurves(curve_prim)
    if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
        return {"valid": False, "error": "Source sketch is open; wrap must be periodic."}

    points = list(curve.GetPointsAttr().Get() or [])
    counts = curve.GetCurveVertexCountsAttr().Get() or []
    count = int(counts[0]) if counts else len(points)
    if count < 3 or len(points) < count:
        return {"valid": False, "error": "Source sketch needs at least 3 readable points."}

    local_to_world = UsdGeom.Xformable(curve_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    world_points = [Gf.Vec3f(local_to_world.Transform(Gf.Vec3d(points[index]))) for index in range(count)]
    if len(world_points) >= 4 and _same_point(world_points[0], world_points[-1]):
        world_points = world_points[:-1]
    if len(world_points) < 3:
        return {"valid": False, "error": "Source sketch footprint collapses below 3 points."}
    if not _is_horizontal(world_points):
        return {"valid": False, "error": "Source sketch is not horizontal."}

    return {
        "valid": True,
        "kind": "Rectangle" if _is_rectangle(world_points) else "Polygon",
        "points": world_points,
        "segments": [(world_points[index], world_points[(index + 1) % len(world_points)]) for index in range(len(world_points))],
    }


def _source_curve_prim(stage, block):
    rel = block.GetRelationship("aec:sourceCurveRel")
    for target in rel.GetTargets() if rel else []:
        prim = stage.GetPrimAtPath(target)
        if prim and prim.IsValid() and prim.IsA(UsdGeom.BasisCurves):
            return prim
    attr = block.GetAttribute("aec:sourceCurve")
    source_path = attr.Get() if attr and attr.HasAuthoredValueOpinion() else None
    if source_path:
        prim = stage.GetPrimAtPath(source_path)
        if prim and prim.IsValid() and prim.IsA(UsdGeom.BasisCurves):
            return prim
    return None


def _remove_rebuild_targets(stage, block):
    for child_name in ("Mass", "Spaces"):
        path = block.GetPath().AppendChild(child_name)
        if stage.GetPrimAtPath(path).IsValid():
            stage.RemovePrim(path)

    partitions = stage.GetPrimAtPath(block.GetPath().AppendChild("Partitions"))
    if partitions and partitions.IsValid():
        for child in list(partitions.GetChildren()):
            if _attr(child, "aec:type", "") == "Partition":
                stage.RemovePrim(child.GetPath())


def _mark_polygon_rebuild(stage, block, footprint, height):
    block.CreateAttribute("aec:rebuildMode", Sdf.ValueTypeNames.String).Set("polygon-aware")
    block.CreateAttribute("aec:footprintKind", Sdf.ValueTypeNames.String).Set("Polygon")
    block.CreateAttribute("aec:footprintPointCount", Sdf.ValueTypeNames.Int).Set(len(footprint["points"]))
    block.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))

    space = stage.GetPrimAtPath(block.GetPath().AppendPath("Spaces/Space_01"))
    if space and space.IsValid():
        space.CreateAttribute("aec:generatedFromPolygonFootprint", Sdf.ValueTypeNames.Bool).Set(True)
        space.CreateRelationship("aec:block").SetTargets([block.GetPath()])

    surfaces_root = stage.GetPrimAtPath(block.GetPath().AppendPath("Spaces/Space_01/Surfaces"))
    if not surfaces_root or not surfaces_root.IsValid():
        return

    for surface in surfaces_root.GetChildren():
        surface_type = _attr(surface, "aec:surfaceType", "")
        if surface_type == "Floor":
            boundary = "Ground"
        elif surface_type in ("Ceiling", "Wall"):
            boundary = "Outdoors"
        else:
            boundary = "Unknown"
        surface.CreateAttribute("aec:outsideBoundaryCondition", Sdf.ValueTypeNames.String).Set(boundary)
        surface.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set(
            "Exterior" if boundary in ("Ground", "Outdoors") else "Unknown"
        )
        points = UsdGeom.Mesh(surface).GetPointsAttr().Get() or []
        if points:
            _author_surface_basis(surface, [Gf.Vec3f(point) for point in points])


def _author_surface_basis(surface, points):
    if len(points) < 3:
        return
    origin = Gf.Vec3f(points[0])
    h_vec = Gf.Vec3f(points[1]) - origin
    v_vec = Gf.Vec3f(points[-1]) - origin
    if h_vec.GetLength() <= 1e-6 or v_vec.GetLength() <= 1e-6:
        return
    h_dir = h_vec.GetNormalized()
    v_dir = v_vec.GetNormalized()
    normal = Gf.Cross(h_dir, v_dir)
    if normal.GetLength() > 0.0:
        normal.Normalize()
    surface.CreateAttribute("aec:basisOrigin", Sdf.ValueTypeNames.Float3).Set(origin)
    surface.CreateAttribute("aec:basisHDir", Sdf.ValueTypeNames.Float3).Set(h_dir)
    surface.CreateAttribute("aec:basisVDir", Sdf.ValueTypeNames.Float3).Set(v_dir)
    surface.CreateAttribute("aec:basisNormal", Sdf.ValueTypeNames.Float3).Set(normal)
    surface.CreateAttribute("aec:basisWidth", Sdf.ValueTypeNames.Float).Set(float(h_vec.GetLength()))
    surface.CreateAttribute("aec:basisHeight", Sdf.ValueTypeNames.Float).Set(float(v_vec.GetLength()))


def _block_height(stage, block):
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


def _capture_preserved_metadata(stage, block):
    return {
        "block": _capture_attrs(block),
        "metadata": _capture_attrs(stage.GetPrimAtPath(block.GetPath().AppendChild("Metadata"))),
    }


def _capture_attrs(prim):
    if not prim or not prim.IsValid():
        return {}
    values = {}
    for attr in prim.GetAttributes():
        name = attr.GetName()
        if not _preserve_attr(name) or not attr.HasAuthoredValueOpinion():
            continue
        values[name] = (attr.GetTypeName(), attr.Get())
    return values


def _restore_preserved_metadata(stage, block, metadata):
    _restore_attrs(block, metadata.get("block") or {})
    metadata_prim = UsdGeom.Xform.Define(stage, block.GetPath().AppendChild("Metadata")).GetPrim()
    metadata_prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Metadata")
    _restore_attrs(metadata_prim, metadata.get("metadata") or {})


def _restore_attrs(prim, values):
    for name, (type_name, value) in values.items():
        prim.CreateAttribute(name, type_name).Set(value)


def _ensure_basic_energy_metadata(block):
    if _attr(block, "aec:energyModel", None) is None:
        block.CreateAttribute("aec:energyModel", Sdf.ValueTypeNames.Bool).Set(True)
    if _attr(block, "aec:constructionName", None) is None:
        block.CreateAttribute("aec:constructionName", Sdf.ValueTypeNames.String).Set("Generic Lightweight Construction")
    if _attr(block, "aec:uValue", None) is None:
        block.CreateAttribute("aec:uValue", Sdf.ValueTypeNames.Float).Set(0.35)
    block.CreateAttribute("aec:exportableToIdf", Sdf.ValueTypeNames.Bool).Set(True)


def _preserve_attr(name):
    lower = name.lower()
    return (
        lower.startswith("dt:")
        or lower.startswith("energy:")
        or lower.startswith("thermal:")
        or lower.startswith("aec:energy")
        or lower.startswith("aec:thermal")
        or lower in {"aec:constructionname", "aec:uvalue", "aec:exportabletoidf"}
    )


def _is_rectangle(points):
    if len(points) != 4 or not _is_horizontal(points):
        return False
    edges = [points[(index + 1) % 4] - points[index] for index in range(4)]
    lengths = [edge.GetLength() for edge in edges]
    if any(length <= 1e-5 for length in lengths):
        return False
    return (
        abs(_dot(_normalized(edges[0]), _normalized(edges[1]))) <= 1e-4
        and abs(_dot(_normalized(edges[1]), _normalized(edges[2]))) <= 1e-4
        and abs(lengths[0] - lengths[2]) <= 1e-4
        and abs(lengths[1] - lengths[3]) <= 1e-4
    )


def _is_horizontal(points):
    if not points:
        return False
    z0 = float(points[0][2])
    return all(abs(float(point[2]) - z0) <= 1e-5 for point in points)


def _same_point(left, right):
    return (Gf.Vec3f(left) - Gf.Vec3f(right)).GetLength() <= 1e-5


def _normalized(vector):
    length = vector.GetLength()
    if length <= 1e-8:
        return Gf.Vec3f(0.0, 0.0, 0.0)
    return Gf.Vec3f(float(vector[0]) / length, float(vector[1]) / length, float(vector[2]) / length)


def _dot(left, right):
    return float(left[0]) * float(right[0]) + float(left[1]) * float(right[1]) + float(left[2]) * float(right[2])


def _attr(prim, name, default=None):
    attr = prim.GetAttribute(name) if prim and prim.IsValid() else None
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default
