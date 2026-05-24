from pxr import Gf, Sdf, Usd, UsdGeom, Vt


def extrude_closed_curve_to_mesh(stage, curve_prim, block_path: str, height: float):
    curve = UsdGeom.BasisCurves(curve_prim)
    points = curve.GetPointsAttr().Get() or []
    counts = curve.GetCurveVertexCountsAttr().Get() or []

    if not counts:
        raise ValueError("Selected curve has no curveVertexCounts.")

    vertex_count = int(counts[0])
    if vertex_count < 3:
        raise ValueError("Selected curve needs at least 3 vertices.")

    local_to_world = UsdGeom.Xformable(curve_prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    base_points = [
        Gf.Vec3f(local_to_world.Transform(Gf.Vec3d(points[i])))
        for i in range(vertex_count)
    ]
    block_transform = _block_transform_from_world_points(base_points)
    world_to_block = block_transform.GetInverse()
    base_points = [
        Gf.Vec3f(world_to_block.Transform(Gf.Vec3d(point)))
        for point in base_points
    ]
    top_points = [Gf.Vec3f(point[0], point[1], point[2] + height) for point in base_points]
    mesh_points = base_points + top_points

    block = _define_block_hierarchy(stage, Sdf.Path(block_path), curve_prim, height, block_transform)
    mass_path = block.GetPath().AppendPath("Mass/BlockMesh")
    _define_block_mesh(stage, mass_path, mesh_points, base_points, top_points, height)

    space_path = block.GetPath().AppendPath("Spaces/Space_01")
    floor = _define_surface_mesh(
        stage,
        space_path.AppendPath("Surfaces/Floor"),
        [base_points[index] for index in reversed(range(vertex_count))],
        "Floor",
        Gf.Vec3f(0.0, 0.0, -1.0),
    )
    ceiling = _define_surface_mesh(
        stage,
        space_path.AppendPath("Surfaces/Ceiling"),
        top_points,
        "Ceiling",
        Gf.Vec3f(0.0, 0.0, 1.0),
    )
    _link_surface(floor, space_path)
    _link_surface(ceiling, space_path)

    for index in range(vertex_count):
        next_index = (index + 1) % vertex_count
        wall_name = _wall_name(index, vertex_count)
        wall_points = [
            base_points[index],
            base_points[next_index],
            top_points[next_index],
            top_points[index],
        ]
        edge = base_points[next_index] - base_points[index]
        normal = Gf.Vec3f(edge[1], -edge[0], 0.0)
        if normal.GetLength() > 0.0:
            normal.Normalize()
        wall = _define_surface_mesh(
            stage,
            space_path.AppendPath(f"Surfaces/{wall_name}"),
            wall_points,
            "Wall",
            normal,
        )
        _link_surface(wall, space_path)
        openings = UsdGeom.Xform.Define(stage, wall.GetPath().AppendPath("Openings")).GetPrim()
        openings.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Openings")

    return block


def _define_block_hierarchy(stage, block_path: Sdf.Path, curve_prim, height: float, transform):
    _ensure_parent_xforms(stage, block_path)
    building = stage.GetPrimAtPath("/World/Building")
    if building and building.IsValid():
        building.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Building")

    block = UsdGeom.Xform.Define(stage, block_path).GetPrim()
    _set_xform_matrix(block, transform)
    block.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Block")
    block.CreateAttribute("aec:blockKind", Sdf.ValueTypeNames.String).Set("Extruded")
    block.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))
    block.CreateAttribute("aec:sourceCurve", Sdf.ValueTypeNames.String).Set(curve_prim.GetPath().pathString)
    block.CreateRelationship("aec:sourceCurveRel").SetTargets([curve_prim.GetPath()])

    for child_name, child_type in [
        ("Sketch", "SketchContainer"),
        ("Mass", "Mass"),
        ("Spaces", "Spaces"),
        ("Spaces/Space_01", "Space"),
        ("Spaces/Space_01/Surfaces", "Surfaces"),
        ("Partitions", "Partitions"),
        ("Metadata", "Metadata"),
    ]:
        child = UsdGeom.Xform.Define(stage, block_path.AppendPath(child_name)).GetPrim()
        child.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set(child_type)

    block.GetStage().GetPrimAtPath(block_path.AppendPath("Spaces/Space_01")).CreateAttribute(
        "aec:name",
        Sdf.ValueTypeNames.String,
    ).Set("Space_01")
    return block


def _block_transform_from_world_points(points):
    if len(points) < 2:
        return Gf.Matrix4d(1.0)

    origin = Gf.Vec3d(0.0, 0.0, 0.0)
    for point in points:
        origin += Gf.Vec3d(point)
    origin /= len(points)

    x_dir = Gf.Vec3d(points[1] - points[0])
    x_dir[2] = 0.0
    if x_dir.GetLength() <= 1e-6:
        x_dir = Gf.Vec3d(1.0, 0.0, 0.0)
    else:
        x_dir.Normalize()

    z_dir = Gf.Vec3d(0.0, 0.0, 1.0)
    y_dir = Gf.Cross(z_dir, x_dir)
    if y_dir.GetLength() <= 1e-6:
        y_dir = Gf.Vec3d(0.0, 1.0, 0.0)
    else:
        y_dir.Normalize()

    origin[2] = min(float(point[2]) for point in points)
    return Gf.Matrix4d(
        x_dir[0], x_dir[1], x_dir[2], 0.0,
        y_dir[0], y_dir[1], y_dir[2], 0.0,
        z_dir[0], z_dir[1], z_dir[2], 0.0,
        origin[0], origin[1], origin[2], 1.0,
    )


