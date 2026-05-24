from __future__ import annotations

import carb
import omni.usd
from custom_aec.extrude.mesh_builder import extrude_closed_curve_to_mesh
from custom_aec.primitive_mesh.mesh_builder import create_or_update_primitive_mesh
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt

from .partition_specs import ensure_aec_container
from .rebuild import rebuild_block
from .rebuild_polygon import rebuild_block_for_footprint


BUILDING_PATH = Sdf.Path("/World/Building")
SKETCHES_PATH = BUILDING_PATH.AppendPath("Sketches")
THERMAL_VIZ_ROOT = BUILDING_PATH.AppendPath("_ThermalViz")
THERMAL_MATERIALS_ROOT = BUILDING_PATH.AppendPath("Materials/Thermal")
DEFAULT_CONSTRUCTION = "Generic Lightweight Construction"


def current_stage():
    return omni.usd.get_context().get_stage()


def create_aec_block(stage, width=10.0, depth=8.0, height=3.0, name=None, primitive_type="Box"):
    width = _positive(width, "width")
    depth = _positive(depth, "depth")
    height = _positive(height, "height")
    _ensure_building(stage)
    block_name = _safe_name(name or "Block_01", "Block")
    block_path = Sdf.Path(omni.usd.get_stage_next_free_path(stage, BUILDING_PATH.AppendChild(block_name).pathString, False))

    block = _define_block_hierarchy(stage, block_path, "Primitive", primitive_type=primitive_type)
    mass_path = block.GetPath().AppendPath("Mass/PrimitiveMesh")
    mass = create_or_update_primitive_mesh(stage, mass_path.pathString, primitive_type, width, depth, height, 1)
    mass.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Mass")
    UsdGeom.Imageable(mass).MakeInvisible()
    _set_display_color(mass, Gf.Vec3f(0.56, 0.56, 0.56))
    _apply_metadata(
        block,
        {
            "type": "Block",
            "blockKind": "Primitive",
            "primitiveType": primitive_type,
            "width": width,
            "depth": depth,
            "height": height,
            "segments": 1,
        },
    )
    rebuild_block(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True)
    prepare_block_for_energy_model(stage, block.GetPath())
    carb.log_info(f"[AEC Modelling API] Created primitive block {block.GetPath()}")
    return block


def create_rectangle_sketch(stage, width=10.0, depth=8.0, name=None, path=None):
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
    sketch = create_polygon_sketch(stage, points, name=name or "Rect_01", path=path, closed=True)
    sketch.CreateAttribute("aec:sketchKind", Sdf.ValueTypeNames.String).Set("Rectangle")
    sketch.CreateAttribute("aec:width", Sdf.ValueTypeNames.Float).Set(float(width))
    sketch.CreateAttribute("aec:depth", Sdf.ValueTypeNames.Float).Set(float(depth))
    carb.log_info(f"[AEC Modelling API] Created rectangle sketch {sketch.GetPath()}")
    return sketch


def create_polygon_sketch(stage, points, name=None, path=None, closed=True):
    _ensure_building(stage)
    sketches = UsdGeom.Xform.Define(stage, SKETCHES_PATH).GetPrim()
    sketches.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Sketches")
    if path is None:
        sketch_name = _safe_name(name or "Poly_01", "Sketch")
        path = omni.usd.get_stage_next_free_path(stage, SKETCHES_PATH.AppendChild(sketch_name).pathString, False)
    curve = _define_curve(stage, Sdf.Path(path), [Gf.Vec3f(point) for point in points], closed)
    prim = curve.GetPrim()
    prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Sketch")
    prim.CreateAttribute("aec:sketchKind", Sdf.ValueTypeNames.String).Set("Polygon" if len(points) != 4 else "Rectangle")
    prim.CreateAttribute("aec:closed", Sdf.ValueTypeNames.Bool).Set(bool(closed))
    carb.log_info(f"[AEC Modelling API] Created polygon sketch {prim.GetPath()}")
    return prim


def extrude_sketch_to_block(stage, sketch_path, height=3.0, block_path=None, prepare_energy=True):
    height = _positive(height, "height")
    sketch = stage.GetPrimAtPath(sketch_path)
    if not sketch or not sketch.IsValid() or not sketch.IsA(UsdGeom.BasisCurves):
        raise ValueError(f"Sketch not found or not BasisCurves: {sketch_path}")
    if UsdGeom.BasisCurves(sketch).GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
        raise ValueError("Only closed sketches with wrap=periodic can be extruded.")
    block_path = block_path or omni.usd.get_stage_next_free_path(stage, BUILDING_PATH.AppendChild("Block_01").pathString, False)
    block = extrude_closed_curve_to_mesh(stage, sketch, block_path, height)
    rebuild = rebuild_block_for_footprint(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True)
    block = rebuild["block"]
    if prepare_energy:
        prepare_block_for_energy_model(stage, block.GetPath())
    carb.log_info(f"[AEC Modelling API] Extruded sketch {sketch.GetPath()} to {block.GetPath()} ({rebuild['mode']})")
    return {"block": block, "rebuild": rebuild}


