import carb
import omni.ext
import omni.kit.menu.utils
import omni.ui as ui
import omni.usd
from omni.kit.menu.utils import MenuItemDescription
from pxr import Sdf, UsdGeom

from .mesh_builder import extrude_closed_curve_to_mesh


DEFAULT_HEIGHT_METERS = 3.0
DEFAULT_OUTPUT_PATH = "/World/Building/Block_01"


class AecExtrudeExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._window = None
        self._menu_items_window = None
        self._menu_items_create = None
        carb.log_info("[AEC Extrude] startup")

    def on_shutdown(self):
        if self._menu_items_window:
            omni.kit.menu.utils.remove_menu_items(self._menu_items_window, "Window")
            self._menu_items_window = None
        if self._menu_items_create:
            omni.kit.menu.utils.remove_menu_items(self._menu_items_create, "Create")
            self._menu_items_create = None
        self._window = None
        carb.log_info("[AEC Extrude] shutdown")

    def _show_window(self):
        if self._window is None:
            self._build_window()
        self._window.visible = True

    def _build_window(self):
        self._window = ui.Window("AEC Extrude", width=380, height=210)
        with self._window.frame:
            with ui.VStack(spacing=8, height=0):
                ui.Label("AEC Extrude", style={"font_size": 18})
                ui.Label("Select a closed BasisCurves sketch and create a mesh block.")

                with ui.HStack():
                    ui.Label("Height Z (m)", width=120)
                    height_field = ui.FloatField()
                    self._height_model = height_field.model
                    self._height_model.set_value(DEFAULT_HEIGHT_METERS)

                with ui.HStack():
                    ui.Label("Block Path", width=120)
                    path_field = ui.StringField()
                    self._path_model = path_field.model
                    self._path_model.set_value(DEFAULT_OUTPUT_PATH)

                with ui.HStack():
                    ui.Spacer()
                    ui.Button("Extrude Selected", width=150, clicked_fn=self._extrude_selected)

    def _extrude_selected(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        if stage is None:
            carb.log_warn("[AEC Extrude] No open stage was found.")
            return

        selection = usd_context.get_selection().get_selected_prim_paths()
        if not selection:
            carb.log_warn("[AEC Extrude] Select a closed BasisCurves sketch first.")
            return

        curve_prim = stage.GetPrimAtPath(selection[0])
        if not curve_prim or not curve_prim.IsValid() or not curve_prim.IsA(UsdGeom.BasisCurves):
            carb.log_warn(f"[AEC Extrude] Selection is not a BasisCurves prim: {selection[0]}")
            return

        curve = UsdGeom.BasisCurves(curve_prim)
        if curve.GetWrapAttr().Get() != UsdGeom.Tokens.periodic:
            carb.log_warn("[AEC Extrude] Only closed curves with wrap=periodic can be extruded.")
            return

        output_path = self._get_output_path()
        height = self._get_height()
        if height <= 0.0:
            carb.log_warn("[AEC Extrude] Height must be greater than zero.")
            return

        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
        building = UsdGeom.Xform.Define(stage, Sdf.Path("/World/Building")).GetPrim()
        building.CreateAttribute("aec:type", Sdf.ValueTypeNames.String).Set("Building")
        output_path = omni.usd.get_stage_next_free_path(stage, output_path, False)

        try:
            prim = extrude_closed_curve_to_mesh(stage, curve_prim, output_path, height)
        except Exception as exc:
            carb.log_warn(f"[AEC Extrude] Extrude failed: {exc}")
            return

        usd_context.get_selection().set_selected_prim_paths([prim.GetPath().pathString], True)
        carb.log_info(
            f"[AEC Extrude] Extruded {curve_prim.GetPath().pathString} "
            f"to {prim.GetPath().pathString} height={height}"
        )

    def _get_height(self):
        if self._window is None:
            return DEFAULT_HEIGHT_METERS
        return float(self._height_model.get_value_as_float())

    def _get_output_path(self):
        if self._window is None:
            return DEFAULT_OUTPUT_PATH

        output_path = self._path_model.get_value_as_string().strip() or DEFAULT_OUTPUT_PATH
        if not output_path.startswith("/"):
            output_path = "/" + output_path

        path = Sdf.Path(output_path)
        if not path.IsAbsolutePath() or path.IsPropertyPath():
            carb.log_warn(f"[AEC Extrude] Invalid output path, using {DEFAULT_OUTPUT_PATH}: {output_path}")
            return DEFAULT_OUTPUT_PATH

        return output_path