def _set_xform_matrix(prim, matrix):
    xformable = UsdGeom.Xformable(prim)
    xformable.ClearXformOpOrder()
    xformable.AddTransformOp().Set(matrix)


def _define_block_mesh(stage, mesh_path, mesh_points, base_points, top_points, height):
    face_counts = []
    face_indices = []
    normals = []
    sts = []
    vertex_count = len(base_points)

    _append_cap(face_counts, face_indices, normals, sts, base_points, reversed(range(vertex_count)), Gf.Vec3f(0.0, 0.0, -1.0))
    _append_cap(face_counts, face_indices, normals, sts, top_points, range(vertex_count), Gf.Vec3f(0.0, 0.0, 1.0), index_offset=vertex_count)
    _append_sides(face_counts, face_indices, normals, sts, base_points, height)
    mesh = _define_mesh(stage, mesh_path, mesh_points, face_counts, face_indices, normals, sts)
    prim = mesh.GetPrim()
    prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Mass")
    UsdGeom.Imageable(prim).MakeInvisible()
    _set_display_color(prim, "Mass")
    return prim


def _define_surface_mesh(stage, mesh_path, points, surface_type, normal):
    if surface_type in ("Floor", "Ceiling") and len(points) > 4:
        triangles = _triangulate_polygon(points, normal)
        face_counts = [3] * len(triangles)
        face_indices = [index for triangle in triangles for index in triangle]
    else:
        face_counts = [len(points)]
        face_indices = list(range(len(points)))
    normals = [normal] * len(face_indices)
    sts = _surface_sts(points)
    if len(sts) == len(points) and len(face_indices) != len(points):
        sts = [sts[index] for index in face_indices]
    mesh = _define_mesh(stage, mesh_path, points, face_counts, face_indices, normals, sts)
    prim = mesh.GetPrim()
    prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Surface")
    prim.CreateAttribute("aec:surfaceType", Sdf.ValueTypeNames.String).Set(surface_type)
    prim.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set(_thermal_boundary(surface_type))
    _set_display_color(prim, surface_type)
    return prim


def _define_mesh(stage, mesh_path, points, face_counts, face_indices, normals, sts):
    mesh = UsdGeom.Mesh.Define(stage, mesh_path)
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(face_counts))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(face_indices))
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


def _link_surface(surface_prim, space_path):
    surface_prim.CreateRelationship("aec:space").SetTargets([space_path])


def _set_display_color(prim, kind):
    colors = {
        "Mass": Gf.Vec3f(0.56, 0.56, 0.56),
        "Floor": Gf.Vec3f(0.42, 0.42, 0.42),
        "Ceiling": Gf.Vec3f(0.68, 0.68, 0.68),
        "Wall": Gf.Vec3f(0.50, 0.50, 0.50),
    }
    UsdGeom.Gprim(prim).CreateDisplayColorAttr().Set(
        Vt.Vec3fArray([colors.get(kind, Gf.Vec3f(0.55, 0.55, 0.55))])
    )


def _thermal_boundary(surface_type):
    if surface_type in ("Floor", "Ceiling", "Wall"):
        return "Exterior"
    return "Unknown"


def _wall_name(index, vertex_count):
    if vertex_count == 4:
        return ["Wall_Front", "Wall_Right", "Wall_Back", "Wall_Left"][index]
    return f"Wall_{index + 1:02d}"


def _surface_sts(points):
    if len(points) < 3:
        return [Gf.Vec2f(0.0, 0.0) for _ in points]

    min_x, min_y, max_x, max_y = _xy_bounds(points)
    z_values = [float(point[2]) for point in points]
    if max(z_values) - min(z_values) < 1e-6:
        return [_xy_st(point, min_x, min_y, max_x, max_y) for point in points]

    distances = [0.0]
    for index in range(1, len(points)):
        distances.append(distances[-1] + (points[index] - points[index - 1]).GetLength())
    total = max(distances[-1], 0.001)
    min_z = min(z_values)
    height = max(max(z_values) - min_z, 0.001)
    return [
        Gf.Vec2f(distances[index] / total, (float(point[2]) - min_z) / height)
        for index, point in enumerate(points)
    ]


def _append_cap(face_counts, face_indices, normals, sts, points, indices_iter, normal, index_offset=0):
    indices = list(indices_iter)
    ordered_points = [points[index] for index in indices]
    triangles = _triangulate_polygon(ordered_points, normal) if len(indices) > 4 else [tuple(range(len(indices)))]
    min_x, min_y, max_x, max_y = _xy_bounds(points)
    cap_sts = [_xy_st(points[index], min_x, min_y, max_x, max_y) for index in indices]
    for triangle in triangles:
        face_counts.append(len(triangle))
        for local_index in triangle:
            source_index = indices[local_index]
            face_indices.append(index_offset + source_index)
            normals.append(normal)
            sts.append(cap_sts[local_index])


