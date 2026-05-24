import carb
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .opening_specs import create_opening_spec, read_opening_specs, update_opening_spec
from .partition_specs import ensure_aec_container, read_partition_specs


def rebuild_block(stage, block_path, rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True):
    block = stage.GetPrimAtPath(block_path)
    if not block or not block.IsValid():
        raise ValueError(f"Block does not exist: {block_path}")

    ensure_aec_container(stage, block.GetPath())
    bounds = block_local_bounds(stage, block)
    if rebuild_partitions:
        _remove_deleted_partition_specs(stage, block)
        _capture_existing_partitions_as_specs(stage, block, bounds)
    specs = read_partition_specs(stage, block)

    if rebuild_partitions:
        _rebuild_partitions(stage, block, bounds, specs)
    if rebuild_spaces:
        _capture_existing_openings_as_specs(stage, block)
        _rebuild_spaces(stage, block, bounds, specs)
        _rebuild_openings(stage, block)

    carb.log_info(
        "[AEC Modelling] rebuild_block "
        f"block={block.GetPath()} partitionSpecs={len(specs)} "
        f"partitions={rebuild_partitions} spaces={rebuild_spaces} surfaces={rebuild_surfaces}"
    )
    return block


def block_local_bounds(stage, block):
    mesh = None
    for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
        candidate = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
        if candidate and candidate.IsValid() and candidate.IsA(UsdGeom.Mesh):
            mesh = candidate
            break
    if mesh is None:
        raise ValueError(f"Block has no mass mesh: {block.GetPath()}")

    points = UsdGeom.Mesh(mesh).GetPointsAttr().Get() or []
    if not points:
        raise ValueError(f"Block mass mesh has no points: {mesh.GetPath()}")

    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    zs = [float(point[2]) for point in points]
    return {
        "min": Gf.Vec3f(min(xs), min(ys), min(zs)),
        "max": Gf.Vec3f(max(xs), max(ys), max(zs)),
    }


def _rebuild_partitions(stage, block, bounds, specs):
    partitions_path = block.GetPath().AppendPath("Partitions")
    partitions = UsdGeom.Xform.Define(stage, partitions_path).GetPrim()
    partitions.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Partitions")
    _remove_generated_children(stage, partitions, "Partition")

    for index, spec in enumerate(specs, start=1):
        partition_path = partitions_path.AppendPath(f"Partition_{index:02d}")
        partition = _define_partition_mesh(stage, partition_path, bounds, spec)
        partition.CreateRelationship("aec:spec").SetTargets([spec["path"]])
        partition.CreateRelationship("aec:block").SetTargets([block.GetPath()])
        spec["prim"].CreateAttribute("aec:partitionPrimPath", Sdf.ValueTypeNames.String).Set(partition_path.pathString)


def _define_partition_mesh(stage, path, bounds, spec):
    min_p = bounds["min"]
    max_p = bounds["max"]
    block_height = max(float(max_p[2] - min_p[2]), 0.001)
    height = block_height
    z0 = float(min_p[2])
    z1 = z0 + height
    orientation = spec["orientation"]
    offset = _clamp(spec["offset_normalized"], 0.0, 1.0)

    if orientation == "Across Y":
        x = _lerp(float(min_p[0]), float(max_p[0]), offset)
        points = [
            Gf.Vec3f(x, min_p[1], z0),
            Gf.Vec3f(x, max_p[1], z0),
            Gf.Vec3f(x, max_p[1], z1),
            Gf.Vec3f(x, min_p[1], z1),
        ]
        normal = Gf.Vec3f(1.0, 0.0, 0.0)
    else:
        y = _lerp(float(min_p[1]), float(max_p[1]), offset)
        points = [
            Gf.Vec3f(min_p[0], y, z0),
            Gf.Vec3f(max_p[0], y, z0),
            Gf.Vec3f(max_p[0], y, z1),
            Gf.Vec3f(min_p[0], y, z1),
        ]
        normal = Gf.Vec3f(0.0, -1.0, 0.0)

    mesh = _define_quad_mesh(stage, path, points, normal)
    prim = mesh.GetPrim()
    prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Partition")
    prim.CreateAttribute("aec:generatedFromSpec", Sdf.ValueTypeNames.Bool).Set(True)
    prim.CreateAttribute("aec:specId", Sdf.ValueTypeNames.String).Set(spec["spec_id"])
    prim.CreateAttribute("aec:orientation", Sdf.ValueTypeNames.String).Set(orientation)
    prim.CreateAttribute("aec:offsetNormalized", Sdf.ValueTypeNames.Float).Set(float(offset))
    prim.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))
    prim.CreateAttribute("aec:thickness", Sdf.ValueTypeNames.Float).Set(float(spec["thickness"]))
    prim.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set("Interior")
    _set_display_color(prim, Gf.Vec3f(0.70, 0.62, 0.35))
    return prim


