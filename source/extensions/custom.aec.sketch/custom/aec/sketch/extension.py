import asyncio

import carb
import omni.ext
import omni.kit.app
import omni.kit.commands
import omni.kit.menu.utils
import omni.usd
from omni.curve.manipulator.bindings import CurveEditingModeType, CurvesEventType, get_interface
from omni.curve.manipulator.scripts.bezier_curve_edits_context import BezierCurveEditsContextManager
from omni.kit.menu.utils import MenuItemDescription
from pxr import Gf, Sdf, Usd, UsdGeom, Vt


RECT_PATH = Sdf.Path("/World/Sketches/Rect_01")
DRAW_WIREFRAME_ATTR = RECT_PATH.AppendProperty("omni:scene:visualization:drawWireframe")
DEFAULT_WIDTH_METERS = 10.0
DEFAULT_DEPTH_METERS = 6.0


class AecSketchExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._curve_manipulator = get_interface()
        self._curve_event_sub = None
        self._menu_items = None
        self._ensure_curve_event_subscription()

    def on_shutdown(self):
        if getattr(self, "_menu_items", None):
            omni.kit.menu.utils.remove_menu_items(self._menu_items, "Create")
            self._menu_items = None
        self._curve_event_sub = None
        self._curve_manipulator = None

    def _get_curve_context(self):
        return BezierCurveEditsContextManager.get_context().curve_edits.curve_context

    def _ensure_curve_event_subscription(self):
        if self._curve_event_sub is not None:
            return
        self._curve_event_sub = self._curve_manipulator.get_curves_event_stream(
            self._get_curve_context()
        ).create_subscription_to_pop(
            self._on_curve_event,
            name="custom.aec.sketch.curve_events",
        )

    def _on_curve_event(self, event):
        if event.type == int(CurvesEventType.END_CURVE_EDIT):
            carb.log_info("[AEC Sketch] END_CURVE_EDIT detected")
            asyncio.ensure_future(self._refresh_curve_after_done())

    def _remove_widths_if_present(self, rect_curve: UsdGeom.BasisCurves):
        rect_prim = rect_curve.GetPrim()
        if rect_prim.HasProperty("widths"):
            rect_prim.RemoveProperty("widths")

    def _recompute_extent_from_plugins(self, rect_curve: UsdGeom.BasisCurves):
        extent = UsdGeom.Boundable.ComputeExtentFromPlugins(
            rect_curve, Usd.TimeCode.Default()
        )
        if extent is None:
            carb.log_warn("[AEC Sketch] extent recompute returned None")
            return

        rect_curve.GetExtentAttr().Set(extent)
        carb.log_info(f"[AEC Sketch] extent recomputed: {list(extent)}")

    async def _refresh_curve_after_done(self):
        await omni.kit.app.get_app().next_update_async()
        stage = omni.usd.get_context().get_stage()
        if not stage:
            return

        rect_prim = stage.GetPrimAtPath(RECT_PATH)
        if not rect_prim or not rect_prim.IsValid():
            return

        rect_curve = UsdGeom.BasisCurves(rect_prim)
        self._recompute_extent_from_plugins(rect_curve)

        with Sdf.ChangeBlock():
            rect_prim.SetActive(False)
            rect_prim.SetActive(True)
        carb.log_info("[AEC Sketch] post-Done Hydra refresh executed")

    async def _enable_curve_editing(self, new_selection):
        await omni.kit.app.get_app().next_update_async()
        curve_context = self._get_curve_context()

        carb.log_info(
            f"[AEC Sketch] before EnableCurveEditing selection="
            f"{omni.usd.get_context().get_selection().get_selected_prim_paths()}"
        )
        carb.log_info(
            f"[AEC Sketch] before EnableCurveEditing prim={new_selection[0]}"
        )
        omni.kit.commands.execute(
            "EnableCurveEditing",
            curve_context=curve_context,
            paths=new_selection,
            mode=CurveEditingModeType.DRAG,
        )
        carb.log_info("[AEC Sketch] EnableCurveEditing executed")

        await omni.kit.app.get_app().next_update_async()

        edit_mode = getattr(CurveEditingModeType, "EDIT", None)
        if edit_mode is not None:
            omni.kit.commands.execute(
                "SetCurveEditingMode",
                curve_context=curve_context,
                mode=edit_mode,
            )
            carb.log_info("[AEC Sketch] SetCurveEditingMode EDIT executed")
        else:
            carb.log_info("[AEC Sketch] SetCurveEditingMode skipped; EDIT is unavailable in this Kit build")

        await omni.kit.app.get_app().next_update_async()
        stage = omni.usd.get_context().get_stage()
        if stage:
            rect_prim = stage.GetPrimAtPath(RECT_PATH)
            if rect_prim and rect_prim.IsValid():
                self._recompute_extent_from_plugins(UsdGeom.BasisCurves(rect_prim))

    def _create_or_update_rectangle(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        if stage is None:
            carb.log_warn("No open stage was found. Rectangle was not created.")
            return

        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        # Asegurar paths base
        UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
        UsdGeom.Xform.Define(stage, Sdf.Path("/World/Sketches"))

        rect_curve = UsdGeom.BasisCurves.Define(stage, RECT_PATH)

        half_width = DEFAULT_WIDTH_METERS * 0.5
        half_depth = DEFAULT_DEPTH_METERS * 0.5

        # Rectangle lies on the XY sketch plane with Z fixed at 0 meters.
        points = [
            Gf.Vec3f(-half_width, -half_depth, 0.0),
            Gf.Vec3f( half_width, -half_depth, 0.0),
            Gf.Vec3f( half_width,  half_depth, 0.0),
            Gf.Vec3f(-half_width,  half_depth, 0.0),
        ]

        # Polilínea cerrada (contorno)
        rect_curve.GetTypeAttr().Set(UsdGeom.Tokens.linear)
        rect_curve.GetWrapAttr().Set(UsdGeom.Tokens.periodic)
        rect_curve.GetPurposeAttr().Set(UsdGeom.Tokens.guide)

        # Arrays USD “correctos”
        rect_curve.GetCurveVertexCountsAttr().Set(Vt.IntArray([len(points)]))
        rect_curve.GetPointsAttr().Set(Vt.Vec3fArray(points))
        self._recompute_extent_from_plugins(rect_curve)
        self._remove_widths_if_present(rect_curve)

        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=DRAW_WIREFRAME_ATTR,
            value=True,
            prev=None,
            type_to_create_if_not_exist=Sdf.ValueTypeNames.Bool,
        )

        selection = usd_context.get_selection()
        new_selection = [RECT_PATH.pathString]
        selection.set_selected_prim_paths(new_selection, True)
        asyncio.ensure_future(self._enable_curve_editing(new_selection))
