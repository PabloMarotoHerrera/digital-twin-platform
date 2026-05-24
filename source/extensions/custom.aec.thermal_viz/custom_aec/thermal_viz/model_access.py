from __future__ import annotations

from dataclasses import dataclass

from pxr import Sdf, Usd, UsdGeom


@dataclass(frozen=True)
class SpaceInfo:
    path: str
    name: str
    block_path: str
    surface_paths: tuple[str, ...]
    bounds_min: tuple[float, float, float] | None
    bounds_max: tuple[float, float, float] | None


def find_spaces(stage: Usd.Stage, root_path: str = "/World/Building") -> list[SpaceInfo]:
    if stage is None:
        return []

    root = stage.GetPrimAtPath(root_path)
    if not root.IsValid():
        return []

    spaces: list[SpaceInfo] = []
    for prim in Usd.PrimRange(root):
        if _get_attr_value(prim, "aec:type") != "Space":
            continue

        space_path = str(prim.GetPath())
        block_path = _get_attr_value(prim, "aec:block") or _infer_block_path(space_path)
        surfaces = _find_surface_paths(prim)
        bounds_min = _vec3_tuple(_get_attr_value(prim, "aec:boundsMin"))
        bounds_max = _vec3_tuple(_get_attr_value(prim, "aec:boundsMax"))

        spaces.append(
            SpaceInfo(
                path=space_path,
                name=prim.GetName(),
                block_path=block_path,
                surface_paths=tuple(surfaces),
                bounds_min=bounds_min,
                bounds_max=bounds_max,
            )
        )

    return sorted(spaces, key=lambda item: item.path)


def _find_surface_paths(space_prim: Usd.Prim) -> list[str]:
    surfaces_root = space_prim.GetStage().GetPrimAtPath(space_prim.GetPath().AppendChild("Surfaces"))
    if not surfaces_root.IsValid():
        return []

    surface_paths: list[str] = []
    for prim in Usd.PrimRange(surfaces_root):
        if prim == surfaces_root:
            continue
        if _get_attr_value(prim, "aec:type") == "Surface" or prim.IsA(UsdGeom.Mesh):
            surface_paths.append(str(prim.GetPath()))
    return sorted(surface_paths)


def _infer_block_path(space_path: str) -> str:
    path = Sdf.Path(space_path)
    while path != Sdf.Path.absoluteRootPath:
        if path.name.startswith("Block_"):
            return str(path)
        path = path.GetParentPath()
    return ""


def _get_attr_value(prim: Usd.Prim, name: str):
    attr = prim.GetAttribute(name)
    if not attr:
        return None
    return attr.Get()


def _vec3_tuple(value) -> tuple[float, float, float] | None:
    if value is None:
        return None
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError, IndexError):
        return None