def _rebuild_spaces(stage, block, bounds, specs):
    spaces_path = block.GetPath().AppendPath("Spaces")
    spaces = UsdGeom.Xform.Define(stage, spaces_path).GetPrim()
    spaces.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Spaces")

    x_cuts = [0.0, 1.0]
    y_cuts = [0.0, 1.0]
    for spec in specs:
        offset = _clamp(spec["offset_normalized"], 0.0, 1.0)
        if spec["orientation"] == "Across Y":
            x_cuts.append(offset)
        else:
            y_cuts.append(offset)

    x_cuts = _unique_sorted(x_cuts)
    y_cuts = _unique_sorted(y_cuts)
    cells = []
    for y_index in range(len(y_cuts) - 1):
        for x_index in range(len(x_cuts) - 1):
            min_norm = Gf.Vec2f(x_cuts[x_index], y_cuts[y_index])
            max_norm = Gf.Vec2f(x_cuts[x_index + 1], y_cuts[y_index + 1])
            cells.append(
                {
                    "x_index": x_index,
                    "y_index": y_index,
                    "min_norm": min_norm,
                    "max_norm": max_norm,
                }
            )

    _remove_existing_spaces(stage, spaces)
    opening_specs = read_opening_specs(stage, block)
    surface_index = {}
    for index, cell in enumerate(cells, start=1):
        min_norm = cell["min_norm"]
        max_norm = cell["max_norm"]
        space_path = spaces_path.AppendPath(f"Space_{index:02d}")
        space = UsdGeom.Xform.Define(stage, space_path).GetPrim()
        space.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Space")
        space.CreateAttribute("aec:name", Sdf.ValueTypeNames.String).Set(f"Space_{index:02d}")
        space.CreateAttribute("aec:generatedFromPartitions", Sdf.ValueTypeNames.Bool).Set(True)
        space.CreateAttribute("aec:gridX", Sdf.ValueTypeNames.Int).Set(int(cell["x_index"]))
        space.CreateAttribute("aec:gridY", Sdf.ValueTypeNames.Int).Set(int(cell["y_index"]))
        space.CreateAttribute("aec:boundsMin", Sdf.ValueTypeNames.Float3).Set(
            _point_from_normalized(bounds, min_norm, low_z=True)
        )
        space.CreateAttribute("aec:boundsMax", Sdf.ValueTypeNames.Float3).Set(
            _point_from_normalized(bounds, max_norm, low_z=False)
        )
        space.CreateAttribute("aec:partitionGridMin", Sdf.ValueTypeNames.Float2).Set(min_norm)
        space.CreateAttribute("aec:partitionGridMax", Sdf.ValueTypeNames.Float2).Set(max_norm)
        space.CreateRelationship("aec:block").SetTargets([block.GetPath()])
        _define_space_surfaces(
            stage,
            space,
            bounds,
            cell,
            len(x_cuts) - 1,
            len(y_cuts) - 1,
            surface_index,
            opening_specs,
        )

    _link_adjacent_surfaces(stage, surface_index)


def _remove_generated_children(stage, parent, aec_type):
    for child in list(parent.GetChildren()):
        if _attr_value(child, "aec:type", "") != aec_type:
            continue
        if _attr_value(child, "aec:generatedFromSpec", False) is True:
            stage.RemovePrim(child.GetPath())


def _remove_existing_spaces(stage, spaces):
    for child in list(spaces.GetChildren()):
        if child.GetName().startswith("Space_"):
            stage.RemovePrim(child.GetPath())


