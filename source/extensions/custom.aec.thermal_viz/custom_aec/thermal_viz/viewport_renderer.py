from __future__ import annotations

import hashlib

import carb
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt

from .model_access import SpaceInfo
from .signals import ThermalSignal
from .thermal_style import ComfortBand, comfort_color_vec3, comfort_delta


COLOR_MODE_SURFACES = "Color surfaces"
COLOR_MODE_PROXIES = "Thermal overlay"
THERMAL_PROXY_NAME = "ThermalProxy"
THERMAL_ROOT_PATH = Sdf.Path("/World/Building/_ThermalViz")


class ThermalViewportRenderer:
    def __init__(self):
        self._original_colors: dict[str, object] = {}
        self._original_opacities: dict[str, object] = {}
        self._original_bindings: dict[str, list[Sdf.Path] | None] = {}
        self._proxy_paths: set[Sdf.Path] = set()
        self._active_mode: str | None = None

    def clear(self, stage: Usd.Stage):
        if stage is None:
            return
        self._restore_surface_bindings(stage)
        self._restore_surface_colors(stage)
        self._remove_proxies(stage)
        if stage.GetPrimAtPath(THERMAL_ROOT_PATH).IsValid():
            stage.RemovePrim(THERMAL_ROOT_PATH)
        self._active_mode = None

    def apply(
        self,
        stage: Usd.Stage,
        spaces: list[SpaceInfo],
        signals: dict[str, ThermalSignal],
        hour: float,
        mode: str,
        comfort: ComfortBand,
        selected_space_path: str | None = None,
    ) -> int:
        if stage is None:
            return 0

        if not spaces:
            self.clear(stage)
            return 0

        values = {
            space.path: _value_at_hour(signals[space.path], hour)
            for space in spaces
            if space.path in signals
        }
        if not values:
            self.clear(stage)
            return 0

        if self._active_mode is not None and self._active_mode != mode:
            self.clear(stage)

        if mode == COLOR_MODE_PROXIES:
            count = self._apply_proxy_colors(stage, spaces, values, comfort, selected_space_path)
        else:
            count = self._apply_surface_colors(stage, spaces, values, comfort, selected_space_path)

        self._active_mode = mode
        carb.log_info(f"[AEC Thermal] Applied viewport heatmap mode={mode} hour={hour:.2f} count={count}")
        return count

    def _apply_surface_colors(
        self,
        stage: Usd.Stage,
        spaces: list[SpaceInfo],
        values: dict[str, float],
        comfort: ComfortBand,
        selected_space_path: str | None,
    ) -> int:
        count = 0
        self._remove_proxies(stage)
        materials_root = UsdGeom.Xform.Define(stage, THERMAL_ROOT_PATH.AppendChild("Materials")).GetPrim()
        materials_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalMaterials")
        for space in spaces:
            value = values.get(space.path)
            if value is None:
                continue
            color = comfort_color_vec3(value, comfort)
            severity = _thermal_severity(value, comfort)
            opacity = _surface_opacity(severity, space.path == selected_space_path)
            emissive = _emissive_color(color, severity, selected=(space.path == selected_space_path))
            for path in space.surface_paths:
                prim = stage.GetPrimAtPath(path)
                if not prim.IsValid() or not prim.IsA(UsdGeom.Gprim):
                    continue
                self._remember_original_binding(prim)
                material = _define_preview_surface_material(stage, prim, color, emissive, opacity, severity)
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
                count += 1
        return count

    def _apply_proxy_colors(
        self,
        stage: Usd.Stage,
        spaces: list[SpaceInfo],
        values: dict[str, float],
        comfort: ComfortBand,
        selected_space_path: str | None,
    ) -> int:
        root = UsdGeom.Xform.Define(stage, THERMAL_ROOT_PATH).GetPrim()
        root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalViz")
        self._apply_neutral_shell(stage, spaces)
        materials_root = UsdGeom.Xform.Define(stage, THERMAL_ROOT_PATH.AppendChild("ProxyMaterials")).GetPrim()
        materials_root.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalProxyMaterials")

        count = 0
        for space in spaces:
            value = values.get(space.path)
            if value is None or space.bounds_min is None or space.bounds_max is None:
                continue
            proxy_path = Sdf.Path(space.path).AppendPath(THERMAL_PROXY_NAME)
            stage.RemovePrim(proxy_path)
            mesh = _define_box_mesh(stage, proxy_path, space.bounds_min, space.bounds_max, inset=0.14)
            prim = mesh.GetPrim()
            prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalProxy")
            prim.CreateAttribute("aec:spacePath", Sdf.ValueTypeNames.String).Set(space.path)
            color = _overlay_proxy_color(value, comfort, selected=(space.path == selected_space_path))
            severity = _thermal_severity(value, comfort)
            opacity = _proxy_opacity(severity, selected=(space.path == selected_space_path))
            emissive = _proxy_emissive(color, severity, selected=(space.path == selected_space_path))
            _set_display_color(prim, color, opacity)
            glow_path = proxy_path.AppendChild("GlowShell")
            stage.RemovePrim(glow_path)
            glow_mesh = _define_box_mesh(stage, glow_path, space.bounds_min, space.bounds_max, inset=0.09)
            glow_prim = glow_mesh.GetPrim()
            glow_prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("ThermalGlowShell")
            glow_opacity = _proxy_glow_opacity(severity, selected=(space.path == selected_space_path))
            glow_material = _define_proxy_glow_material(stage, glow_prim, color, emissive, glow_opacity)
            UsdShade.MaterialBindingAPI.Apply(glow_prim).Bind(glow_material)
            self._proxy_paths.add(proxy_path)
            self._proxy_paths.add(glow_path)
            count += 1
        return count

    def _apply_neutral_shell(self, stage: Usd.Stage, spaces: list[SpaceInfo]):
        seen: set[str] = set()
        blocks: set[str] = set()
        for space in spaces:
            if space.block_path:
                blocks.add(space.block_path)
            for path in space.surface_paths:
                if path in seen:
                    continue
                seen.add(path)
                prim = stage.GetPrimAtPath(path)
                if not prim.IsValid() or not prim.IsA(UsdGeom.Gprim):
                    continue
                self._remember_original_binding(prim)
                material = _define_shell_material(stage, prim)
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
        for block_path in sorted(blocks):
            partitions_root = stage.GetPrimAtPath(Sdf.Path(block_path).AppendChild("Partitions"))
            if not partitions_root.IsValid():
                continue
            for prim in Usd.PrimRange(partitions_root):
                if prim == partitions_root or not prim.IsA(UsdGeom.Mesh):
                    continue
                prim_path = prim.GetPath().pathString
                if prim_path in seen:
                    continue
                seen.add(prim_path)
                self._remember_original_binding(prim)
                material = _define_shell_material(stage, prim)
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)

    def _remember_original(self, prim: Usd.Prim):
        path = prim.GetPath().pathString
        if path not in self._original_colors:
            attr = UsdGeom.Gprim(prim).GetDisplayColorAttr()
            self._original_colors[path] = attr.Get() if attr and attr.HasAuthoredValueOpinion() else None
        if path not in self._original_opacities:
            attr = UsdGeom.Gprim(prim).GetDisplayOpacityAttr()
            self._original_opacities[path] = attr.Get() if attr and attr.HasAuthoredValueOpinion() else None

    def _remember_original_binding(self, prim: Usd.Prim):
        path = prim.GetPath().pathString
        if path in self._original_bindings:
            return
        rel = UsdShade.MaterialBindingAPI.Apply(prim).GetDirectBindingRel()
        self._original_bindings[path] = list(rel.GetTargets()) if rel and rel.HasAuthoredTargets() else None

    def _restore_surface_colors(self, stage: Usd.Stage):
        for path, value in list(self._original_colors.items()):
            prim = stage.GetPrimAtPath(path)
            if not prim.IsValid() or not prim.IsA(UsdGeom.Gprim):
                continue
            attr = UsdGeom.Gprim(prim).GetDisplayColorAttr()
            if value is None:
                attr.Clear()
            else:
                attr.Set(value)

        for path, value in list(self._original_opacities.items()):
            prim = stage.GetPrimAtPath(path)
            if not prim.IsValid() or not prim.IsA(UsdGeom.Gprim):
                continue
            attr = UsdGeom.Gprim(prim).GetDisplayOpacityAttr()
            if value is None:
                attr.Clear()
            else:
                attr.Set(value)

        self._original_colors.clear()
        self._original_opacities.clear()

    def _restore_surface_bindings(self, stage: Usd.Stage):
        for path, targets in list(self._original_bindings.items()):
            prim = stage.GetPrimAtPath(path)
            if not prim.IsValid():
                continue
            rel = UsdShade.MaterialBindingAPI.Apply(prim).GetDirectBindingRel()
            if targets:
                rel.SetTargets(targets)
            else:
                rel.ClearTargets(False)
        self._original_bindings.clear()

    def _remove_proxies(self, stage: Usd.Stage):
        for path in list(self._proxy_paths):
            if stage.GetPrimAtPath(path).IsValid():
                stage.RemovePrim(path)
        self._proxy_paths.clear()


