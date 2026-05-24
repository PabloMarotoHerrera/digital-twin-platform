from pxr import Sdf, UsdGeom


AEC_PATH_NAME = "_AEC"
PARTITION_SPECS_NAME = "PartitionSpecs"


def ensure_aec_container(stage, block_path):
    block_path = Sdf.Path(block_path)
    aec = UsdGeom.Xform.Define(stage, block_path.AppendPath(AEC_PATH_NAME)).GetPrim()
    aec.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("AECMetadata")

    specs = UsdGeom.Xform.Define(stage, aec.GetPath().AppendPath(PARTITION_SPECS_NAME)).GetPrim()
    specs.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("PartitionSpecs")
    return aec, specs


def create_partition_spec(stage, block, orientation, offset_normalized, height, thickness):
    _, specs_parent = ensure_aec_container(stage, block.GetPath())
    spec_id = _next_spec_id(specs_parent)
    spec_path = specs_parent.GetPath().AppendPath(spec_id)
    spec = UsdGeom.Xform.Define(stage, spec_path).GetPrim()

    spec.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("PartitionSpec")
    spec.CreateAttribute("aec:specId", Sdf.ValueTypeNames.String).Set(spec_id)
    spec.CreateAttribute("aec:orientation", Sdf.ValueTypeNames.String).Set(orientation)
    spec.CreateAttribute("aec:offsetNormalized", Sdf.ValueTypeNames.Float).Set(float(_clamp(offset_normalized, 0.0, 1.0)))
    spec.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))
    spec.CreateAttribute("aec:thickness", Sdf.ValueTypeNames.Float).Set(float(thickness))
    spec.CreateAttribute("aec:level", Sdf.ValueTypeNames.Int).Set(0)
    spec.CreateRelationship("aec:block").SetTargets([block.GetPath()])
    return spec


def read_partition_specs(stage, block):
    specs_path = block.GetPath().AppendPath(AEC_PATH_NAME).AppendPath(PARTITION_SPECS_NAME)
    specs_parent = stage.GetPrimAtPath(specs_path)
    if not specs_parent or not specs_parent.IsValid():
        return []

    specs = []
    for child in specs_parent.GetChildren():
        if _attr_value(child, "aec:type", "") != "PartitionSpec":
            continue
        specs.append(
            {
                "prim": child,
                "path": child.GetPath(),
                "spec_id": _attr_value(child, "aec:specId", child.GetName()),
                "orientation": _attr_value(child, "aec:orientation", "Across X"),
                "offset_normalized": float(_attr_value(child, "aec:offsetNormalized", 0.5)),
                "height": float(_attr_value(child, "aec:height", 3.0)),
                "thickness": float(_attr_value(child, "aec:thickness", 0.1)),
                "level": int(_attr_value(child, "aec:level", 0)),
            }
        )
    return sorted(specs, key=lambda item: item["spec_id"])


def _next_spec_id(specs_parent):
    index = 1
    existing_names = {child.GetName() for child in specs_parent.GetChildren()}
    while True:
        spec_id = f"PartitionSpec_{index:02d}"
        if spec_id not in existing_names:
            return spec_id
        index += 1


def _attr_value(prim, attr_name, default):
    attr = prim.GetAttribute(attr_name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, float(value)))