def _define_space_surfaces(stage, space, bounds, cell, x_count, y_count, surface_index, opening_specs):
    surfaces_path = space.GetPath().AppendPath("Surfaces")
    surfaces = UsdGeom.Xform.Define(stage, surfaces_path).GetPrim()
    surfaces.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Surfaces")

    min_p = _point_from_normalized(bounds, cell["min_norm"], low_z=True)
    max_p = _point_from_normalized(bounds, cell["max_norm"], low_z=False)
    x0, y0, z0 = float(min_p[0]), float(min_p[1]), float(min_p[2])
    x1, y1, z1 = float(max_p[0]), float(max_p[1]), float(max_p[2])
    x_index = cell["x_index"]
    y_index = cell["y_index"]

    surface_defs = [
        {
            "name": "Floor",
            "type": "Floor",
            "normal": Gf.Vec3f(0.0, 0.0, -1.0),
            "points": [
                Gf.Vec3f(x0, y1, z0),
                Gf.Vec3f(x1, y1, z0),
                Gf.Vec3f(x1, y0, z0),
                Gf.Vec3f(x0, y0, z0),
            ],
            "boundary": "Ground",
            "key": None,
        },
        {
            "name": "Ceiling",
            "type": "Ceiling",
            "normal": Gf.Vec3f(0.0, 0.0, 1.0),
            "points": [
                Gf.Vec3f(x0, y0, z1),
                Gf.Vec3f(x1, y0, z1),
                Gf.Vec3f(x1, y1, z1),
                Gf.Vec3f(x0, y1, z1),
            ],
            "boundary": "Outdoors",
            "key": None,
        },
        {
            "name": "Wall_XMin",
            "type": "Wall",
            "normal": Gf.Vec3f(-1.0, 0.0, 0.0),
            "points": [
                Gf.Vec3f(x0, y0, z0),
                Gf.Vec3f(x0, y1, z0),
                Gf.Vec3f(x0, y1, z1),
                Gf.Vec3f(x0, y0, z1),
            ],
            "boundary": "Surface" if x_index > 0 else "Outdoors",
            "key": ("x", x_index, y_index),
        },
        {
            "name": "Wall_XMax",
            "type": "Wall",
            "normal": Gf.Vec3f(1.0, 0.0, 0.0),
            "points": [
                Gf.Vec3f(x1, y1, z0),
                Gf.Vec3f(x1, y0, z0),
                Gf.Vec3f(x1, y0, z1),
                Gf.Vec3f(x1, y1, z1),
            ],
            "boundary": "Surface" if x_index < x_count - 1 else "Outdoors",
            "key": ("x", x_index + 1, y_index),
        },
        {
            "name": "Wall_YMin",
            "type": "Wall",
            "normal": Gf.Vec3f(0.0, -1.0, 0.0),
            "points": [
                Gf.Vec3f(x1, y0, z0),
                Gf.Vec3f(x0, y0, z0),
                Gf.Vec3f(x0, y0, z1),
                Gf.Vec3f(x1, y0, z1),
            ],
            "boundary": "Surface" if y_index > 0 else "Outdoors",
            "key": ("y", x_index, y_index),
        },
        {
            "name": "Wall_YMax",
            "type": "Wall",
            "normal": Gf.Vec3f(0.0, 1.0, 0.0),
            "points": [
                Gf.Vec3f(x0, y1, z0),
                Gf.Vec3f(x1, y1, z0),
                Gf.Vec3f(x1, y1, z1),
                Gf.Vec3f(x0, y1, z1),
            ],
            "boundary": "Surface" if y_index < y_count - 1 else "Outdoors",
            "key": ("y", x_index, y_index + 1),
        },
    ]

    for surface_def in surface_defs:
        surface_path = surfaces_path.AppendPath(surface_def["name"])
        surface_openings = [
            spec for spec in opening_specs
            if spec["host_surface"] == surface_path and surface_def["type"] == "Wall"
        ]
        if surface_openings:
            mesh = _define_wall_mesh_with_openings(
                stage,
                surface_path,
                surface_def["points"],
                surface_def["normal"],
                surface_openings,
            )
        else:
            mesh = _define_quad_mesh(stage, surface_path, surface_def["points"], surface_def["normal"])
        surface = mesh.GetPrim()
        surface.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Surface")
        surface.CreateAttribute("aec:surfaceType", Sdf.ValueTypeNames.String).Set(surface_def["type"])
        surface.CreateAttribute("aec:outsideBoundaryCondition", Sdf.ValueTypeNames.String).Set(surface_def["boundary"])
        surface.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set(
            "Interior" if surface_def["boundary"] == "Surface" else "Exterior"
        )
        if surface_def["boundary"] == "Surface" and surface_def["type"] == "Wall":
            surface.CreateAttribute("aec:hiddenByPartition", Sdf.ValueTypeNames.Bool).Set(True)
            UsdGeom.Imageable(surface).MakeInvisible()
        _author_surface_basis(surface, surface_def["points"], surface_def["normal"])
        surface.CreateRelationship("aec:space").SetTargets([space.GetPath()])
        _set_display_color(surface, _surface_color(surface_def["type"], surface_def["boundary"]))
        if surface_def["key"] is not None and surface_def["boundary"] == "Surface":
            surface_index.setdefault(surface_def["key"], []).append(surface)


def _link_adjacent_surfaces(stage, surface_index):
    for surfaces in surface_index.values():
        if len(surfaces) != 2:
            continue
        first, second = surfaces
        first.CreateRelationship("aec:adjacentSurface").SetTargets([second.GetPath()])
        second.CreateRelationship("aec:adjacentSurface").SetTargets([first.GetPath()])
        first_space = first.GetRelationship("aec:space").GetTargets()
        second_space = second.GetRelationship("aec:space").GetTargets()
        if second_space:
            first.CreateRelationship("aec:adjacentSpace").SetTargets(second_space)
        if first_space:
            second.CreateRelationship("aec:adjacentSpace").SetTargets(first_space)