def _define_box_mesh(stage: Usd.Stage, path: Sdf.Path, min_point, max_point, inset: float = 0.0) -> UsdGeom.Mesh:
    min_x, min_y, min_z = (float(min_point[0]), float(min_point[1]), float(min_point[2]))
    max_x, max_y, max_z = (float(max_point[0]), float(max_point[1]), float(max_point[2]))
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    min_x += min(width * inset, width * 0.18)
    max_x -= min(width * inset, width * 0.18)
    min_y += min(depth * inset, depth * 0.18)
    max_y -= min(depth * inset, depth * 0.18)
    min_z += min(height * inset, height * 0.18)
    max_z -= min(height * inset, height * 0.18)
    points = [
        Gf.Vec3f(min_x, min_y, min_z),
        Gf.Vec3f(max_x, min_y, min_z),
        Gf.Vec3f(max_x, max_y, min_z),
        Gf.Vec3f(min_x, max_y, min_z),
        Gf.Vec3f(min_x, min_y, max_z),
        Gf.Vec3f(max_x, min_y, max_z),
        Gf.Vec3f(max_x, max_y, max_z),
        Gf.Vec3f(min_x, max_y, max_z),
    ]
    face_vertex_counts = [4, 4, 4, 4, 4, 4]
    face_vertex_indices = [
        0, 1, 2, 3,
        4, 7, 6, 5,
        0, 4, 5, 1,
        1, 5, 6, 2,
        2, 6, 7, 3,
        3, 7, 4, 0,
    ]

    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(face_vertex_counts))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(face_vertex_indices))
    mesh.GetExtentAttr().Set(Vt.Vec3fArray([Gf.Vec3f(min_x, min_y, min_z), Gf.Vec3f(max_x, max_y, max_z)]))
    return mesh


