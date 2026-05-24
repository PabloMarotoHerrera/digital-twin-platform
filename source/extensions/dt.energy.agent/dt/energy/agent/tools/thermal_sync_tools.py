from __future__ import annotations

import carb
import omni.usd
from custom_aec.modeling import api as aec_api
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt

from .results import tool_result


THERMAL_VIZ_ROOT = Sdf.Path("/World/Building/_ThermalViz")
THERMAL_MATERIALS_ROOT = Sdf.Path("/World/Building/Materials/Thermal")
DEFAULT_CONSTRUCTION = "Generic Lightweight Construction"
DEFAULT_U_VALUE = 0.35
DEFAULT_THERMAL_CONDUCTIVITY = 0.16
DEFAULT_DENSITY = 800.0
DEFAULT_SPECIFIC_HEAT = 1000.0
THERMAL_METADATA_ATTRS = (
    "aec:energyModel",
    "aec:constructionName",
    "aec:uValue",
)


def sync_aec_block_to_thermalviz(block_path: str | None = None) -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    block = _resolve_block(stage, block_path)
    if block is None:
        return tool_result(False, "No se encontro un bloque AEC valido.", errors=["Select or provide an AEC Block path."])

    warnings = []
    sync = aec_api.sync_block_to_thermalviz(stage, block.GetPath())
    material = sync["material"]
    bound_count = sync["bound_count"]
    registry_prim = sync["registry"]
    if not _has_spaces(stage, block):
        warnings.append(f"{block.GetPath()} no tiene Spaces AEC; ThermalViz no podra listar zonas hasta reconstruir el bloque.")

    carb.log_info(f"[Energy Twin Agent] Synced AEC block to ThermalViz: {block.GetPath()}")
    return tool_result(
        True,
        "Bloque sincronizado con ThermalViz:",
        {
            "block_path": block.GetPath().pathString,
            "status": "sincronizado",
            "details": [
                f"ThermalViz root: {THERMAL_VIZ_ROOT}",
                f"Registro: {registry_prim.GetPath()}",
                f"Material termico: {material.GetPath()}",
                f"Prims con material nuevo: {bound_count}",
                "API nativa: custom_aec.modeling.api.sync_block_to_thermalviz",
            ],
        },
        warnings,
    )


def sync_all_blocks_to_thermalviz() -> dict:
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return tool_result(False, "No hay ningun stage abierto.", errors=["No stage is currently open."])
    blocks = _all_blocks(stage)
    synced = []
    warnings = []
    errors = []
    for block in blocks:
        result = sync_aec_block_to_thermalviz(block.GetPath().pathString)
        if result["ok"]:
            synced.append(block.GetPath().pathString)
            warnings.extend(result.get("warnings") or [])
        else:
            errors.extend(result.get("errors") or [result.get("message", "Sync failed.")])
    return tool_result(
        not errors,
        "Sincronizacion ThermalViz completada:",
        {
            "block_count": len(blocks),
            "thermalviz_synced_block_count": len(synced),
            "details": [f"Bloques sincronizados: {', '.join(synced) or 'none'}"],
        },
        warnings,
        errors,
    )


def thermalviz_sync_state(stage, block) -> dict:
    return {
        "has_energy_metadata": _has_energy_metadata(block),
        "has_thermal_material": _has_thermal_material(stage, block),
        "thermalviz_registered": _thermalviz_registry_prim(stage, block) is not None,
        "has_spaces": _has_spaces(stage, block),
    }


def is_block_synced_to_thermalviz(stage, block) -> bool:
    state = thermalviz_sync_state(stage, block)
    return bool(state["has_energy_metadata"] and state["has_thermal_material"] and state["thermalviz_registered"])


def unsynced_block_reasons(stage, block) -> list[str]:
    state = thermalviz_sync_state(stage, block)
    reasons = []
    if not state["has_energy_metadata"]:
        reasons.append("metadata energetica incompleta")
    if not state["has_thermal_material"]:
        reasons.append("sin material termico")
    if not state["thermalviz_registered"]:
        reasons.append("no registrado en ThermalViz")
    if not state["has_spaces"]:
        reasons.append("sin Spaces AEC para ThermalViz")
    return reasons


def _resolve_block(stage, block_path: str | None):
    path = block_path or _selected_path()
    if not path:
        return None
    prim = stage.GetPrimAtPath(path)
    if prim and prim.IsValid() and _attr(prim, "aec:type", "") == "Block":
        return prim
    return None


def _selected_path() -> str | None:
    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
    return selection[0] if selection else None


def _all_blocks(stage) -> list[Usd.Prim]:
    building = stage.GetPrimAtPath("/World/Building")
    if not building or not building.IsValid():
        return []
    return [prim for prim in Usd.PrimRange(building) if _attr(prim, "aec:type", "") == "Block"]


def _ensure_energy_metadata(block, added: list[str]):
    if _attr(block, "aec:energyModel", None) is None:
        block.CreateAttribute("aec:energyModel", Sdf.ValueTypeNames.Bool).Set(True)
        added.append("aec:energyModel")
    if _attr(block, "aec:constructionName", None) is None:
        block.CreateAttribute("aec:constructionName", Sdf.ValueTypeNames.String).Set(DEFAULT_CONSTRUCTION)
        added.append("aec:constructionName")
    if _attr(block, "aec:uValue", None) is None:
        block.CreateAttribute("aec:uValue", Sdf.ValueTypeNames.Float).Set(DEFAULT_U_VALUE)
        added.append("aec:uValue")
    block.CreateAttribute("aec:thermalVizReady", Sdf.ValueTypeNames.Bool).Set(True)