def _rebuild_openings(stage, block):
    specs = read_opening_specs(stage, block)
    created = 0
    for spec in specs:
        host = stage.GetPrimAtPath(spec["host_surface"])
        if not host or not host.IsValid() or not host.IsA(UsdGeom.Mesh):
            carb.log_warn(
                f"[AEC Modelling] Skipping opening spec {spec['path']}: "
                f"host surface no longer exists ({spec['host_surface']})"
            )
            continue
        try:
            opening = _define_opening_from_spec(stage, host, spec)
        except Exception as exc:
            carb.log_warn(f"[AEC Modelling] Opening rebuild failed for {spec['path']}: {exc}")
            continue
        opening.CreateRelationship("aec:spec").SetTargets([spec["path"]])
        created += 1
    carb.log_info(f"[AEC Modelling] Rebuilt {created}/{len(specs)} openings for {block.GetPath()}")


def _capture_existing_openings_as_specs(stage, block):
    captured = 0
    updated = 0
    for prim in Usd.PrimRange(block):
        if _attr_value(prim, "aec:type", "") != "Opening":
            continue
        spec_rel = prim.GetRelationship("aec:spec")
        spec_targets = spec_rel.GetTargets() if spec_rel else []
        host_rel = prim.GetRelationship("aec:hostSurface")
        host_targets = host_rel.GetTargets() if host_rel else []
        if not host_targets:
            continue
        host = stage.GetPrimAtPath(host_targets[0])
        if not host or not host.IsValid():
            continue
        values = _opening_values_from_existing_prim(stage, prim, host)
        opening_type = _attr_value(prim, "aec:openingType", "Window")
        if values is None:
            values = {
                "width": float(_attr_value(prim, "aec:width", 1.2)),
                "height": float(_attr_value(prim, "aec:height", 1.2)),
                "sill": float(_attr_value(prim, "aec:sillHeight", 1.0)),
                "offset": float(_attr_value(prim, "aec:horizontalOffset", 0.0)),
            }
        if spec_targets:
            spec = stage.GetPrimAtPath(spec_targets[0])
            if spec and spec.IsValid():
                update_opening_spec(
                    stage,
                    spec,
                    block,
                    host,
                    opening_type,
                    values["width"],
                    values["height"],
                    values["sill"],
                    values["offset"],
                )
                updated += 1
                continue
        create_opening_spec(
            stage,
            block,
            host,
            opening_type,
            values["width"],
            values["height"],
            values["sill"],
            values["offset"],
        )
        captured += 1
    if captured or updated:
        carb.log_info(f"[AEC Modelling] Captured {captured} and updated {updated} opening specs")


def _capture_existing_partitions_as_specs(stage, block, bounds):
    updated = 0
    for prim in Usd.PrimRange(block):
        if _attr_value(prim, "aec:type", "") != "Partition":
            continue
        spec_rel = prim.GetRelationship("aec:spec")
        spec_targets = spec_rel.GetTargets() if spec_rel else []
        if not spec_targets:
            continue
        spec = stage.GetPrimAtPath(spec_targets[0])
        if not spec or not spec.IsValid():
            continue
        values = _partition_values_from_existing_prim(prim, block, bounds, spec)
        if values is None:
            continue
        spec.CreateAttribute("aec:orientation", Sdf.ValueTypeNames.String).Set(values["orientation"])
        spec.CreateAttribute("aec:offsetNormalized", Sdf.ValueTypeNames.Float).Set(values["offset_normalized"])
        spec.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(values["height"])
        updated += 1
    if updated:
        carb.log_info(f"[AEC Modelling] Updated {updated} partition specs from current geometry")


def _remove_deleted_partition_specs(stage, block):
    removed = 0
    for spec in read_partition_specs(stage, block):
        prim_path_attr = spec["prim"].GetAttribute("aec:partitionPrimPath")
        if not prim_path_attr or not prim_path_attr.IsValid() or not prim_path_attr.HasAuthoredValueOpinion():
            continue
        prim_path = prim_path_attr.Get()
        if prim_path and not stage.GetPrimAtPath(prim_path).IsValid():
            stage.RemovePrim(spec["path"])
            removed += 1
    if removed:
        carb.log_info(f"[AEC Modelling] Removed {removed} deleted partition specs before rebuild")


def _opening_values_from_existing_prim(stage, opening, host):
    panel = stage.GetPrimAtPath(opening.GetPath().AppendPath("Panel"))
    if not panel or not panel.IsValid() or not panel.IsA(UsdGeom.Mesh):
        return None

    points = UsdGeom.Mesh(panel).GetPointsAttr().Get() or []
    if len(points) < 4:
        return None

    panel_to_world = UsdGeom.Xformable(panel).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    host_to_world = UsdGeom.Xformable(host).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    world_to_host = host_to_world.GetInverse()
    host_points = [
        Gf.Vec3f(world_to_host.Transform(panel_to_world.Transform(Gf.Vec3d(point))))
        for point in points
    ]

    basis = _wall_basis(host)
    origin = basis["bottom_left"]
    u_values = [Gf.Dot(point - origin, basis["h_dir"]) for point in host_points]
    v_values = [Gf.Dot(point - origin, basis["v_dir"]) for point in host_points]
    width = max(u_values) - min(u_values)
    height = max(v_values) - min(v_values)
    sill = min(v_values)
    offset = ((min(u_values) + max(u_values)) * 0.5) - (basis["width"] * 0.5)
    return _clamped_opening_values(host, width, height, sill, offset)