def _set_display_color(prim: Usd.Prim, color: Gf.Vec3f, opacity: float | None):
    gprim = UsdGeom.Gprim(prim)
    color_attr = gprim.CreateDisplayColorAttr()
    color_attr.SetMetadata("interpolation", "constant")
    color_attr.Set(Vt.Vec3fArray([color]))
    if opacity is not None:
        opacity_attr = gprim.CreateDisplayOpacityAttr()
        opacity_attr.SetMetadata("interpolation", "constant")
        opacity_attr.Set(Vt.FloatArray([float(opacity)]))


def _define_preview_surface_material(
    stage: Usd.Stage,
    prim: Usd.Prim,
    color: Gf.Vec3f,
    emissive: Gf.Vec3f,
    opacity: float,
    severity: float,
) -> UsdShade.Material:
    digest = hashlib.md5(prim.GetPath().pathString.encode("utf-8")).hexdigest()[:10]
    material_path = THERMAL_ROOT_PATH.AppendChild("Materials").AppendChild(f"{prim.GetName()}_{digest}")
    shader_path = material_path.AppendChild("PreviewSurface")

    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, shader_path)
    diffuse = _diffuse_overlay_color(color, severity)
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse)
    shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(emissive)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(float(opacity))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(max(0.08, 0.26 - severity * 0.12))
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.18)
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _define_proxy_glow_material(
    stage: Usd.Stage,
    prim: Usd.Prim,
    color: Gf.Vec3f,
    emissive: Gf.Vec3f,
    opacity: float,
) -> UsdShade.Material:
    digest = hashlib.md5((prim.GetPath().pathString + "_proxy_glow").encode("utf-8")).hexdigest()[:10]
    material_path = THERMAL_ROOT_PATH.AppendChild("ProxyMaterials").AppendChild(f"{prim.GetName()}_{digest}")
    shader_path = material_path.AppendChild("PreviewSurface")

    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.0, 0.0, 0.0))
    shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(_lerp_vec3(emissive, Gf.Vec3f(1.0, 1.0, 1.0), 0.18))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(float(opacity))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.02)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.0)
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _define_shell_material(stage: Usd.Stage, prim: Usd.Prim) -> UsdShade.Material:
    digest = hashlib.md5((prim.GetPath().pathString + "_shell").encode("utf-8")).hexdigest()[:10]
    material_path = THERMAL_ROOT_PATH.AppendChild("ProxyMaterials").AppendChild(f"{prim.GetName()}_shell_{digest}")
    shader_path = material_path.AppendChild("PreviewSurface")

    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.045, 0.065, 0.085))
    shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.0, 0.0, 0.0))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.10)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.28)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.0)
    shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _diffuse_overlay_color(color: Gf.Vec3f, severity: float) -> Gf.Vec3f:
    base = Gf.Vec3f(0.02, 0.035, 0.055)
    tint = 0.18 + severity * 0.16
    return Gf.Vec3f(
        base[0] + color[0] * tint,
        base[1] + color[1] * tint,
        base[2] + color[2] * tint,
    )