def rebuild_block_native(stage, block_path):
    result = rebuild_block_for_footprint(stage, Sdf.Path(block_path), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True)
    prepare_block_for_energy_model(stage, result["block"].GetPath())
    return result


def assign_default_energy_metadata(stage, block_path):
    block = stage.GetPrimAtPath(block_path)
    if not block or not block.IsValid():
        raise ValueError(f"Block does not exist: {block_path}")
    if _attr(block, "aec:energyModel", None) is None:
        block.CreateAttribute("aec:energyModel", Sdf.ValueTypeNames.Bool).Set(True)
    if _attr(block, "aec:constructionName", None) is None:
        block.CreateAttribute("aec:constructionName", Sdf.ValueTypeNames.String).Set(DEFAULT_CONSTRUCTION)
    if _attr(block, "aec:uValue", None) is None:
        block.CreateAttribute("aec:uValue", Sdf.ValueTypeNames.Float).Set(0.35)
    if _attr(block, "aec:thermalConductivity", None) is None:
        block.CreateAttribute("aec:thermalConductivity", Sdf.ValueTypeNames.Float).Set(0.16)
    if _attr(block, "aec:density", None) is None:
        block.CreateAttribute("aec:density", Sdf.ValueTypeNames.Float).Set(800.0)
    if _attr(block, "aec:specificHeat", None) is None:
        block.CreateAttribute("aec:specificHeat", Sdf.ValueTypeNames.Float).Set(1000.0)
    block.CreateAttribute("aec:exportableToIdf", Sdf.ValueTypeNames.Bool).Set(True)
    return block


def sync_block_to_thermalviz(stage, block_path):
    block = assign_default_energy_metadata(stage, block_path)
    material = _ensure_thermal_material(stage)
    bound_count = _ensure_material_bindings(stage, block, material)
    registry = _ensure_thermalviz_registration(stage, block)
    block.CreateAttribute("aec:thermalVizReady", Sdf.ValueTypeNames.Bool).Set(True)
    carb.log_info(f"[AEC Modelling API] Synced block to ThermalViz {block.GetPath()}")
    return {"block": block, "material": material, "registry": registry, "bound_count": bound_count}


def prepare_block_for_energy_model(stage, block_path):
    return sync_block_to_thermalviz(stage, block_path)


def validate_aec_block(stage, block_path):
    block = stage.GetPrimAtPath(block_path)
    errors = []
    warnings = []
    if not block or not block.IsValid():
        return {"ok": False, "errors": [f"Block does not exist: {block_path}"], "warnings": warnings}
    if _attr(block, "aec:type", "") != "Block":
        errors.append(f"{block_path} is not an AEC Block.")
    if not _mass_mesh(stage, block):
        errors.append(f"{block_path} has no Mass/BlockMesh or Mass/PrimitiveMesh.")
    if not _has_child_type(stage, block, "Space"):
        errors.append(f"{block_path} has no AEC Spaces.")
    if not _has_child_type(stage, block, "Surface"):
        errors.append(f"{block_path} has no AEC Surfaces.")
    for name in ("aec:energyModel", "aec:constructionName", "aec:uValue"):
        if _attr(block, name, None) is None:
            warnings.append(f"{block_path} missing {name}.")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _define_block_hierarchy(stage, block_path, block_kind, primitive_type=""):
    block = UsdGeom.Xform.Define(stage, block_path).GetPrim()
    ensure_aec_container(stage, block_path)
    _apply_metadata(block, {"type": "Block", "blockKind": block_kind})
    if primitive_type:
        block.CreateAttribute("aec:primitiveType", Sdf.ValueTypeNames.String).Set(primitive_type)
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
    stage.GetPrimAtPath(block_path.AppendPath("Spaces/Space_01")).CreateAttribute("aec:name", Sdf.ValueTypeNames.String).Set("Space_01")
    return block


def _define_curve(stage, path, points, closed):
    curve = UsdGeom.BasisCurves.Define(stage, path)
    curve.GetTypeAttr().Set(UsdGeom.Tokens.linear)
    curve.GetWrapAttr().Set(UsdGeom.Tokens.periodic if closed else UsdGeom.Tokens.nonperiodic)
    curve.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
    curve.GetCurveVertexCountsAttr().Set(Vt.IntArray([len(points)] if points else []))
    curve.GetPointsAttr().Set(Vt.Vec3fArray(points))
    if curve.GetPrim().HasProperty("widths"):
        curve.GetPrim().RemoveProperty("widths")
    extent = UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())
    if extent:
        curve.GetExtentAttr().Set(extent)
    return curve