def _partition_values_from_existing_prim(partition, block, bounds, spec):
    points = UsdGeom.Mesh(partition).GetPointsAttr().Get() or []
    if len(points) < 4:
        return None

    partition_to_world = UsdGeom.Xformable(partition).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    block_to_world = UsdGeom.Xformable(block).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    world_to_block = block_to_world.GetInverse()
    block_points = [
        Gf.Vec3f(world_to_block.Transform(partition_to_world.Transform(Gf.Vec3d(point))))
        for point in points
    ]

    min_p = bounds["min"]
    max_p = bounds["max"]
    orientation = _attr_value(spec, "aec:orientation", _attr_value(partition, "aec:orientation", "Across X"))
    if orientation == "Across Y":
        span = max(float(max_p[0] - min_p[0]), 1e-6)
        offset = (sum(float(point[0]) for point in block_points) / len(block_points) - float(min_p[0])) / span
    else:
        span = max(float(max_p[1] - min_p[1]), 1e-6)
        offset = (sum(float(point[1]) for point in block_points) / len(block_points) - float(min_p[1])) / span

    block_height = max(float(max_p[2] - min_p[2]), 0.001)
    z_values = [float(point[2]) for point in block_points]
    return {
        "orientation": orientation,
        "offset_normalized": _clamp(offset, 0.001, 0.999),
        "height": block_height,
    }


def _define_opening_from_spec(stage, wall_prim, spec):
    points, clamped_width, clamped_height = _opening_points_on_wall(
        wall_prim,
        spec["width"],
        spec["height"],
        spec["sill"],
        spec["offset"],
    )
    openings_parent_path = wall_prim.GetPath().AppendPath("Openings")
    openings_parent = UsdGeom.Xform.Define(stage, openings_parent_path).GetPrim()
    openings_parent.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Openings")

    opening_path = openings_parent_path.AppendPath(_opening_name(spec))
    opening = UsdGeom.Xform.Define(stage, opening_path).GetPrim()
    opening.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Opening")
    opening.CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(spec["opening_type"])
    opening.CreateAttribute("aec:width", Sdf.ValueTypeNames.Float).Set(float(clamped_width))
    opening.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(clamped_height))
    clamped_values = _clamped_opening_values(wall_prim, spec["width"], spec["height"], spec["sill"], spec["offset"])
    opening.CreateAttribute("aec:sillHeight", Sdf.ValueTypeNames.Float).Set(float(clamped_values["sill"]))
    opening.CreateAttribute("aec:horizontalOffset", Sdf.ValueTypeNames.Float).Set(float(clamped_values["offset"]))
    opening.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set("SubSurface")
    opening.CreateRelationship("aec:hostSurface").SetTargets([wall_prim.GetPath()])

    frame = _opening_frame_from_points(points)
    _set_xform_matrix(opening, frame["matrix"])

    panel = UsdGeom.Mesh.Define(stage, opening_path.AppendPath("Panel"))
    panel.GetPointsAttr().Set(Vt.Vec3fArray(frame["local_points"]))
    panel.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
    panel.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))
    panel.GetNormalsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(0.0, 0.0, 1.0)] * 4))
    panel.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    panel.CreateSubdivisionSchemeAttr().Set("none")
    panel.CreateDoubleSidedAttr().Set(True)
    panel.CreateDisplayColorAttr().Set(Vt.Vec3fArray([_opening_color(spec["opening_type"])]))
    panel.CreateDisplayOpacityAttr().Set(Vt.FloatArray([0.45]))
    st_primvar = UsdGeom.PrimvarsAPI(panel.GetPrim()).CreatePrimvar(
        "st",
        Sdf.ValueTypeNames.TexCoord2fArray,
        UsdGeom.Tokens.faceVarying,
    )
    st_primvar.Set(
        Vt.Vec2fArray(
            [
                Gf.Vec2f(0.0, 0.0),
                Gf.Vec2f(1.0, 0.0),
                Gf.Vec2f(1.0, 1.0),
                Gf.Vec2f(0.0, 1.0),
            ]
        )
    )
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(panel, Usd.TimeCode.Default())
    if extent:
        panel.GetExtentAttr().Set(extent)
    panel.GetPrim().CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("OpeningPanel")
    panel.GetPrim().CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(spec["opening_type"])
    return opening


