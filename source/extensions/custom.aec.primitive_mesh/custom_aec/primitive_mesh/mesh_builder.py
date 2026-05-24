import math

from pxr import Gf, Sdf, Usd, UsdGeom, Vt


SUPPORTED_PRIMITIVES = ("Box", "Cylinder", "Plane")


def create_or_update_primitive_mesh(
    stage,
    prim_path: str,
    primitive_type: str,
    width: float,
    depth: float,
    height: float,
    segments: int,
):
    if primitive_type not in SUPPORTED_PRIMITIVES:
        raise ValueError(f"Unsupported primitive type: {primitive_type}")

    _ensure_parent_xforms(stage, Sdf.Path(prim_path))
    mesh = UsdGeom.Mesh.Define(stage, prim_path)

    if primitive_type == "Box":
        points, counts, indices, normals, sts = _build_box(width, depth, height)
    elif primitive_type == "Cylinder":
        points, counts, indices, normals, sts = _build_cylinder(width, depth, height, segments)
    else:
        points, counts, indices, normals, sts = _build_plane(width, depth, segments)

    mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))
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

    return mesh.GetPrim()


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


def _build_box(width: float, depth: float, height: float):
    half_w = max(width, 0.001) * 0.5
    half_d = max(depth, 0.001) * 0.5
    top_z = max(height, 0.001)

    corners = [
        Gf.Vec3f(-half_w, -half_d, 0.0),
        Gf.Vec3f(half_w, -half_d, 0.0),
        Gf.Vec3f(half_w, half_d, 0.0),
        Gf.Vec3f(-half_w, half_d, 0.0),
        Gf.Vec3f(-half_w, -half_d, top_z),
        Gf.Vec3f(half_w, -half_d, top_z),
        Gf.Vec3f(half_w, half_d, top_z),
        Gf.Vec3f(-half_w, half_d, top_z),
    ]
    faces = [
        (0, 3, 2, 1, Gf.Vec3f(0.0, 0.0, -1.0)),
        (4, 5, 6, 7, Gf.Vec3f(0.0, 0.0, 1.0)),
        (0, 1, 5, 4, Gf.Vec3f(0.0, -1.0, 0.0)),
        (1, 2, 6, 5, Gf.Vec3f(1.0, 0.0, 0.0)),
        (2, 3, 7, 6, Gf.Vec3f(0.0, 1.0, 0.0)),
        (3, 0, 4, 7, Gf.Vec3f(-1.0, 0.0, 0.0)),
    ]
    return _flatten_faces(corners, faces)


def _build_plane(width: float, depth: float, segments: int):
    half_w = max(width, 0.001) * 0.5
    half_d = max(depth, 0.001) * 0.5
    divisions = max(int(segments), 1)
    points = []

    for y_index in range(divisions + 1):
        y = -half_d + (depth * y_index / divisions)
        for x_index in range(divisions + 1):
            x = -half_w + (width * x_index / divisions)
            points.append(Gf.Vec3f(x, y, 0.0))

    counts = []
    indices = []
    normals = []
    sts = []
    stride = divisions + 1
    for y_index in range(divisions):
        for x_index in range(divisions):
            v0 = y_index * stride + x_index
            v1 = v0 + 1
            v2 = v0 + stride + 1
            v3 = v0 + stride
            counts.append(4)
            indices.extend([v0, v1, v2, v3])
            normals.extend([Gf.Vec3f(0.0, 0.0, 1.0)] * 4)
            sts.extend(
                [
                    Gf.Vec2f(x_index / divisions, y_index / divisions),
                    Gf.Vec2f((x_index + 1) / divisions, y_index / divisions),
                    Gf.Vec2f((x_index + 1) / divisions, (y_index + 1) / divisions),
                    Gf.Vec2f(x_index / divisions, (y_index + 1) / divisions),
                ]
            )

    return points, counts, indices, normals, sts


def _build_cylinder(width: float, depth: float, height: float, segments: int):
    radius_x = max(width, 0.001) * 0.5
    radius_y = max(depth, 0.001) * 0.5
    top_z = max(height, 0.001)
    sides = max(int(segments), 3)

    bottom = []
    top = []
    for i in range(sides):
        angle = 2.0 * math.pi * i / sides
        x = math.cos(angle) * radius_x
        y = math.sin(angle) * radius_y
        bottom.append(Gf.Vec3f(x, y, 0.0))
        top.append(Gf.Vec3f(x, y, top_z))

    points = bottom + top + [Gf.Vec3f(0.0, 0.0, 0.0), Gf.Vec3f(0.0, 0.0, top_z)]
    bottom_center = sides * 2
    top_center = bottom_center + 1
    counts = []
    indices = []
    normals = []
    sts = []

    for i in range(sides):
        next_i = (i + 1) % sides
        side_indices = [i, next_i, sides + next_i, sides + i]
        counts.append(4)
        indices.extend(side_indices)

        mid_angle = 2.0 * math.pi * (i + 0.5) / sides
        normal = Gf.Vec3f(math.cos(mid_angle), math.sin(mid_angle), 0.0).GetNormalized()
        normals.extend([normal] * 4)
        sts.extend(
            [
                Gf.Vec2f(i / sides, 0.0),
                Gf.Vec2f((i + 1) / sides, 0.0),
                Gf.Vec2f((i + 1) / sides, 1.0),
                Gf.Vec2f(i / sides, 1.0),
            ]
        )

    for i in range(sides):
        next_i = (i + 1) % sides
        counts.append(3)
        indices.extend([bottom_center, next_i, i])
        normals.extend([Gf.Vec3f(0.0, 0.0, -1.0)] * 3)
        sts.extend(
            [
                Gf.Vec2f(0.5, 0.5),
                _cylinder_cap_st(bottom[next_i], radius_x, radius_y),
                _cylinder_cap_st(bottom[i], radius_x, radius_y),
            ]
        )

        counts.append(3)
        indices.extend([top_center, sides + i, sides + next_i])
        normals.extend([Gf.Vec3f(0.0, 0.0, 1.0)] * 3)
        sts.extend(
            [
                Gf.Vec2f(0.5, 0.5),
                _cylinder_cap_st(top[i], radius_x, radius_y),
                _cylinder_cap_st(top[next_i], radius_x, radius_y),
            ]
        )

    return points, counts, indices, normals, sts


def _flatten_faces(points, faces):
    counts = []
    indices = []
    normals = []
    sts = []
    face_sts = [
        Gf.Vec2f(0.0, 0.0),
        Gf.Vec2f(1.0, 0.0),
        Gf.Vec2f(1.0, 1.0),
        Gf.Vec2f(0.0, 1.0),
    ]

    for face in faces:
        vertex_indices = face[:-1]
        normal = face[-1]
        counts.append(len(vertex_indices))
        indices.extend(vertex_indices)
        normals.extend([normal] * len(vertex_indices))
        sts.extend(face_sts[: len(vertex_indices)])

    return points, counts, indices, normals, sts


def _cylinder_cap_st(point: Gf.Vec3f, radius_x: float, radius_y: float):
    return Gf.Vec2f(
        (float(point[0]) / (radius_x * 2.0)) + 0.5,
        (float(point[1]) / (radius_y * 2.0)) + 0.5,
    )
