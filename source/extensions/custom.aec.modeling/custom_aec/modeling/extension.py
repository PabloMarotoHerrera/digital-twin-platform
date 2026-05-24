import asyncio

import carb
import omni.ext
import omni.kit.app
import omni.kit.commands
import omni.kit.menu.utils
import omni.ui as ui
import omni.usd
from custom_aec.extrude.mesh_builder import extrude_closed_curve_to_mesh
from custom_aec.primitive_mesh.mesh_builder import SUPPORTED_PRIMITIVES, create_or_update_primitive_mesh
from omni.curve.manipulator.bindings import CurveEditingModeType
from omni.curve.manipulator.scripts.bezier_curve_edits_context import BezierCurveEditsContextManager
from omni.kit.menu.utils import MenuItemDescription
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .opening_specs import create_opening_spec, read_opening_specs, update_opening_spec
from .partition_specs import create_partition_spec, ensure_aec_container, read_partition_specs
from . import api as aec_api
from .rebuild import rebuild_block
from .rebuild_polygon import rebuild_block_for_footprint


BUILDING_PATH = Sdf.Path("/World/Building")
SKETCHES_PATH = BUILDING_PATH.AppendPath("Sketches")
DEFAULT_RECT_PATH = SKETCHES_PATH.AppendPath("Rect_01").pathString
DEFAULT_LINEAR_PATH = SKETCHES_PATH.AppendPath("LineSketch_01").pathString
DEFAULT_BLOCK_PATH = "/World/Building/Block_01"
DEFAULT_PRIMITIVE_PATH = "/World/Building/Block_01"


class AecModelingExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._window = None
        self._primitive_index = 0
        self._opening_index = 0
        self._partition_index = 0
        self._menu_items = [
            MenuItemDescription(name="AEC/Modelling", onclick_fn=self._show_window)
        ]
        omni.kit.menu.utils.add_menu_items(self._menu_items, "Window")
        carb.log_info("[AEC Modelling] startup")

    def on_shutdown(self):
        if self._menu_items:
            omni.kit.menu.utils.remove_menu_items(self._menu_items, "Window")
            self._menu_items = None
        self._window = None
        carb.log_info("[AEC Modelling] shutdown")

    def _show_window(self):
        if self._window is None:
            self._build_window()
        self._window.visible = True

    def _build_window(self):
        self._window = ui.Window("AEC Modelling", width=460, height=760)
        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=10, height=0):
                    ui.Label("AEC Modelling", style={"font_size": 20})
                    ui.Label("MVP-safe sketch, block, opening, and validation tools.")

                    with ui.CollapsableFrame("Sketch", collapsed=False):
                        with ui.VStack(spacing=6, height=0):
                            self._rect_width_model = self._float_row("Rect Width X (m)", 10.0)
                            self._rect_depth_model = self._float_row("Rect Depth Y (m)", 6.0)
                            self._rect_path_model = self._string_row("Rect Path", DEFAULT_RECT_PATH)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Rectangle Sketch", width=190, clicked_fn=self._create_rectangle_sketch)

                            ui.Spacer(height=4)
                            self._line_path_model = self._string_row("Linear Sketch Path", DEFAULT_LINEAR_PATH)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Draw Linear Sketch", width=190, clicked_fn=self._draw_linear_sketch)

                    with ui.CollapsableFrame("Extrude", collapsed=False):
                        with ui.VStack(spacing=6, height=0):
                            self._extrude_height_model = self._float_row("Height Z (m)", 3.0)
                            self._extrude_path_model = self._string_row("Block Path", DEFAULT_BLOCK_PATH)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Extrude Selected Sketch", width=190, clicked_fn=self._extrude_selected)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Update Selected Block", width=190, clicked_fn=self._update_selected_block)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Regenerate Surfaces", width=190, clicked_fn=self._regenerate_selected_block)

                    with ui.CollapsableFrame("Primitive Block", collapsed=False):
                        with ui.VStack(spacing=6, height=0):
                            with ui.HStack():
                                ui.Label("Primitive", width=135)
                                primitive_model = ui.ComboBox(0, *SUPPORTED_PRIMITIVES).model
                                primitive_model.add_item_changed_fn(self._on_primitive_changed)

                            self._primitive_width_model = self._float_row("Width X (m)", 10.0)
                            self._primitive_depth_model = self._float_row("Depth Y (m)", 6.0)
                            self._primitive_height_model = self._float_row("Height Z (m)", 3.0)
                            self._primitive_segments_model = self._int_row("Segments", 16)
                            self._primitive_path_model = self._string_row("Block Path", DEFAULT_PRIMITIVE_PATH)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Primitive Block", width=190, clicked_fn=self._create_primitive_block)

                    with ui.CollapsableFrame("Partitions", collapsed=True):
                        with ui.VStack(spacing=6, height=0):
                            ui.Label("Select a block, then create a simple local partition.")
                            with ui.HStack():
                                ui.Label("Orientation", width=135)
                                partition_model = ui.ComboBox(0, "Across X", "Across Y").model
                                partition_model.add_item_changed_fn(self._on_partition_changed)
                            self._partition_offset_model = self._float_row("Offset (0..1)", 0.5)
                            self._partition_height_model = self._float_row("Height (m)", 3.0)
                            self._partition_thickness_model = self._float_row("Thickness (m)", 0.10)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Partition in Selected Block", width=270, clicked_fn=self._create_partition)

                    with ui.CollapsableFrame("Openings", collapsed=False):
                        with ui.VStack(spacing=6, height=0):
                            ui.Label("Select a wall surface, then create an opening.")
                            with ui.HStack():
                                ui.Label("Opening Type", width=135)
                                opening_model = ui.ComboBox(0, "Window", "Door").model
                                opening_model.add_item_changed_fn(self._on_opening_changed)

                            self._opening_width_model = self._float_row("Width (m)", 1.2)
                            self._opening_height_model = self._float_row("Height (m)", 1.2)
                            self._opening_sill_model = self._float_row("Sill / Bottom Z (m)", 1.0)
                            self._opening_offset_model = self._float_row("Horizontal Offset (m)", 0.0)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Opening on Selected Wall", width=230, clicked_fn=self._create_opening)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Opening Sketch on Selected Wall", width=250, clicked_fn=self._create_opening_sketch)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Create Opening from Selected Sketch", width=250, clicked_fn=self._create_opening_from_sketch)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Update Selected Opening", width=210, clicked_fn=self._update_selected_opening)

                    with ui.CollapsableFrame("Check Model", collapsed=True):
                        with ui.VStack(spacing=6, height=0):
                            ui.Label("Basic checks before the next MVP stage.")
                            self._check_result_model = ui.SimpleStringModel("Not checked yet.")
                            ui.Label("", model=self._check_result_model)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Check Model", width=160, clicked_fn=self._check_model)

    def _float_row(self, label, value):
        with ui.HStack():
            ui.Label(label, width=135)
            field = ui.FloatField()
            field.model.set_value(value)
            return field.model

    def _int_row(self, label, value):
        with ui.HStack():
            ui.Label(label, width=135)
            field = ui.IntField()
            field.model.set_value(value)
            return field.model

    def _string_row(self, label, value):
        with ui.HStack():
            ui.Label(label, width=135)
            field = ui.StringField()
            field.model.set_value(value)
            return field.model

    def _on_primitive_changed(self, model, _item):
        self._primitive_index = model.get_item_value_model().as_int

    def _on_opening_changed(self, model, _item):
        self._opening_index = model.get_item_value_model().as_int

    def _on_partition_changed(self, model, _item):
        self._partition_index = model.get_item_value_model().as_int

    def _create_rectangle_sketch(self):
        stage = self._get_stage()
        if stage is None:
            return

        rect_path = self._next_free_path(stage, self._model_path(self._rect_path_model, DEFAULT_RECT_PATH))
        half_width = max(self._rect_width_model.get_value_as_float(), 0.001) * 0.5
        half_depth = max(self._rect_depth_model.get_value_as_float(), 0.001) * 0.5
        surface_basis = self._selected_surface_basis(stage)
        if surface_basis:
            center = (
                surface_basis["bottom_left"]
                + surface_basis["h_dir"] * (surface_basis["width"] * 0.5)
                + surface_basis["v_dir"] * (surface_basis["height"] * 0.5)
            )
            points = [
                center - surface_basis["h_dir"] * half_width - surface_basis["v_dir"] * half_depth,
                center + surface_basis["h_dir"] * half_width - surface_basis["v_dir"] * half_depth,
                center + surface_basis["h_dir"] * half_width + surface_basis["v_dir"] * half_depth,
                center - surface_basis["h_dir"] * half_width + surface_basis["v_dir"] * half_depth,
            ]
        else:
            points = [
                Gf.Vec3f(-half_width, -half_depth, 0.0),
                Gf.Vec3f(half_width, -half_depth, 0.0),
                Gf.Vec3f(half_width, half_depth, 0.0),
                Gf.Vec3f(-half_width, half_depth, 0.0),
            ]
        curve = self._define_curve(rect_path, points, UsdGeom.Tokens.periodic)
        self._apply_aec_metadata(
            curve.GetPrim(),
            {
                "type": "Sketch",
                "sketchKind": "Rectangle",
                "closed": True,
                "width": half_width * 2.0,
                "depth": half_depth * 2.0,
            },
        )
        self._select(curve.GetPrim().GetPath().pathString)
        asyncio.ensure_future(self._enter_curve_editing([curve.GetPrim().GetPath().pathString], switch_to_edit=True))
        carb.log_info(f"[AEC Modeling] Created rectangle sketch at {rect_path}")

    def _draw_linear_sketch(self):
        stage = self._get_stage()
        if stage is None:
            return

        line_path = self._next_free_path(stage, self._model_path(self._line_path_model, DEFAULT_LINEAR_PATH))
        surface_basis = self._selected_surface_basis(stage)
        if surface_basis:
            center = (
                surface_basis["bottom_left"]
                + surface_basis["h_dir"] * (surface_basis["width"] * 0.5)
                + surface_basis["v_dir"] * (surface_basis["height"] * 0.5)
            )
            points = [
                center - surface_basis["h_dir"] * 0.5,
                center + surface_basis["h_dir"] * 0.5,
            ]
        else:
            points = []
        curve = self._define_curve(line_path, points, UsdGeom.Tokens.nonperiodic)
        self._apply_aec_metadata(curve.GetPrim(), {"type": "Sketch", "sketchKind": "Linear", "closed": False})
        self._select(curve.GetPrim().GetPath().pathString)
        asyncio.ensure_future(self._enter_curve_editing([curve.GetPrim().GetPath().pathString], switch_to_edit=False))
        carb.log_info(f"[AEC Modeling] Started linear sketch at {line_path}")

    def _extrude_selected(self):
        stage = self._get_stage()
        if stage is None:
            return

        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            carb.log_warn("[AEC Modeling] Select a closed sketch before extruding.")
            return

        curve_prim = stage.GetPrimAtPath(selection[0])
        if not curve_prim or not curve_prim.IsValid() or not curve_prim.IsA(UsdGeom.BasisCurves):
            carb.log_warn(f"[AEC Modeling] Selection is not a BasisCurves prim: {selection[0]}")
            return

        curve = UsdGeom.BasisCurves(curve_prim)
        if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
            carb.log_warn("[AEC Modeling] Only closed curves with wrap=periodic can be extruded.")
            return

        output_path = self._next_free_path(stage, self._model_path(self._extrude_path_model, DEFAULT_BLOCK_PATH))
        height = max(self._extrude_height_model.get_value_as_float(), 0.001)
        try:
            native_result = aec_api.extrude_sketch_to_block(stage, curve_prim.GetPath(), height=height, block_path=output_path)
            prim = native_result["block"]
            rebuild = native_result["rebuild"]
            rebuild_note = f"with {rebuild['mode']} AEC rebuild"
            for warning in rebuild.get("warnings") or []:
                carb.log_warn(f"[AEC Modeling] {warning}")
            aec_api.prepare_block_for_energy_model(stage, updated.GetPath())
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Extrude failed: {exc}")
            return

        self._select(prim.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Extruded {curve_prim.GetPath()} to {prim.GetPath()} ({rebuild_note})")

    def _update_selected_block(self):
        stage = self._get_stage()
        if stage is None:
            return

        block = self._selected_or_ancestor(stage, "Block")
        if block is None:
            carb.log_warn("[AEC Modeling] Select a block or one of its children before updating.")
            return

        try:
            updated = self._update_block(stage, block)
            rebuild = rebuild_block_for_footprint(
                stage,
                updated.GetPath(),
                rebuild_partitions=True,
                rebuild_spaces=True,
                rebuild_surfaces=True,
            )
            for warning in rebuild.get("warnings") or []:
                carb.log_warn(f"[AEC Modeling] {warning}")
            aec_api.prepare_block_for_energy_model(stage, block.GetPath())
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Block update failed: {exc}")
            return

        self._select(updated.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Updated block at {updated.GetPath()}")

    def _regenerate_selected_block(self):
        stage = self._get_stage()
        if stage is None:
            return

        block = self._selected_or_ancestor(stage, "Block")
        if block is None:
            carb.log_warn("[AEC Modeling] Select a block before regenerating surfaces.")
            return

        try:
            self._regenerate_block_surfaces(stage, block)
            rebuild = rebuild_block_for_footprint(
                stage,
                block.GetPath(),
                rebuild_partitions=True,
                rebuild_spaces=True,
                rebuild_surfaces=True,
            )
            for warning in rebuild.get("warnings") or []:
                carb.log_warn(f"[AEC Modeling] {warning}")
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Surface regeneration failed: {exc}")
            return

        self._select(block.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Regenerated surfaces for {block.GetPath()}")

    def _create_primitive_block(self):
        stage = self._get_stage()
        if stage is None:
            return

        primitive_type = SUPPORTED_PRIMITIVES[self._primitive_index]
        block_path = self._next_free_path(stage, self._model_path(self._primitive_path_model, DEFAULT_PRIMITIVE_PATH))
        width = max(self._primitive_width_model.get_value_as_float(), 0.001)
        depth = max(self._primitive_depth_model.get_value_as_float(), 0.001)
        height = max(self._primitive_height_model.get_value_as_float(), 0.001)
        segments = max(self._primitive_segments_model.get_value_as_int(), 1)
        block_prim = self._define_primitive_block_hierarchy(stage, Sdf.Path(block_path), primitive_type)
        mass_path = block_prim.GetPath().AppendPath("Mass/PrimitiveMesh")
        prim = create_or_update_primitive_mesh(
            stage=stage,
            prim_path=mass_path.pathString,
            primitive_type=primitive_type,
            width=width,
            depth=depth,
            height=height,
            segments=segments,
        )

        prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Mass")
        UsdGeom.Imageable(prim).MakeInvisible()
        self._set_display_color(prim, "Mass")
        self._apply_aec_metadata(
            block_prim,
            {
                "type": "Block",
                "blockKind": "Primitive",
                "primitiveType": primitive_type,
                "width": width,
                "depth": depth,
                "height": height,
                "segments": segments,
            },
        )
        if primitive_type == "Box":
            self._define_box_surfaces(stage, block_prim.GetPath(), width, depth, height)
        rebuild_block(stage, block_prim.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=True)
        aec_api.prepare_block_for_energy_model(stage, block_prim.GetPath())
        self._select(block_prim.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Created {primitive_type} block at {block_prim.GetPath()}")

    def _create_partition(self):
        stage = self._get_stage()
        if stage is None:
            return

        block = self._selected_or_ancestor(stage, "Block")
        if block is None:
            carb.log_warn("[AEC Modeling] Select a block before creating a partition.")
            return

        try:
            orientation = "Across X" if self._partition_index == 0 else "Across Y"
            spec = create_partition_spec(
                stage,
                block,
                orientation,
                self._partition_offset_model.get_value_as_float(),
                max(self._partition_height_model.get_value_as_float(), 0.001),
                max(self._partition_thickness_model.get_value_as_float(), 0.001),
            )
            rebuild_block(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=False)
            partition = self._partition_for_spec(stage, block, spec)
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Partition creation failed: {exc}")
            return

        if partition:
            self._select(partition.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Created partition spec at {spec.GetPath()}")

    def _create_opening(self):
        stage = self._get_stage()
        if stage is None:
            return

        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            carb.log_warn("[AEC Modeling] Select a wall surface before creating an opening.")
            return

        wall_prim = stage.GetPrimAtPath(selection[0])
        if not wall_prim or not wall_prim.IsValid() or not wall_prim.IsA(UsdGeom.Mesh):
            carb.log_warn(f"[AEC Modeling] Selection is not a wall mesh: {selection[0]}")
            return

        surface_type = wall_prim.GetAttribute("aec:surfaceType").Get()
        if surface_type != "Wall":
            carb.log_warn(f"[AEC Modeling] Selected surface is not a Wall: {selection[0]}")
            return

        opening_type = "Window" if self._opening_index == 0 else "Door"
        width = max(self._opening_width_model.get_value_as_float(), 0.001)
        height = max(self._opening_height_model.get_value_as_float(), 0.001)
        sill = max(self._opening_sill_model.get_value_as_float(), 0.0)
        offset = self._opening_offset_model.get_value_as_float()

        try:
            block = self._selected_or_ancestor(stage, "Block")
            if block is None:
                carb.log_warn("[AEC Modeling] Could not find parent block for selected wall.")
                return
            spec = create_opening_spec(stage, block, wall_prim, opening_type, width, height, sill, offset)
            rebuild_block(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=False)
            opening_prim = self._opening_for_spec(stage, block, spec)
            if opening_prim is None:
                raise ValueError(f"Opening was not rebuilt from spec: {spec.GetPath()}")
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Opening creation failed: {exc}")
            return

        self._select(opening_prim.GetPath().pathString)
        carb.log_info(
            f"[AEC Modeling] Created {opening_type} at {opening_prim.GetPath()} "
            f"on {wall_prim.GetPath()}"
        )

    def _create_opening_sketch(self):
        stage = self._get_stage()
        if stage is None:
            return

        wall_prim = self._selected_wall(stage)
        if wall_prim is None:
            return

        opening_type = "Window" if self._opening_index == 0 else "Door"
        width = max(self._opening_width_model.get_value_as_float(), 0.001)
        height = max(self._opening_height_model.get_value_as_float(), 0.001)
        sill = max(self._opening_sill_model.get_value_as_float(), 0.0)
        offset = self._opening_offset_model.get_value_as_float()

        try:
            points = self._opening_points_on_wall(wall_prim, width, height, sill, offset)
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Opening sketch creation failed: {exc}")
            return

        sketches_parent_path = wall_prim.GetPath().AppendPath("OpeningSketches")
        sketches_parent = UsdGeom.Xform.Define(stage, sketches_parent_path).GetPrim()
        sketches_parent.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("OpeningSketches")
        sketch_path = omni.usd.get_stage_next_free_path(
            stage,
            sketches_parent_path.AppendPath("OpeningSketch_01").pathString,
            False,
        )

        curve = self._define_curve(sketch_path, points, UsdGeom.Tokens.periodic)
        curve_prim = curve.GetPrim()
        curve_prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("OpeningSketch")
        curve_prim.CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(opening_type)
        curve_prim.CreateRelationship("aec:hostSurface").SetTargets([wall_prim.GetPath()])
        self._select(curve_prim.GetPath().pathString)
        asyncio.ensure_future(self._enter_curve_editing([curve_prim.GetPath().pathString], switch_to_edit=True))
        carb.log_info(f"[AEC Modeling] Created {opening_type} sketch at {curve_prim.GetPath()}")

    def _create_opening_from_sketch(self):
        stage = self._get_stage()
        if stage is None:
            return

        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            carb.log_warn("[AEC Modeling] Select a closed opening sketch before creating an opening.")
            return

        curve_prim = stage.GetPrimAtPath(selection[0])
        if not curve_prim or not curve_prim.IsValid() or not curve_prim.IsA(UsdGeom.BasisCurves):
            carb.log_warn(f"[AEC Modeling] Selection is not a BasisCurves sketch: {selection[0]}")
            return

        curve = UsdGeom.BasisCurves(curve_prim)
        if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
            carb.log_warn("[AEC Modeling] Opening sketches must be closed curves with wrap=periodic.")
            return

        wall_prim = self._host_wall_for_sketch(stage, curve_prim)
        if wall_prim is None:
            carb.log_warn("[AEC Modeling] Could not find a host wall for the selected opening sketch.")
            return

        try:
            opening_prim = self._define_opening_from_sketch(stage, wall_prim, curve_prim)
            block = self._ancestor_from_prim(stage, wall_prim, "Block")
            if block:
                spec = create_opening_spec(
                    stage,
                    block,
                    wall_prim,
                    self._attr_value(opening_prim, "aec:openingType", "Window"),
                    float(self._attr_value(opening_prim, "aec:width", 1.2)),
                    float(self._attr_value(opening_prim, "aec:height", 1.2)),
                    float(self._attr_value(opening_prim, "aec:sillHeight", 1.0)),
                    float(self._attr_value(opening_prim, "aec:horizontalOffset", 0.0)),
                )
                rebuild_block(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=False)
                rebuilt_opening = self._opening_for_spec(stage, block, spec)
                if rebuilt_opening:
                    opening_prim = rebuilt_opening
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Opening from sketch failed: {exc}")
            return

        self._select(opening_prim.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Created opening from {curve_prim.GetPath()} at {opening_prim.GetPath()}")

    def _update_selected_opening(self):
        stage = self._get_stage()
        if stage is None:
            return

        opening = self._selected_or_ancestor(stage, "Opening")
        if opening is None:
            carb.log_warn("[AEC Modeling] Select an opening before updating.")
            return

        rel = opening.GetRelationship("aec:hostSurface")
        targets = rel.GetTargets() if rel else []
        if not targets:
            carb.log_warn(f"[AEC Modeling] Opening has no host surface: {opening.GetPath()}")
            return

        wall_prim = stage.GetPrimAtPath(targets[0])
        if not wall_prim or not wall_prim.IsValid():
            carb.log_warn(f"[AEC Modeling] Opening host surface is missing: {targets[0]}")
            return

        opening_type = self._attr_value(opening, "aec:openingType", "Window")
        width = float(self._attr_value(opening, "aec:width", self._opening_width_model.get_value_as_float()))
        height = float(self._attr_value(opening, "aec:height", self._opening_height_model.get_value_as_float()))
        sill = float(self._attr_value(opening, "aec:sillHeight", self._opening_sill_model.get_value_as_float()))
        offset = float(self._attr_value(opening, "aec:horizontalOffset", self._opening_offset_model.get_value_as_float()))

        try:
            block = self._selected_or_ancestor(stage, "Block")
            if block is None:
                carb.log_warn("[AEC Modeling] Could not find parent block for selected opening.")
                return
            spec = self._spec_for_opening(stage, opening)
            if spec is None:
                spec = create_opening_spec(stage, block, wall_prim, opening_type, width, height, sill, offset)
            else:
                update_opening_spec(stage, spec, block, wall_prim, opening_type, width, height, sill, offset)
            rebuild_block(stage, block.GetPath(), rebuild_partitions=True, rebuild_spaces=True, rebuild_surfaces=False)
            updated = self._opening_for_spec(stage, block, spec)
            if updated is None:
                raise ValueError(f"Opening was not rebuilt from spec: {spec.GetPath()}")
        except Exception as exc:
            carb.log_warn(f"[AEC Modeling] Opening update failed: {exc}")
            return

        self._select(updated.GetPath().pathString)
        carb.log_info(f"[AEC Modeling] Updated opening at {updated.GetPath()}")

    def _check_model(self):
        stage = self._get_stage()
        if stage is None:
            return

        issues = []
        building = stage.GetPrimAtPath(BUILDING_PATH)
        if not building or not building.IsValid():
            issues.append("Missing /World/Building.")
        else:
            for prim in Usd.PrimRange(building):
                aec_type = self._attr_value(prim, "aec:type", "")
                if aec_type == "Block":
                    if self._attr_value(prim, "aec:schemaVersion", "") and self._attr_value(prim, "aec:schemaVersion", "") != "mvp-1":
                        issues.append(f"{prim.GetPath()} has unexpected schema version.")
                    if not stage.GetPrimAtPath(prim.GetPath().AppendPath("Spaces/Space_01")).IsValid():
                        issues.append(f"{prim.GetPath()} has no Space_01.")
                    if not stage.GetPrimAtPath(prim.GetPath().AppendPath("Mass")).IsValid():
                        issues.append(f"{prim.GetPath()} has no Mass container.")
                    if not self._block_has_mass_mesh(stage, prim):
                        issues.append(f"{prim.GetPath()} has no Mass/BlockMesh or Mass/PrimitiveMesh mesh.")
                    if self._attr_value(prim, "aec:blockKind", "") == "Extruded":
                        self._check_block_source_curve(stage, prim, issues)
                    specs = read_partition_specs(stage, prim)
                    expected_spaces = self._expected_space_count(specs)
                    actual_spaces = self._actual_space_count(stage, prim)
                    if actual_spaces != expected_spaces:
                        issues.append(
                            f"{prim.GetPath()} has {actual_spaces} spaces but specs require {expected_spaces}."
                        )
                    for spec in specs:
                        offset = float(spec["offset_normalized"])
                        if offset <= 0.0 or offset >= 1.0:
                            issues.append(f"{spec['path']} offset should be inside the block, not on its boundary.")
                        partition_path = self._attr_value(spec["prim"], "aec:partitionPrimPath", "")
                        if partition_path and not stage.GetPrimAtPath(partition_path).IsValid():
                            issues.append(f"{spec['path']} points to missing partition mesh: {partition_path}")
                    for opening_spec in read_opening_specs(stage, prim):
                        host = stage.GetPrimAtPath(opening_spec["host_surface"])
                        if not host.IsValid():
                            issues.append(
                                f"{opening_spec['path']} host surface is missing: {opening_spec['host_surface']}"
                            )
                        elif self._attr_value(host, "aec:type", "") != "Surface":
                            issues.append(f"{opening_spec['path']} host is not an AEC Surface: {host.GetPath()}")
                        if self._opening_for_spec(stage, prim, opening_spec["prim"]) is None:
                            issues.append(f"{opening_spec['path']} has no generated Opening under its host surface.")
                elif aec_type == "Surface":
                    if not prim.GetAttribute("aec:surfaceType").Get():
                        issues.append(f"{prim.GetPath()} has no aec:surfaceType.")
                    if not prim.GetRelationship("aec:space").GetTargets():
                        issues.append(f"{prim.GetPath()} is not linked to a space.")
                    if self._attr_value(prim, "aec:surfaceType", "") == "Wall":
                        for attr_name in ("aec:basisOrigin", "aec:basisHDir", "aec:basisVDir", "aec:basisWidth", "aec:basisHeight"):
                            if not self._has_authored_attr(prim, attr_name):
                                issues.append(f"{prim.GetPath()} wall is missing {attr_name}.")
                elif aec_type == "Space":
                    surfaces_path = prim.GetPath().AppendPath("Surfaces")
                    surfaces = stage.GetPrimAtPath(surfaces_path)
                    if not prim.GetRelationship("aec:block").GetTargets():
                        issues.append(f"{prim.GetPath()} is not linked to a block.")
                    if not self._has_authored_attr(prim, "aec:boundsMin") or not self._has_authored_attr(prim, "aec:boundsMax"):
                        issues.append(f"{prim.GetPath()} is missing bounds metadata.")
                    if not surfaces or not surfaces.IsValid():
                        issues.append(f"{prim.GetPath()} has no Surfaces container.")
                    else:
                        for surface_name in ("Floor", "Ceiling", "Wall_XMin", "Wall_XMax", "Wall_YMin", "Wall_YMax"):
                            surface = stage.GetPrimAtPath(surfaces_path.AppendPath(surface_name))
                            if not surface.IsValid():
                                issues.append(f"{prim.GetPath()} is missing {surface_name}.")
                            elif self._attr_value(surface, "aec:type", "") != "Surface":
                                issues.append(f"{surface.GetPath()} exists but is not marked as Surface.")
                elif aec_type == "Opening":
                    host_targets = prim.GetRelationship("aec:hostSurface").GetTargets()
                    spec_targets = prim.GetRelationship("aec:spec").GetTargets()
                    if not host_targets:
                        issues.append(f"{prim.GetPath()} has no host surface.")
                    elif not stage.GetPrimAtPath(host_targets[0]).IsValid():
                        issues.append(f"{prim.GetPath()} host surface is missing: {host_targets[0]}")
                    if not spec_targets:
                        issues.append(f"{prim.GetPath()} has no OpeningSpec relationship.")
                    elif not stage.GetPrimAtPath(spec_targets[0]).IsValid():
                        issues.append(f"{prim.GetPath()} OpeningSpec target is missing: {spec_targets[0]}")
                    panel = stage.GetPrimAtPath(prim.GetPath().AppendPath("Panel"))
                    if not panel.IsValid() or not panel.IsA(UsdGeom.Mesh):
                        issues.append(f"{prim.GetPath()} has no mesh Panel.")
                elif aec_type == "Partition":
                    spec_targets = prim.GetRelationship("aec:spec").GetTargets()
                    if not spec_targets:
                        issues.append(f"{prim.GetPath()} has no PartitionSpec relationship.")
                    elif not stage.GetPrimAtPath(spec_targets[0]).IsValid():
                        issues.append(f"{prim.GetPath()} PartitionSpec target is missing: {spec_targets[0]}")
                    if not prim.GetRelationship("aec:block").GetTargets():
                        issues.append(f"{prim.GetPath()} is not linked to a block.")
                elif aec_type in ("Sketch", "OpeningSketch"):
                    if prim.IsA(UsdGeom.BasisCurves):
                        curve = UsdGeom.BasisCurves(prim)
                        if self._attr_value(prim, "aec:closed", None) is True:
                            if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
                                issues.append(f"{prim.GetPath()} is marked closed but wrap is not periodic.")
                        if self._attr_value(prim, "aec:closed", None) is True:
                            counts = curve.GetCurveVertexCountsAttr().Get() or []
                            if not counts or int(counts[0]) < 3:
                                issues.append(f"{prim.GetPath()} is a closed sketch with fewer than 3 vertices.")
                    if aec_type == "OpeningSketch" and not prim.GetRelationship("aec:hostSurface").GetTargets():
                        issues.append(f"{prim.GetPath()} has no host surface.")

        if issues:
            message = f"{len(issues)} issue(s). See Console."
            for issue in issues:
                carb.log_warn(f"[AEC Modeling][Check] {issue}")
        else:
            message = "OK: model hierarchy and MVP metadata look valid."
            carb.log_info("[AEC Modeling][Check] OK")

        if getattr(self, "_check_result_model", None):
            self._check_result_model.set_value(message)

    def _get_stage(self):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            carb.log_warn("[AEC Modeling] No open stage was found.")
            return None

        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
        building = UsdGeom.Xform.Define(stage, BUILDING_PATH).GetPrim()
        building.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Building")
        building.CreateAttribute("aec:schemaVersion", Sdf.ValueTypeNames.String).Set("mvp-1")
        sketches = UsdGeom.Xform.Define(stage, SKETCHES_PATH).GetPrim()
        sketches.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Sketches")
        return stage

    def _define_primitive_block_hierarchy(self, stage, block_path, primitive_type):
        block = UsdGeom.Xform.Define(stage, block_path).GetPrim()
        ensure_aec_container(stage, block_path)
        self._apply_aec_metadata(
            block,
            {
                "type": "Block",
                "blockKind": "Primitive",
                "primitiveType": primitive_type,
            },
        )

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
        stage.GetPrimAtPath(block_path.AppendPath("Spaces/Space_01")).CreateAttribute(
            "aec:name", Sdf.ValueTypeNames.String
        ).Set("Space_01")
        return block

    def _define_box_surfaces(self, stage, block_path, width, depth, height):
        half_width = width * 0.5
        half_depth = depth * 0.5
        base = [
            Gf.Vec3f(-half_width, -half_depth, 0.0),
            Gf.Vec3f(half_width, -half_depth, 0.0),
            Gf.Vec3f(half_width, half_depth, 0.0),
            Gf.Vec3f(-half_width, half_depth, 0.0),
        ]
        top = [Gf.Vec3f(point[0], point[1], height) for point in base]
        surfaces_path = block_path.AppendPath("Spaces/Space_01/Surfaces")

        surface_defs = [
            ("Floor", "Floor", [base[3], base[2], base[1], base[0]], Gf.Vec3f(0.0, 0.0, -1.0)),
            ("Ceiling", "Ceiling", top, Gf.Vec3f(0.0, 0.0, 1.0)),
            ("Wall_Front", "Wall", [base[0], base[1], top[1], top[0]], Gf.Vec3f(0.0, -1.0, 0.0)),
            ("Wall_Right", "Wall", [base[1], base[2], top[2], top[1]], Gf.Vec3f(1.0, 0.0, 0.0)),
            ("Wall_Back", "Wall", [base[2], base[3], top[3], top[2]], Gf.Vec3f(0.0, 1.0, 0.0)),
            ("Wall_Left", "Wall", [base[3], base[0], top[0], top[3]], Gf.Vec3f(-1.0, 0.0, 0.0)),
        ]
        for name, surface_type, points, normal in surface_defs:
            surface = self._define_surface_mesh(
                stage,
                surfaces_path.AppendPath(name),
                points,
                surface_type,
                normal,
            )
            if surface_type == "Wall":
                openings = UsdGeom.Xform.Define(stage, surface.GetPath().AppendPath("Openings")).GetPrim()
                openings.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Openings")

    def _define_surface_mesh(self, stage, path, points, surface_type, normal):
        mesh = UsdGeom.Mesh.Define(stage, path)
        mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))
        mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([len(points)]))
        mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(list(range(len(points)))))
        mesh.GetNormalsAttr().Set(Vt.Vec3fArray([normal] * len(points)))
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
        mesh.CreateSubdivisionSchemeAttr().Set("none")
        st_primvar = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar(
            "st",
            Sdf.ValueTypeNames.TexCoord2fArray,
            UsdGeom.Tokens.faceVarying,
        )
        st_primvar.Set(Vt.Vec2fArray(self._surface_sts(points)))
        extent = UsdGeom.Boundable.ComputeExtentFromPlugins(mesh, Usd.TimeCode.Default())
        if extent:
            mesh.GetExtentAttr().Set(extent)

        prim = mesh.GetPrim()
        prim.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Surface")
        prim.CreateAttribute("aec:surfaceType", Sdf.ValueTypeNames.String).Set(surface_type)
        prim.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set(self._thermal_boundary(surface_type))
        self._set_display_color(prim, surface_type)
        self._link_surface_to_space(prim)
        return prim

    def _define_opening_on_wall(self, stage, wall_prim, opening_type, width, height, sill, offset):
        points = self._opening_points_on_wall(wall_prim, width, height, sill, offset)
        wall_basis = self._wall_basis(wall_prim)
        wall_width = wall_basis["width"]
        clamped_width = min(width, max(wall_width - 0.05, 0.001))
        clamped_height = min(height, max(wall_basis["height"] - sill - 0.05, 0.001))
        return self._define_opening_panel(
            stage,
            wall_prim,
            opening_type,
            points,
            clamped_width,
            clamped_height,
            sill,
            offset,
        )

    def _define_opening_from_sketch(self, stage, wall_prim, curve_prim):
        points = self._curve_points_in_wall_space(curve_prim, wall_prim)
        if len(points) < 4:
            raise ValueError("Opening sketch needs at least four points.")

        wall_basis = self._wall_basis(wall_prim)
        origin = wall_basis["bottom_left"]
        h_dir = wall_basis["h_dir"]
        v_dir = wall_basis["v_dir"]
        normal = wall_basis["normal"]

        projected = [(Gf.Dot(point - origin, h_dir), Gf.Dot(point - origin, v_dir)) for point in points]
        min_u = min(item[0] for item in projected)
        max_u = max(item[0] for item in projected)
        min_v = min(item[1] for item in projected)
        max_v = max(item[1] for item in projected)
        width = max(max_u - min_u, 0.001)
        height = max(max_v - min_v, 0.001)
        offset = ((min_u + max_u) * 0.5) - (wall_basis["width"] * 0.5)
        sill = max(min_v, 0.0)
        opening_type_attr = curve_prim.GetAttribute("aec:openingType")
        opening_type = opening_type_attr.Get() if opening_type_attr and opening_type_attr.IsValid() else "Window"
        if not opening_type:
            opening_type = "Window"

        panel_points = [
            origin + h_dir * min_u + v_dir * min_v + normal * 0.01,
            origin + h_dir * max_u + v_dir * min_v + normal * 0.01,
            origin + h_dir * max_u + v_dir * max_v + normal * 0.01,
            origin + h_dir * min_u + v_dir * max_v + normal * 0.01,
        ]
        opening = self._define_opening_panel(
            stage,
            wall_prim,
            opening_type,
            panel_points,
            width,
            height,
            sill,
            offset,
        )
        opening.CreateRelationship("aec:sourceSketch").SetTargets([curve_prim.GetPath()])
        return opening

    def _opening_points_on_wall(self, wall_prim, width, height, sill, offset):
        wall_basis = self._wall_basis(wall_prim)
        h_dir = wall_basis["h_dir"]
        v_dir = wall_basis["v_dir"]
        normal = wall_basis["normal"]
        wall_width = wall_basis["width"]
        wall_height = wall_basis["height"]
        clamped_width = min(width, max(wall_width - 0.05, 0.001))
        clamped_height = min(height, max(wall_height - sill - 0.05, 0.001))
        center_on_bottom = wall_basis["bottom_left"] + h_dir * (wall_width * 0.5 + offset)
        bottom_center = center_on_bottom + v_dir * sill + normal * 0.01

        p0 = bottom_center - h_dir * (clamped_width * 0.5)
        p1 = bottom_center + h_dir * (clamped_width * 0.5)
        p2 = p1 + v_dir * clamped_height
        p3 = p0 + v_dir * clamped_height
        return [p0, p1, p2, p3]

    def _wall_basis(self, wall_prim):
        authored = self._authored_surface_basis(wall_prim)
        if authored is not None:
            return authored

        wall_points = self._mesh_points(wall_prim)
        if len(wall_points) < 4:
            raise ValueError("Wall mesh needs at least four points.")

        bottom_left = wall_points[0]
        bottom_right = wall_points[1]
        top_left = wall_points[3]
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

    def _selected_surface_basis(self, stage):
        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            return None
        prim = stage.GetPrimAtPath(selection[0])
        if not prim or not prim.IsValid() or not prim.IsA(UsdGeom.Mesh):
            return None
        if self._attr_value(prim, "aec:type", "") != "Surface":
            return None
        return self._wall_basis(prim)

    def _authored_surface_basis(self, surface):
        origin_attr = surface.GetAttribute("aec:basisOrigin")
        h_attr = surface.GetAttribute("aec:basisHDir")
        v_attr = surface.GetAttribute("aec:basisVDir")
        normal_attr = surface.GetAttribute("aec:basisNormal")
        width_attr = surface.GetAttribute("aec:basisWidth")
        height_attr = surface.GetAttribute("aec:basisHeight")
        attrs = [origin_attr, h_attr, v_attr, normal_attr, width_attr, height_attr]
        if not all(attr and attr.IsValid() and attr.HasAuthoredValueOpinion() for attr in attrs):
            return None

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
            "bottom_left": Gf.Vec3f(origin_attr.Get()),
            "h_dir": h_dir,
            "v_dir": v_dir,
            "normal": normal,
            "width": float(width_attr.Get()),
            "height": float(height_attr.Get()),
        }

    def _define_opening_panel(self, stage, wall_prim, opening_type, points, width, height, sill, offset, opening_path=None):
        openings_parent_path = wall_prim.GetPath().AppendPath("Openings")
        openings_parent = UsdGeom.Xform.Define(stage, openings_parent_path).GetPrim()
        openings_parent.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Openings")
        if opening_path is None:
            opening_path = Sdf.Path(
                omni.usd.get_stage_next_free_path(
                    stage,
                    openings_parent_path.AppendPath(f"{opening_type}_01").pathString,
                    False,
                )
            )
        elif isinstance(opening_path, str):
            opening_path = Sdf.Path(opening_path)

        opening = UsdGeom.Xform.Define(stage, opening_path).GetPrim()
        opening.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Opening")
        opening.CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(opening_type)
        opening.CreateAttribute("aec:width", Sdf.ValueTypeNames.Float).Set(float(width))
        opening.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(height))
        opening.CreateAttribute("aec:sillHeight", Sdf.ValueTypeNames.Float).Set(float(sill))
        opening.CreateAttribute("aec:horizontalOffset", Sdf.ValueTypeNames.Float).Set(float(offset))
        opening.CreateAttribute("aec:thermalBoundary", Sdf.ValueTypeNames.String).Set("SubSurface")
        opening.CreateRelationship("aec:hostSurface").SetTargets([wall_prim.GetPath()])

        opening_frame = self._opening_frame_from_points(points)
        self._set_xform_matrix(opening, opening_frame["matrix"])

        panel = UsdGeom.Mesh.Define(stage, Sdf.Path(opening_path).AppendPath("Panel"))
        panel.GetPointsAttr().Set(Vt.Vec3fArray(opening_frame["local_points"]))
        panel.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
        panel.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))
        panel.GetNormalsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(0.0, 0.0, 1.0)] * 4))
        panel.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
        panel.CreateSubdivisionSchemeAttr().Set("none")
        panel.CreateDoubleSidedAttr().Set(True)
        panel.CreateDisplayColorAttr().Set(Vt.Vec3fArray([self._opening_color(opening_type)]))
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
        panel.GetPrim().CreateAttribute("aec:openingType", Sdf.ValueTypeNames.String).Set(opening_type)
        return opening

    def _opening_frame_from_points(self, points):
        if len(points) < 4:
            raise ValueError("Opening panel needs four points.")

        p0 = Gf.Vec3d(points[0])
        p1 = Gf.Vec3d(points[1])
        p2 = Gf.Vec3d(points[2])
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

        center = (p0 + p1 + p2 + p3) * 0.25
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

    def _set_xform_matrix(self, prim, matrix):
        xformable = UsdGeom.Xformable(prim)
        xformable.ClearXformOpOrder()
        xformable.AddTransformOp().Set(matrix)

    def _update_block(self, stage, block):
        block_kind = self._attr_value(block, "aec:blockKind", "")
        if block_kind == "Primitive":
            primitive_type = self._attr_value(block, "aec:primitiveType", "Box")
            width = float(self._attr_value(block, "aec:width", self._primitive_width_model.get_value_as_float()))
            depth = float(self._attr_value(block, "aec:depth", self._primitive_depth_model.get_value_as_float()))
            height = self._current_block_height(
                block,
                float(self._attr_value(block, "aec:height", self._primitive_height_model.get_value_as_float())),
            )
            segments = int(self._attr_value(block, "aec:segments", self._primitive_segments_model.get_value_as_int()))
            mass_path = block.GetPath().AppendPath("Mass/PrimitiveMesh")
            mass = create_or_update_primitive_mesh(stage, mass_path.pathString, primitive_type, width, depth, height, segments)
            mass.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Mass")
            UsdGeom.Imageable(mass).MakeInvisible()
            self._set_display_color(mass, "Mass")
            self._apply_aec_metadata(
                block,
                {
                    "type": "Block",
                    "blockKind": "Primitive",
                    "primitiveType": primitive_type,
                    "width": width,
                    "depth": depth,
                    "height": height,
                    "segments": segments,
                },
            )
            if primitive_type == "Box":
                self._define_box_surfaces(stage, block.GetPath(), width, depth, height)
            return block

        rel = block.GetRelationship("aec:sourceCurveRel")
        targets = rel.GetTargets() if rel else []
        if not targets:
            raise ValueError("Block has no source curve relationship.")
        curve_prim = stage.GetPrimAtPath(targets[0])
        if not curve_prim or not curve_prim.IsValid():
            raise ValueError(f"Source curve is missing: {targets[0]}")
        height = self._current_block_height(
            block,
            float(self._attr_value(block, "aec:height", self._extrude_height_model.get_value_as_float())),
        )
        return extrude_closed_curve_to_mesh(stage, curve_prim, block.GetPath().pathString, height)

    def _current_block_height(self, block, fallback):
        for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
            mesh_prim = block.GetStage().GetPrimAtPath(block.GetPath().AppendPath(relative))
            if not mesh_prim or not mesh_prim.IsValid() or not mesh_prim.IsA(UsdGeom.Mesh):
                continue
            points = UsdGeom.Mesh(mesh_prim).GetPointsAttr().Get() or []
            if not points:
                continue
            mesh_to_world = UsdGeom.Xformable(mesh_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            z_values = [float(mesh_to_world.Transform(Gf.Vec3d(point))[2]) for point in points]
            height = max(z_values) - min(z_values)
            if height > 1e-6:
                return float(height)
        return max(float(fallback), 0.001)

    def _block_uses_rectangular_rebuild(self, stage, block):
        block_kind = self._attr_value(block, "aec:blockKind", "")
        if block_kind == "Primitive":
            return True
        targets = block.GetRelationship("aec:sourceCurveRel").GetTargets()
        if not targets:
            return True
        curve_prim = stage.GetPrimAtPath(targets[0])
        if not curve_prim or not curve_prim.IsValid() or not curve_prim.IsA(UsdGeom.BasisCurves):
            return False
        return self._curve_is_rectangular_footprint(curve_prim)

    def _curve_is_rectangular_footprint(self, curve_prim):
        curve = UsdGeom.BasisCurves(curve_prim)
        if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
            return False
        points = curve.GetPointsAttr().Get() or []
        counts = curve.GetCurveVertexCountsAttr().Get() or []
        vertex_count = int(counts[0]) if counts else len(points)
        if vertex_count != 4 or len(points) < vertex_count:
            return False

        curve_to_world = UsdGeom.Xformable(curve_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        world_points = [
            Gf.Vec3f(curve_to_world.Transform(Gf.Vec3d(points[index])))
            for index in range(vertex_count)
        ]
        return self._points_form_rectangle(world_points)

    def _points_form_rectangle(self, points):
        if len(points) != 4 or not self._points_are_horizontal(points):
            return False
        edges = [points[(index + 1) % 4] - points[index] for index in range(4)]
        lengths = [edge.GetLength() for edge in edges]
        if any(length <= 1e-5 for length in lengths):
            return False
        dot01 = abs(self._dot(self._normalized(edges[0]), self._normalized(edges[1])))
        dot12 = abs(self._dot(self._normalized(edges[1]), self._normalized(edges[2])))
        opposite0 = abs(lengths[0] - lengths[2]) <= 1e-4
        opposite1 = abs(lengths[1] - lengths[3]) <= 1e-4
        return dot01 <= 1e-4 and dot12 <= 1e-4 and opposite0 and opposite1

    def _points_are_horizontal(self, points):
        if not points:
            return False
        z0 = float(points[0][2])
        return all(abs(float(point[2]) - z0) <= 1e-5 for point in points)

    def _normalized(self, vector):
        length = vector.GetLength()
        if length <= 1e-8:
            return Gf.Vec3f(0.0, 0.0, 0.0)
        return Gf.Vec3f(float(vector[0]) / length, float(vector[1]) / length, float(vector[2]) / length)

    def _dot(self, left, right):
        return float(left[0]) * float(right[0]) + float(left[1]) * float(right[1]) + float(left[2]) * float(right[2])

    def _regenerate_block_surfaces(self, stage, block):
        block_kind = self._attr_value(block, "aec:blockKind", "")
        if block_kind == "Primitive":
            primitive_type = self._attr_value(block, "aec:primitiveType", "Box")
            if primitive_type != "Box":
                raise ValueError("Surface regeneration is currently supported for Box primitive blocks.")
            self._define_box_surfaces(
                stage,
                block.GetPath(),
                float(self._attr_value(block, "aec:width", 10.0)),
                float(self._attr_value(block, "aec:depth", 6.0)),
                float(self._attr_value(block, "aec:height", 3.0)),
            )
            return
        self._update_block(stage, block)

    def _define_partition_in_block(self, stage, block, orientation_index, offset, height, thickness):
        bounds = self._block_local_bounds(stage, block)
        min_x, min_y, min_z = bounds["min"]
        max_x, max_y, max_z = bounds["max"]
        partition_height = min(height, max(max_z - min_z, 0.001))
        if orientation_index == 0:
            x0, x1 = min_x, max_x
            y0, y1 = offset, offset
        else:
            x0, x1 = offset, offset
            y0, y1 = min_y, max_y

        z0 = min_z
        z1 = min_z + partition_height
        points = [
            Gf.Vec3f(x0, y0, z0),
            Gf.Vec3f(x1, y1, z0),
            Gf.Vec3f(x1, y1, z1),
            Gf.Vec3f(x0, y0, z1),
        ]
        parent_path = block.GetPath().AppendPath("Partitions")
        parent = UsdGeom.Xform.Define(stage, parent_path).GetPrim()
        parent.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Partitions")
        partition_path = Sdf.Path(
            omni.usd.get_stage_next_free_path(
                stage,
                parent_path.AppendPath("Partition_01").pathString,
                False,
            )
        )
        normal = Gf.Vec3f(0.0, -1.0, 0.0) if orientation_index == 0 else Gf.Vec3f(1.0, 0.0, 0.0)
        partition = self._define_surface_mesh(stage, partition_path, points, "Partition", normal)
        partition.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Partition")
        partition.CreateAttribute("aec:height", Sdf.ValueTypeNames.Float).Set(float(partition_height))
        partition.CreateAttribute("aec:thickness", Sdf.ValueTypeNames.Float).Set(float(thickness))
        partition.CreateAttribute("aec:horizontalOffset", Sdf.ValueTypeNames.Float).Set(float(offset))
        partition.CreateRelationship("aec:block").SetTargets([block.GetPath()])
        self._set_display_color(partition, "Partition")
        return partition

    def _partition_for_spec(self, stage, block, spec):
        spec_path = spec.GetPath()
        partitions = stage.GetPrimAtPath(block.GetPath().AppendPath("Partitions"))
        if not partitions or not partitions.IsValid():
            return None

        for child in partitions.GetChildren():
            rel = child.GetRelationship("aec:spec")
            if rel and spec_path in rel.GetTargets():
                return child
        return None

    def _opening_for_spec(self, stage, block, spec):
        spec_path = spec.GetPath()
        for opening in read_opening_specs(stage, block):
            if opening["path"] != spec_path:
                continue
            host = stage.GetPrimAtPath(opening["host_surface"])
            if not host or not host.IsValid():
                return None
            openings_parent = stage.GetPrimAtPath(host.GetPath().AppendPath("Openings"))
            if not openings_parent or not openings_parent.IsValid():
                return None
            for child in openings_parent.GetChildren():
                rel = child.GetRelationship("aec:spec")
                if rel and spec_path in rel.GetTargets():
                    return child
        return None

    def _spec_for_opening(self, stage, opening):
        rel = opening.GetRelationship("aec:spec")
        targets = rel.GetTargets() if rel else []
        if not targets:
            return None
        spec = stage.GetPrimAtPath(targets[0])
        if spec and spec.IsValid() and self._attr_value(spec, "aec:type", "") == "OpeningSpec":
            return spec
        return None

    def _ancestor_from_prim(self, stage, prim, aec_type):
        path = prim.GetPath()
        while path != Sdf.Path.absoluteRootPath:
            current = stage.GetPrimAtPath(path)
            if current and current.IsValid() and self._attr_value(current, "aec:type", "") == aec_type:
                return current
            path = path.GetParentPath()
        return None

    def _expected_space_count(self, specs):
        x_cuts = 1
        y_cuts = 1
        for spec in specs:
            if spec["orientation"] == "Across Y":
                x_cuts += 1
            else:
                y_cuts += 1
        return max(x_cuts, 1) * max(y_cuts, 1)

    def _actual_space_count(self, stage, block):
        spaces = stage.GetPrimAtPath(block.GetPath().AppendPath("Spaces"))
        if not spaces or not spaces.IsValid():
            return 0
        return len(
            [
                child
                for child in spaces.GetChildren()
                if child.GetName().startswith("Space_") and self._attr_value(child, "aec:type", "") == "Space"
            ]
        )

    def _block_has_mass_mesh(self, stage, block):
        for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
            prim = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
            if prim and prim.IsValid() and prim.IsA(UsdGeom.Mesh):
                return True
        return False

    def _check_block_source_curve(self, stage, block, issues):
        targets = block.GetRelationship("aec:sourceCurveRel").GetTargets()
        if not targets:
            issues.append(f"{block.GetPath()} has no source curve relationship.")
            return

        curve_prim = stage.GetPrimAtPath(targets[0])
        if not curve_prim or not curve_prim.IsValid():
            issues.append(f"{block.GetPath()} source curve is missing: {targets[0]}")
            return
        if not curve_prim.IsA(UsdGeom.BasisCurves):
            issues.append(f"{block.GetPath()} source curve is not BasisCurves: {targets[0]}")
            return

        curve = UsdGeom.BasisCurves(curve_prim)
        if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
            issues.append(f"{block.GetPath()} source curve is not closed with wrap=periodic.")
        counts = curve.GetCurveVertexCountsAttr().Get() or []
        if not counts or int(counts[0]) < 3:
            issues.append(f"{block.GetPath()} source curve has fewer than 3 vertices.")

    def _has_authored_attr(self, prim, attr_name):
        attr = prim.GetAttribute(attr_name)
        return bool(attr and attr.IsValid() and attr.HasAuthoredValueOpinion())

    def _block_local_bounds(self, stage, block):
        mesh = None
        for relative in ("Mass/BlockMesh", "Mass/PrimitiveMesh"):
            candidate = stage.GetPrimAtPath(block.GetPath().AppendPath(relative))
            if candidate and candidate.IsValid() and candidate.IsA(UsdGeom.Mesh):
                mesh = candidate
                break
        if mesh is None:
            raise ValueError("Block has no mass mesh for bounds.")

        points = self._mesh_points(mesh)
        if not points:
            raise ValueError("Block mass mesh has no points.")
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        zs = [float(point[2]) for point in points]
        return {"min": (min(xs), min(ys), min(zs)), "max": (max(xs), max(ys), max(zs))}

    def _selected_or_ancestor(self, stage, aec_type):
        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            return None
        path = Sdf.Path(selection[0])
        while path != Sdf.Path.absoluteRootPath:
            prim = stage.GetPrimAtPath(path)
            if prim and prim.IsValid() and self._attr_value(prim, "aec:type", "") == aec_type:
                return prim
            path = path.GetParentPath()
        return None

    def _apply_aec_metadata(self, prim, values):
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

    def _attr_value(self, prim, attr_name, default):
        attr = prim.GetAttribute(attr_name)
        if attr and attr.IsValid() and attr.HasAuthoredValueOpinion():
            value = attr.Get()
            return default if value is None else value
        return default

    def _set_display_color(self, prim, kind):
        if not prim or not prim.IsValid():
            return
        color = self._display_color(kind)
        UsdGeom.Gprim(prim).CreateDisplayColorAttr().Set(Vt.Vec3fArray([color]))

    def _display_color(self, kind):
        colors = {
            "Mass": Gf.Vec3f(0.56, 0.56, 0.56),
            "Floor": Gf.Vec3f(0.42, 0.42, 0.42),
            "Ceiling": Gf.Vec3f(0.68, 0.68, 0.68),
            "Wall": Gf.Vec3f(0.50, 0.50, 0.50),
            "Partition": Gf.Vec3f(0.70, 0.62, 0.35),
        }
        return colors.get(kind, Gf.Vec3f(0.55, 0.55, 0.55))

    def _thermal_boundary(self, surface_type):
        if surface_type in ("Floor", "Ceiling", "Wall"):
            return "Exterior"
        if surface_type == "Partition":
            return "Interior"
        return "Unknown"

    def _link_surface_to_space(self, surface_prim):
        path = surface_prim.GetPath()
        while path != Sdf.Path.absoluteRootPath:
            prim = surface_prim.GetStage().GetPrimAtPath(path)
            if prim and prim.IsValid() and self._attr_value(prim, "aec:type", "") == "Space":
                surface_prim.CreateRelationship("aec:space").SetTargets([prim.GetPath()])
                return
            path = path.GetParentPath()

    def _selected_wall(self, stage):
        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if not selection:
            carb.log_warn("[AEC Modeling] Select a wall surface first.")
            return None

        wall_prim = stage.GetPrimAtPath(selection[0])
        if not wall_prim or not wall_prim.IsValid() or not wall_prim.IsA(UsdGeom.Mesh):
            carb.log_warn(f"[AEC Modeling] Selection is not a wall mesh: {selection[0]}")
            return None

        surface_type = wall_prim.GetAttribute("aec:surfaceType").Get()
        if surface_type != "Wall":
            carb.log_warn(f"[AEC Modeling] Selected surface is not a Wall: {selection[0]}")
            return None
        return wall_prim

    def _host_wall_for_sketch(self, stage, curve_prim):
        rel = curve_prim.GetRelationship("aec:hostSurface")
        if rel:
            targets = rel.GetTargets()
            if targets:
                wall_prim = stage.GetPrimAtPath(targets[0])
                if wall_prim and wall_prim.IsValid() and wall_prim.IsA(UsdGeom.Mesh):
                    return wall_prim

        path = curve_prim.GetPath().GetParentPath()
        while path != Sdf.Path.absoluteRootPath:
            prim = stage.GetPrimAtPath(path)
            if prim and prim.IsValid() and prim.IsA(UsdGeom.Mesh):
                if prim.GetAttribute("aec:surfaceType").Get() == "Wall":
                    return prim
            path = path.GetParentPath()
        return None

    def _curve_points_in_wall_space(self, curve_prim, wall_prim):
        curve = UsdGeom.BasisCurves(curve_prim)
        points = curve.GetPointsAttr().Get() or []
        curve_to_world = UsdGeom.Xformable(curve_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        wall_to_world = UsdGeom.Xformable(wall_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        world_to_wall = wall_to_world.GetInverse()
        return [
            Gf.Vec3f(world_to_wall.Transform(curve_to_world.Transform(Gf.Vec3d(point))))
            for point in points
        ]

    def _mesh_points(self, prim):
        mesh = UsdGeom.Mesh(prim)
        points = mesh.GetPointsAttr().Get() or []
        return [Gf.Vec3f(point) for point in points]

    def _opening_color(self, opening_type):
        if opening_type == "Door":
            return Gf.Vec3f(0.55, 0.30, 0.12)
        return Gf.Vec3f(0.25, 0.55, 0.90)

    def _surface_sts(self, points):
        return [
            Gf.Vec2f(0.0, 0.0),
            Gf.Vec2f(1.0, 0.0),
            Gf.Vec2f(1.0, 1.0),
            Gf.Vec2f(0.0, 1.0),
        ][: len(points)]

    def _define_curve(self, path, points, wrap):
        stage = omni.usd.get_context().get_stage()
        curve = UsdGeom.BasisCurves.Define(stage, path)
        curve.GetTypeAttr().Set(UsdGeom.Tokens.linear)
        curve.GetWrapAttr().Set(wrap)
        curve.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
        curve.GetCurveVertexCountsAttr().Set(Vt.IntArray([len(points)] if points else []))
        curve.GetPointsAttr().Set(Vt.Vec3fArray(points))
        self._remove_widths_if_present(curve)
        self._set_draw_wireframe(path, True)
        self._recompute_extent(curve)
        return curve

    def _remove_widths_if_present(self, curve):
        prim = curve.GetPrim()
        if prim.HasProperty("widths"):
            prim.RemoveProperty("widths")

    def _set_draw_wireframe(self, path, value):
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path(path).AppendProperty("omni:scene:visualization:drawWireframe"),
            value=value,
            prev=None,
            type_to_create_if_not_exist=Sdf.ValueTypeNames.Bool,
        )

    def _recompute_extent(self, curve):
        extent = UsdGeom.Boundable.ComputeExtentFromPlugins(curve, Usd.TimeCode.Default())
        if extent:
            curve.GetExtentAttr().Set(extent)

    async def _enter_curve_editing(self, paths, switch_to_edit):
        await omni.kit.app.get_app().next_update_async()
        curve_context = BezierCurveEditsContextManager.get_context().curve_edits.curve_context
        omni.kit.commands.execute(
            "EnableCurveEditing",
            curve_context=curve_context,
            paths=paths,
            mode=CurveEditingModeType.DRAG,
        )
        carb.log_info("[AEC Modeling] EnableCurveEditing executed")

        if switch_to_edit:
            await omni.kit.app.get_app().next_update_async()
            carb.log_info("[AEC Modeling] Curve editor kept in DRAG mode; EDIT is unavailable in this Kit build")

    def _select(self, path):
        omni.usd.get_context().get_selection().set_selected_prim_paths([path], True)

    def _model_path(self, model, default_path):
        path = model.get_value_as_string().strip() or default_path
        if not path.startswith("/"):
            path = "/" + path

        sdf_path = Sdf.Path(path)
        if not sdf_path.IsAbsolutePath() or sdf_path.IsPropertyPath():
            carb.log_warn(f"[AEC Modeling] Invalid path, using {default_path}: {path}")
            return default_path
        return path

    def _next_free_path(self, stage, path):
        return omni.usd.get_stage_next_free_path(stage, path, False)