def _ensure_thermal_material(stage, added: list[str]) -> UsdShade.Material:
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/Building/Materials")).GetPrim().CreateAttribute(
        "aec:type", Sdf.ValueTypeNames.String
    ).Set("Materials")
    materials_root = UsdGeom.Xform.Define(stage, THERMAL_MATERIALS_ROOT).GetPrim()
    materials_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalMaterials")
    material_path = materials_root.GetPath().AppendChild("GenericThermalConstruction")
    material = UsdShade.Material.Define(stage, material_path)
    material.GetPrim().CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalMaterial")
    material.GetPrim().CreateAttribute("aec:constructionName", Sdf.ValueTypeNames.String).Set(DEFAULT_CONSTRUCTION)
    material.GetPrim().CreateAttribute("aec:uValue", Sdf.ValueTypeNames.Float).Set(DEFAULT_U_VALUE)
    material.GetPrim().CreateAttribute("aec:thermalConductivity", Sdf.ValueTypeNames.Float).Set(DEFAULT_THERMAL_CONDUCTIVITY)
    material.GetPrim().CreateAttribute("aec:density", Sdf.ValueTypeNames.Float).Set(DEFAULT_DENSITY)
    material.GetPrim().CreateAttribute("aec:specificHeat", Sdf.ValueTypeNames.Float).Set(DEFAULT_SPECIFIC_HEAT)

    shader = UsdShade.Shader.Define(stage, material_path.AppendChild("PreviewSurface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.34, 0.42, 0.46))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.52)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    if "thermal_material" not in added:
        added.append("thermal_material")
    return material


def _ensure_material_bindings(stage, block, material: UsdShade.Material, added: list[str]) -> int:
    count = 0
    targets = []
    for prim in Usd.PrimRange(block):
        if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Gprim):
            targets.append(prim)
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
    if count:
        added.append("material_bindings")
    return count


def _ensure_thermalviz_registration(stage, block, added: list[str]):
    root = _ensure_thermalviz_root(stage)
    blocks_root = UsdGeom.Xform.Define(stage, root.GetPath().AppendChild("Blocks")).GetPrim()
    blocks_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalVizBlocks")
    existing = _thermalviz_registry_prim(stage, block)
    if existing is not None:
        return existing
    registry_path = blocks_root.GetPath().AppendChild(_safe_name(block.GetName()))
    registry = UsdGeom.Xform.Define(stage, registry_path).GetPrim()
    registry.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalVizBlock")
    registry.CreateAttribute("aec:blockPath", Sdf.ValueTypeNames.String).Set(block.GetPath().pathString)
    registry.CreateRelationship("aec:block").SetTargets([block.GetPath()])
    block.CreateRelationship("aec:thermalVizRegistry").SetTargets([registry.GetPath()])
    added.append("thermalviz_registry")
    return registry


def _ensure_thermalviz_root(stage):
    UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/Building"))
    root = UsdGeom.Xform.Define(stage, THERMAL_VIZ_ROOT).GetPrim()
    root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalViz")
    return root


def _thermalviz_registry_prim(stage, block):
    rel = block.GetRelationship("aec:thermalVizRegistry")
    for target in rel.GetTargets() if rel else []:
        prim = stage.GetPrimAtPath(target)
        if prim and prim.IsValid():
            block_rel = prim.GetRelationship("aec:block")
            if block_rel and block.GetPath() in block_rel.GetTargets():
                return prim
    blocks_root = stage.GetPrimAtPath(THERMAL_VIZ_ROOT.AppendChild("Blocks"))
    if not blocks_root or not blocks_root.IsValid():
        return None
    for prim in blocks_root.GetChildren():
        block_rel = prim.GetRelationship("aec:block")
        if block_rel and block.GetPath() in block_rel.GetTargets():
            block.CreateRelationship("aec:thermalVizRegistry").SetTargets([prim.GetPath()])
            return prim
    return None


def _has_energy_metadata(block) -> bool:
    return all(_attr(block, name, None) is not None for name in THERMAL_METADATA_ATTRS)


def _has_thermal_material(stage, block) -> bool:
    rel = block.GetRelationship("aec:thermalMaterial")
    if rel and rel.GetTargets():
        return True
    for prim in Usd.PrimRange(block):
        rel = prim.GetRelationship("aec:thermalMaterial")
        if rel and rel.GetTargets():
            return True
    return False


def _has_spaces(stage, block) -> bool:
    spaces_root = stage.GetPrimAtPath(block.GetPath().AppendChild("Spaces"))
    if not spaces_root or not spaces_root.IsValid():
        return False
    return any(_attr(prim, "aec:type", "") == "Space" for prim in Usd.PrimRange(spaces_root))


def _attr(prim, name: str, default=None):
    attr = prim.GetAttribute(name)
    if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
        value = attr.Get()
        return default if value is None else value
    return default


def _safe_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(name or "Block"))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"Block_{cleaned or '01'}"
    return cleaned