def _append_sides(face_counts, face_indices, normals, sts, base_points, height):
    count = len(base_points)
    perimeter = _perimeter_lengths(base_points)
    total_length = perimeter[-1] if perimeter[-1] > 0.0 else 1.0

    for index in range(count):
        next_index = (index + 1) % count
        face_counts.append(4)
        face_indices.extend([index, next_index, count + next_index, count + index])

        edge = base_points[next_index] - base_points[index]
        normal = Gf.Vec3f(edge[1], -edge[0], 0.0)
        if normal.GetLength() > 0.0:
            normal.Normalize()
        normals.extend([normal] * 4)

        u0 = perimeter[index] / total_length
        u1 = perimeter[next_index] / total_length if next_index != 0 else 1.0
        sts.extend(
            [
                Gf.Vec2f(u0, 0.0),
                Gf.Vec2f(u1, 0.0),
                Gf.Vec2f(u1, max(height, 0.001)),
                Gf.Vec2f(u0, max(height, 0.001)),
            ]
        )


def _perimeter_lengths(points):
    lengths = [0.0]
    for index in range(1, len(points)):
        lengths.append(lengths[-1] + (points[index] - points[index - 1]).GetLength())
    lengths.append(lengths[-1] + (points[0] - points[-1]).GetLength())
    return lengths


def _xy_bounds(points):
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _xy_st(point, min_x, min_y, max_x, max_y):
    width = max(max_x - min_x, 0.001)
    depth = max(max_y - min_y, 0.001)
    return Gf.Vec2f((float(point[0]) - min_x) / width, (float(point[1]) - min_y) / depth)


def _triangulate_polygon(points, normal):
    if len(points) < 3:
        raise ValueError("Polygon needs at least 3 points.")
    if len(points) == 3:
        return [(0, 1, 2)]

    desired_sign = 1.0 if float(normal[2]) >= 0.0 else -1.0
    indices = list(range(len(points)))
    if _signed_area_xy(points) * desired_sign < 0.0:
        indices.reverse()

    triangles = []
    guard = 0
    while len(indices) > 3 and guard < len(points) * len(points):
        guard += 1
        ear_found = False
        polygon_sign = 1.0 if _signed_area_xy([points[index] for index in indices]) >= 0.0 else -1.0
        for cursor in range(len(indices)):
            prev_i = indices[(cursor - 1) % len(indices)]
            curr_i = indices[cursor]
            next_i = indices[(cursor + 1) % len(indices)]
            if not _is_convex_corner(points[prev_i], points[curr_i], points[next_i], polygon_sign):
                continue
            if _triangle_contains_any_point(points, prev_i, curr_i, next_i, indices):
                continue
            triangles.append((prev_i, curr_i, next_i))
            del indices[cursor]
            ear_found = True
            break
        if not ear_found:
            raise ValueError("Could not triangulate polygon footprint; check self-intersections or duplicate points.")

    if len(indices) == 3:
        triangles.append((indices[0], indices[1], indices[2]))
    if not triangles:
        raise ValueError("Could not triangulate polygon footprint.")
    return triangles


def _signed_area_xy(points):
    area = 0.0
    for index, point in enumerate(points):
        other = points[(index + 1) % len(points)]
        area += float(point[0]) * float(other[1]) - float(other[0]) * float(point[1])
    return area * 0.5


def _is_convex_corner(prev_point, curr_point, next_point, polygon_sign):
    cross = (
        (float(curr_point[0]) - float(prev_point[0])) * (float(next_point[1]) - float(curr_point[1]))
        - (float(curr_point[1]) - float(prev_point[1])) * (float(next_point[0]) - float(curr_point[0]))
    )
    return cross * polygon_sign > 1e-8


def _triangle_contains_any_point(points, a_index, b_index, c_index, polygon_indices):
    a = points[a_index]
    b = points[b_index]
    c = points[c_index]
    for index in polygon_indices:
        if index in (a_index, b_index, c_index):
            continue
        if _point_in_triangle_xy(points[index], a, b, c):
            return True
    return False


def _point_in_triangle_xy(point, a, b, c):
    px, py = float(point[0]), float(point[1])
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    cx, cy = float(c[0]), float(c[1])
    denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(denom) <= 1e-12:
        return False
    alpha = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / denom
    beta = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / denom
    gamma = 1.0 - alpha - beta
    tolerance = 1e-8
    return alpha > tolerance and beta > tolerance and gamma > tolerance


def _ensure_parent_xforms(stage, path: Sdf.Path):
    parent = path.GetParentPath()
    if parent == Sdf.Path.absoluteRootPath:
        return

    ancestors = []
    current = parent
    while current != Sdf.Path.absoluteRootPath:
        ancestors.append(current)
        current = current.GetParentPath()

    for ancestor in reversed(ancestors):
        if not stage.GetPrimAtPath(ancestor).IsValid():
            UsdGeom.Xform.Define(stage, ancestor)