def _opening_name(spec):
    prefix = "Door" if spec["opening_type"] == "Door" else "Window"
    suffix = spec["spec_id"].split("_")[-1]
    return f"{prefix}_{suffix}"


def _opening_points_on_wall(wall_prim, width, height, sill, offset):
    wall_basis = _wall_basis(wall_prim)
    h_dir = wall_basis["h_dir"]
    v_dir = wall_basis["v_dir"]
    normal = wall_basis["normal"]
    wall_width = wall_basis["width"]
    clamped = _clamped_opening_values(wall_prim, width, height, sill, offset)
    clamped_width = clamped["width"]
    clamped_height = clamped["height"]
    center_on_bottom = wall_basis["bottom_left"] + h_dir * (wall_width * 0.5 + clamped["offset"])
    bottom_center = center_on_bottom + v_dir * clamped["sill"] + normal * 0.01

    p0 = bottom_center - h_dir * (clamped_width * 0.5)
    p1 = bottom_center + h_dir * (clamped_width * 0.5)
    p2 = p1 + v_dir * clamped_height
    p3 = p0 + v_dir * clamped_height
    return [p0, p1, p2, p3], clamped_width, clamped_height


def _clamped_opening_values(wall_prim, width, height, sill, offset):
    wall_basis = _wall_basis(wall_prim)
    margin = 0.05
    wall_width = max(float(wall_basis["width"]), 0.001)
    wall_height = max(float(wall_basis["height"]), 0.001)
    clamped_width = _clamp(width, 0.001, max(wall_width - margin, 0.001))
    clamped_height = _clamp(height, 0.001, max(wall_height - margin, 0.001))
    clamped_sill = _clamp(sill, 0.0, max(wall_height - clamped_height - margin, 0.0))
    center_u = _clamp(wall_width * 0.5 + offset, clamped_width * 0.5, wall_width - clamped_width * 0.5)
    return {
        "width": clamped_width,
        "height": clamped_height,
        "sill": clamped_sill,
        "offset": center_u - wall_width * 0.5,
    }


def _wall_basis(wall_prim):
    authored = _authored_surface_basis(wall_prim)
    if authored is not None:
        return authored

    points = UsdGeom.Mesh(wall_prim).GetPointsAttr().Get() or []
    if len(points) < 4:
        raise ValueError("Wall mesh needs at least four points.")

    bottom_left = Gf.Vec3f(points[0])
    bottom_right = Gf.Vec3f(points[1])
    top_left = Gf.Vec3f(points[3])
    horizontal = bottom_right - bottom_left
    vertical = top_left - bottom_left
    if horizontal.GetLength() <= 1e-6 or vertical.GetLength() <= 1e-6:
        raise ValueError("Wall has invalid basis vectors.")

    h_dir = horizontal.GetNormalized()
    v_dir = vertical.GetNormalized()
    normal = Gf.Cross(h_dir, v_dir)
    if normal.GetLength() > 0.0:
        normal.Normalize()

    return {
        "bottom_left": bottom_left,
        "h_dir": h_dir,
        "v_dir": v_dir,
        "normal": normal,
        "width": horizontal.GetLength(),
        "height": vertical.GetLength(),
    }


def _author_surface_basis(surface, points, normal):
    basis = _basis_from_surface_points(points)
    surface.CreateAttribute("aec:basisOrigin", Sdf.ValueTypeNames.Float3).Set(basis["origin"])
    surface.CreateAttribute("aec:basisHDir", Sdf.ValueTypeNames.Float3).Set(basis["h_dir"])
    surface.CreateAttribute("aec:basisVDir", Sdf.ValueTypeNames.Float3).Set(basis["v_dir"])
    surface.CreateAttribute("aec:basisNormal", Sdf.ValueTypeNames.Float3).Set(normal)
    surface.CreateAttribute("aec:basisWidth", Sdf.ValueTypeNames.Float).Set(float(basis["width"]))
    surface.CreateAttribute("aec:basisHeight", Sdf.ValueTypeNames.Float).Set(float(basis["height"]))


def _authored_surface_basis(surface):
    origin_attr = surface.GetAttribute("aec:basisOrigin")
    h_attr = surface.GetAttribute("aec:basisHDir")
    v_attr = surface.GetAttribute("aec:basisVDir")
    normal_attr = surface.GetAttribute("aec:basisNormal")
    width_attr = surface.GetAttribute("aec:basisWidth")
    height_attr = surface.GetAttribute("aec:basisHeight")
    attrs = [origin_attr, h_attr, v_attr, normal_attr, width_attr, height_attr]
    if not all(attr and attr.IsValid() and attr.HasAuthoredValueOpinion() for attr in attrs):
        return None

    origin = Gf.Vec3f(origin_attr.Get())
    h_dir = Gf.Vec3f(h_attr.Get())
    v_dir = Gf.Vec3f(v_attr.Get())
    normal = Gf.Vec3f(normal_attr.Get())
    if h_dir.GetLength() > 0.0:
        h_dir.Normalize()
    if v_dir.GetLength() > 0.0:
        v_dir.Normalize()
    if normal.GetLength() > 0.0:
        normal.Normalize()
    return {
        "bottom_left": origin,
        "h_dir": h_dir,
        "v_dir": v_dir,
        "normal": normal,
        "width": float(width_attr.Get()),
        "height": float(height_attr.Get()),
    }