def _ensure_building(stage):
    UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    building = UsdGeom.Xform.Define(stage, BUILDING_PATH).GetPrim()
    building.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Building")
    building.CreateAttribute("aec:schemaVersion", Sdf.ValueTypeNames.String).Set("mvp-1")
    return building


def _ensure_thermal_material(stage):
    UsdGeom.Xform.Define(stage, BUILDING_PATH.AppendChild("Materials")).GetPrim().CreateAttribute(
        "aec:type", Sdf.ValueTypeNames.String
    ).Set("Materials")
    materials_root = UsdGeom.Xform.Define(stage, THERMAL_MATERIALS_ROOT).GetPrim()
    materials_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalMaterials")
    material_path = THERMAL_MATERIALS_ROOT.AppendChild("GenericThermalConstruction")
    material = UsdShade.Material.Define(stage, material_path)
    material.GetPrim().CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalMaterial")
    material.GetPrim().CreateAttribute("aec:constructionName", Sdf.ValueTypeNames.String).Set(DEFAULT_CONSTRUCTION)
    material.GetPrim().CreateAttribute("aec:uValue", Sdf.ValueTypeNames.Float).Set(0.35)
    material.GetPrim().CreateAttribute("aec:thermalConductivity", Sdf.ValueTypeNames.Float).Set(0.16)
    material.GetPrim().CreateAttribute("aec:density", Sdf.ValueTypeNames.Float).Set(800.0)
    material.GetPrim().CreateAttribute("aec:specificHeat", Sdf.ValueTypeNames.Float).Set(1000.0)
    shader = UsdShade.Shader.Define(stage, material_path.AppendChild("PreviewSurface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.34, 0.42, 0.46))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.52)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _ensure_material_bindings(stage, block, material):
    count = 0
    targets = [prim for prim in Usd.PrimRange(block) if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Gprim)]
    if not targets:
        targets = [block]
    for prim in targets:
        binding = UsdShade.MaterialBindingAPI.Apply(prim)
        rel = binding.GetDirectBindingRel()
        if rel and rel.HasAuthoredTargets():
            continue
        binding.Bind(material)
        prim.CreateRelationship("aec:thermalMaterial").SetTargets([material.GetPath()])
        count += 1
    block.CreateRelationship("aec:thermalMaterial").SetTargets([material.GetPath()])
    return count


def _ensure_thermalviz_registration(stage, block):
    root = UsdGeom.Xform.Define(stage, THERMAL_VIZ_ROOT).GetPrim()
    root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalViz")
    blocks_root = UsdGeom.Xform.Define(stage, root.GetPath().AppendChild("Blocks")).GetPrim()
    blocks_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalVizBlocks")
    for child in blocks_root.GetChildren():
        rel = child.GetRelationship("aec:block")
        if rel and block.GetPath() in rel.GetTargets():
            block.CreateRelationship("aec:thermalVizRegistry").SetTargets([child.GetPath()])
            return child
    registry = UsdGeom.Xform.Define(stage, blocks_root.GetPath().AppendChild(_safe_name(block.GetName(), "Block"))).GetPrim()
    registry.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalVizBlock")
    registry.CreateAttribute("aec:blockPath", Sdf.ValueTypeNames.String).Set(block.GetPath().pathString)
    registry.CreateRelationship("aec:block").SetTargets([block.GetPath()])
    block.CreateRelationship("aec:thermalVizRegistry").SetTargets([registry.GetPath()])
    return registry


def _mass_mesh(stage, block):
    for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
        prim = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
        if prim and prim.IsValid() and prim.IsA(UsdGeom.Mesh):
            return prim
    return None


def _has_child_type(stage, block, aec_type):
    return any(_attr(prim, "aec:type", "") == aec_type for prim in Usd.PrimRange(block))


def _apply_metadata(prim, values):
    for key, value in values.items():
        attr_name = key if key.startswith("aec:") else f"aec:{key}"
        if isinstance(value, bool):
            value_type = Sdf.ValueTypeNames.Bool
        elif isinstance(value, int):
            value_type = Sdf.ValueTypeNames.Int
        elif isinstance(value, float):
            value_type = Sdf.ValueTypeNames.Float
        else:
            value_type = Sdf.ValueTypeNames.String
        prim.CreateAttribute(attr_name, value_type).Set(value)


def _set_display_color(prim, color):
    UsdGeom.Gprim(prim).CreateDisplayColorAttr().Set(Vt.Vec3fArray([color]))


def _positive(value, label):
    number = float(value)
    if number <= 0.0:
        raise ValueError(f"{label} must be greater than zero.")
    return number


def _safe_name(name, prefix):
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(name or prefix))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"{prefix}_{cleaned or '01'}"
    return cleaned


def _attr(prim, name, default=None):
    attr = prim.GetAttribute(name) if prim and prim.IsValid() else None
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default