def _emissive_color(color: Gf.Vec3f, severity: float, selected: bool) -> Gf.Vec3f:
    boost = 0.85 + severity * 2.8 + (0.55 if selected else 0.0)
    return Gf.Vec3f(color[0] * boost, color[1] * boost, color[2] * boost)


def _surface_opacity(severity: float, selected: bool) -> float:
    base = 0.18 + severity * 0.34
    return min(0.88, base + (0.14 if selected else 0.0))


def _proxy_diffuse(color: Gf.Vec3f, severity: float) -> Gf.Vec3f:
    lift = 0.22 + severity * 0.10
    return _lerp_vec3(color, Gf.Vec3f(1.0, 1.0, 1.0), lift)


def _proxy_emissive(color: Gf.Vec3f, severity: float, selected: bool) -> Gf.Vec3f:
    boost = 1.35 + severity * 1.25 + (0.4 if selected else 0.0)
    return Gf.Vec3f(color[0] * boost, color[1] * boost, color[2] * boost)


def _proxy_opacity(severity: float, selected: bool) -> float:
    if selected:
        return min(0.035, 0.018 + severity * 0.012)
    return min(0.010, 0.003 + severity * 0.004)


def _proxy_glow_opacity(severity: float, selected: bool) -> float:
    if selected:
        return min(0.018, 0.008 + severity * 0.006)
    return min(0.005, 0.0015 + severity * 0.002)


def _overlay_proxy_color(value: float, comfort: ComfortBand, selected: bool) -> Gf.Vec3f:
    color = comfort_color_vec3(value, comfort)
    if selected:
        color = _lerp_vec3(color, Gf.Vec3f(1.0, 1.0, 1.0), 0.10)
    return color


def _lerp_vec3(left: Gf.Vec3f, right: Gf.Vec3f, t: float) -> Gf.Vec3f:
    t = max(0.0, min(1.0, t))
    return Gf.Vec3f(
        left[0] * (1.0 - t) + right[0] * t,
        left[1] * (1.0 - t) + right[1] * t,
        left[2] * (1.0 - t) + right[2] * t,
    )


def _thermal_severity(value: float, comfort: ComfortBand) -> float:
    delta = abs(comfort_delta(value, comfort))
    if delta > 0.0:
        return min(1.0, delta / 1.8)
    midpoint_span = max(0.25, (comfort.max_c - comfort.min_c) * 0.5)
    inside_offset = abs(value - comfort.midpoint)
    return min(0.45, inside_offset / midpoint_span * 0.45)


def _value_at_hour(signal: ThermalSignal, hour: float) -> float:
    timeline = signal.timeline_hours
    values = signal.temperature_c
    if not timeline or not values:
        return 0.0
    clamped = max(0.0, min(24.0, float(hour)))
    nearest = min(range(len(timeline)), key=lambda index: abs(timeline[index] - clamped))
    return float(values[nearest])