def _opening_frame_from_points(points):
    if len(points) < 4:
        raise ValueError("Opening panel needs four points.")

    p0 = Gf.Vec3d(points[0])
    p1 = Gf.Vec3d(points[1])
    p3 = Gf.Vec3d(points[3])
    h_vec = p1 - p0
    v_vec = p3 - p0
    width = h_vec.GetLength()
    height = v_vec.GetLength()
    if width <= 1e-6 or height <= 1e-6:
        raise ValueError("Opening panel has invalid dimensions.")

    h_dir = h_vec.GetNormalized()
    v_dir = v_vec.GetNormalized()
    normal = Gf.Cross(h_dir, v_dir)
    if normal.GetLength() <= 1e-6:
        raise ValueError("Opening panel has invalid normal.")
    normal.Normalize()

    center = (Gf.Vec3d(points[0]) + Gf.Vec3d(points[1]) + Gf.Vec3d(points[2]) + Gf.Vec3d(points[3])) * 0.25
    matrix = Gf.Matrix4d(
        h_dir[0], h_dir[1], h_dir[2], 0.0,
        v_dir[0], v_dir[1], v_dir[2], 0.0,
        normal[0], normal[1], normal[2], 0.0,
        center[0], center[1], center[2], 1.0,
    )
    local_points = [
        Gf.Vec3f(-width * 0.5, -height * 0.5, 0.0),
        Gf.Vec3f(width * 0.5, -height * 0.5, 0.0),
        Gf.Vec3f(width * 0.5, height * 0.5, 0.0),
        Gf.Vec3f(-width * 0.5, height * 0.5, 0.0),
    ]
    return {"matrix": matrix, "local_points": local_points}


def _set_xform_matrix(prim, matrix):
    xformable = UsdGeom.Xformable(prim)
    xformable.ClearXformOpOrder()
    xformable.AddTransformOp().Set(matrix)


def _opening_color(opening_type):
    if opening_type == "Door":
        return Gf.Vec3f(0.55, 0.30, 0.12)
    return Gf.Vec3f(0.25, 0.55, 0.90)


def _define_wall_mesh_with_openings(stage, path, points, normal, opening_specs):
    basis = _basis_from_surface_points(points)
    opening_rects = []
    for spec in opening_specs:
        rect = _opening_rect_from_spec(basis, spec)
        if rect is not None:
            opening_rects.append(rect)

    if not opening_rects:
        return _define_quad_mesh(stage, path, points, normal)

    u_cuts = [0.0, basis["width"]]
    v_cuts = [0.0, basis["height"]]
    for rect in opening_rects:
        u_cuts.extend([rect["u0"], rect["u1"]])
        v_cuts.extend([rect["v0"], rect["v1"]])
    u_cuts = _unique_sorted_with_tolerance(u_cuts, 1e-5)
    v_cuts = _unique_sorted_with_tolerance(v_cuts, 1e-5)

    mesh_points = []
    indices = []
    counts = []
    normals = []
    sts = []
    for v_index in range(len(v_cuts) - 1):
        for u_index in range(len(u_cuts) - 1):
            u0 = u_cuts[u_index]
            u1 = u_cuts[u_index + 1]
            v0 = v_cuts[v_index]
            v1 = v_cuts[v_index + 1]
            center_u = (u0 + u1) * 0.5
            center_v = (v0 + v1) * 0.5
            if _point_inside_any_rect(center_u, center_v, opening_rects):
                continue

            start = len(mesh_points)
            mesh_points.extend(
                [
                    basis["origin"] + basis["h_dir"] * u0 + basis["v_dir"] * v0,
                    basis["origin"] + basis["h_dir"] * u1 + basis["v_dir"] * v0,
                    basis["origin"] + basis["h_dir"] * u1 + basis["v_dir"] * v1,
                    basis["origin"] + basis["h_dir"] * u0 + basis["v_dir"] * v1,
                ]
            )
            indices.extend([start, start + 1, start + 2, start + 3])
            counts.append(4)
            normals.extend([normal] * 4)
            sts.extend(
                [
                    Gf.Vec2f(u0 / basis["width"], v0 / basis["height"]),
                    Gf.Vec2f(u1 / basis["width"], v0 / basis["height"]),
                    Gf.Vec2f(u1 / basis["width"], v1 / basis["height"]),
                    Gf.Vec2f(u0 / basis["width"], v1 / basis["height"]),
                ]
            )

    if not mesh_points:
        carb.log_warn(f"[AEC Modelling] Wall {path} would be fully consumed by openings; keeping fallback quad")
        return _define_quad_mesh(stage, path, points, normal)

    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(mesh_points))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(counts))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(indices))
    mesh.GetNormalsAttr().Set(Vt.Vec3fArray(normals))
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    mesh.CreateSubdivisionSchemeAttr().Set("none")

    st_primvar = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar(
        "st",
        Sdf.ValueTypeNames.TexCoord2fArray,
        UsdGeom.Tokens.faceVarying,
    )
    st_primvar.Set(Vt.Vec2fArray(sts))
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(mesh, Usd.TimeCode.Default())
    if extent:
        mesh.GetExtentAttr().Set(extent)
    return mesh


