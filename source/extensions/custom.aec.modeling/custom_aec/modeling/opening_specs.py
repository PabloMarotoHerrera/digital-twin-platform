from pxr import Sdf, UsdGeom

from .partition_specs import ensure_aec_container


OPENING_SPECS_NAME = "OpeningSpecs"


def ensure_opening_specs(stage, block):
    aec, _ = ensure_aec_container(stage, block.GetPath())
    specs = UsdGeom.Xform.Define(stage, aec.GetPath().AppendPath(OPENING_SPECS_NAME)).GetPrim()
    specs.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("OpeningSpecs")
    return specs


def create_opening_spec(stage, block, host_surface, opening_type, width, height, sill, offset):
    specs_parent = ensure_opening_specs(stage, block)
    spec_id = _next_spec_id(specs_parent)
    spec = UsdGeom.Xform.Define(stage, specs_parent.GetPath().AppendPath(spec_id)).GetPrim()
    _write_opening_spec(spec, block, host_surface, opening_type, width, height, sill, offset, spec_id)
    return spec


def update_opening_spec(stage, spec, block, host_surface, opening_type, width, height, sill, offset):
    spec_id = _attr_value(spec, "aec:specId", spec.GetName())
    _write_opening_spec(spec, block, host_surface, opening_type, width, height, sill, offset, spec_id)
    return spec


def read_opening_specs(stage, block):
    specs_path = block.GetPath().AppendPath("_AEC").AppendPath(OPENING_SPECS_NAME)
    specs_parent = stage.GetPrimAtPath(specs_path)
    if not specs_parent or not specs_parent.IsValid():
        return []

    specs = []
    for child in specs_parent.GetChildren():
        if _attr_value(child, "aec:type", "") != "OpeningSpec":
            continue
        rel = child.GetRelationship("aec:hostSurface")
        targets = rel.GetTargets() if rel else []
        if not targets:
            continue
        specs.append(
            {
                "prim": child,
                "path": child.GetPath(),
                "spec_id": _attr_value(child, "aec:specId", child.GetName()),
                "host_surface": targets[0],
                "opening_type": _attr_value(child, "aec:openingType", "Window"),
                "width": float(_attr_value(child, "aec:width", 1.2)),
                "height": float(_attr_value(child, "aec:height", 1.2)),
                "sill": float(_attr_value(child, "aec:sillHeight", 1.0)),
                "offset": float(_attr_value(child, "aec:horizontalOffset", 0.0)),
            }
        )
    return sorted(specs, key=lambda item: item["spec_id"])


def _write_opening_spec(spec, block, host_surface, opening_type, width, height, sill, offset, spec_id):
    spec.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("OpeningSpec")
    spec.CreateAttribute("aec:specId", Sdf.ValueTypeNames.String).Set(spec_id)
    spec.CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(opening_type)
    spec.CreateAttribute("aec:width", Sdf.ValueTypeNames.Float).Set(float(width))
    spec.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))
    spec.CreateAttribute("aec:sillHeight", Sdf.ValueTypeNames.Float).Set(float(sill))
    spec.CreateAttribute("aec:horizontalOffset", Sdf.ValueTypeNames.Float).Set(float(offset))
    spec.CreateRelationship("aec:block").SetTargets([block.GetPath()])
    spec.CreateRelationship("aec:hostSurface").SetTargets([host_surface.GetPath()])


def _next_spec_id(specs_parent):
    index = 1
    existing_names = {child.GetName() for child in specs_parent.GetChildren()}
    while True:
        spec_id = f"OpeningSpec_{index:02d}"
        if spec_id not in existing_names:
            return spec_id
        index += 1


def _attr_value(prim, attr_name, default):
    attr = prim.GetAttribute(attr_name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default