def _basis_from_surface_points(points):
    origin = Gf.Vec3f(points[0])
    horizontal = Gf.Vec3f(points[1]) - origin
    vertical = Gf.Vec3f(points[3]) - origin
    if horizontal.GetLength() <= 1e-6 or vertical.GetLength() <= 1e-6:
        raise ValueError("Surface has invalid basis vectors.")
    return {
        "origin": origin,
        "h_dir": horizontal.GetNormalized(),
        "v_dir": vertical.GetNormalized(),
        "width": horizontal.GetLength(),
        "height": vertical.GetLength(),
    }


def _opening_rect_from_spec(basis, spec):
    margin = 0.05
    width = _clamp(spec["width"], 0.001, max(basis["width"] - margin, 0.001))
    height = _clamp(spec["height"], 0.001, max(basis["height"] - margin, 0.001))
    sill = _clamp(spec["sill"], 0.0, max(basis["height"] - height - margin, 0.0))
    center_u = _clamp(
        basis["width"] * 0.5 + spec["offset"],
        width * 0.5,
        basis["width"] - width * 0.5,
    )
    return {
        "u0": center_u - width * 0.5,
        "u1": center_u + width * 0.5,
        "v0": sill,
        "v1": sill + height,
    }


def _point_inside_any_rect(u, v, rects):
    for rect in rects:
        if rect["u0"] - 1e-6 <= u <= rect["u1"] + 1e-6 and rect["v0"] - 1e-6 <= v <= rect["v1"] + 1e-6:
            return True
    return False


def _define_quad_mesh(stage, path, points, normal):
    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))
    mesh.GetNormalsAttr().Set(Vt.Vec3fArray([normal] * 4))
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    mesh.CreateSubdivisionSchemeAttr().Set("none")

    st_primvar = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar(
        "st",
        Sdf.ValueTypeNames.TexCoord2fArray,
        UsdGeom.Tokens.faceVarying,
    )
    st_primvar.Set(
        Vt.Vec2fArray(
            [
                Gf.Vec2f(0.0, 0.0),
                Gf.Vec2f(1.0, 0.0),
                Gf.Vec2f(1.0, 1.0),
                Gf.Vec2f(0.0, 1.0),
            ]
        )
    )
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(mesh, Usd.TimeCode.Default())
    if extent:
        mesh.GetExtentAttr().Set(extent)
    return mesh


def _point_from_normalized(bounds, normalized, low_z):
    min_p = bounds["min"]
    max_p = bounds["max"]
    return Gf.Vec3f(
        _lerp(float(min_p[0]), float(max_p[0]), float(normalized[0])),
        _lerp(float(min_p[1]), float(max_p[1]), float(normalized[1])),
        float(min_p[2] if low_z else max_p[2]),
    )


def _set_display_color(prim, color):
    UsdGeom.Gprim(prim).CreateDisplayColorAttr().Set(Vt.Vec3fArray([color]))


def _surface_color(surface_type, boundary):
    if boundary == "Surface":
        return Gf.Vec3f(0.70, 0.62, 0.35)
    if surface_type == "Floor":
        return Gf.Vec3f(0.42, 0.42, 0.42)
    if surface_type == "Ceiling":
        return Gf.Vec3f(0.68, 0.68, 0.68)
    return Gf.Vec3f(0.50, 0.50, 0.50)


def _attr_value(prim, attr_name, default):
    attr = prim.GetAttribute(attr_name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default


def _unique_sorted(values):
    clamped = [_clamp(value, 0.0, 1.0) for value in values]
    result = []
    for value in sorted(clamped):
        if not result or abs(value - result[-1]) > 1e-5:
            result.append(value)
    return result


def _unique_sorted_with_tolerance(values, tolerance):
    result = []
    for value in sorted(float(v) for v in values):
        if not result or abs(value - result[-1]) > tolerance:
            result.append(value)
    return result


def _lerp(start, end, t):
    return start + (end - start) * t


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, float(value)))
