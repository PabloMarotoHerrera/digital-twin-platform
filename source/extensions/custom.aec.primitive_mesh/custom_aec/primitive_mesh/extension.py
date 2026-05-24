import carb
import omni.ext
import omni.kit.menu.utils
import omni.ui as ui
import omni.usd
from omni.kit.menu.utils import MenuItemDescription
from pxr import Sdf, UsdGeom

from .mesh_builder import SUPPORTED_PRIMITIVES, create_or_update_primitive_mesh


DEFAULT_PATH = "/World/Design/Primitive_01"


class AecPrimitiveMeshExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._window = None
        self._primitive_index = 0
        self._menu_items_window = None
        self._menu_items_create = None
        carb.log_info("[AEC Primitive Mesh] startup")

    def on_shutdown(self):
        if self._menu_items_window:
            omni.kit.menu.utils.remove_menu_items(self._menu_items_window, "Window")
            self._menu_items_window = None
        if self._menu_items_create:
            omni.kit.menu.utils.remove_menu_items(self._menu_items_create, "Create")
            self._menu_items_create = None
        self._window = None
        carb.log_info("[AEC Primitive Mesh] shutdown")

    def _show_window(self):
        if self._window is None:
            self._build_window()
        self._window.visible = True

    def _build_window(self):
        self._window = ui.Window(
            "Primitive Mesh",
            width=380,
            height=330,
        )

        with self._window.frame:
            with ui.VStack(spacing=8, height=0):
                ui.Label("AEC Primitive Mesh", style={"font_size": 18})
                ui.Label("Parametric modeling primitives in meters.")

                with ui.HStack():
                    ui.Label("Primitive", width=110)
                    primitive_model = ui.ComboBox(0, *SUPPORTED_PRIMITIVES).model
                    primitive_model.add_item_changed_fn(self._on_primitive_changed)

                self._width_model = self._float_row("Width X (m)", 10.0)
                self._depth_model = self._float_row("Depth Y (m)", 6.0)
                self._height_model = self._float_row("Height Z (m)", 3.0)
                self._segments_model = self._int_row("Segments", 16)

                with ui.HStack():
                    ui.Label("Path", width=110)
                    path_field = ui.StringField()
                    self._path_model = path_field.model
                    self._path_model.set_value(DEFAULT_PATH)

                ui.Spacer(height=4)
                with ui.HStack():
                    ui.Spacer()
                    ui.Button("Create New", width=150, clicked_fn=self._create_or_update)

    def _float_row(self, label, value):
        with ui.HStack():
            ui.Label(label, width=110)
            field = ui.FloatField()
            field.model.set_value(value)
            return field.model

    def _int_row(self, label, value):
        with ui.HStack():
            ui.Label(label, width=110)
            field = ui.IntField()
            field.model.set_value(value)
            return field.model

    def _on_primitive_changed(self, model, _item):
        self._primitive_index = model.get_item_value_model().as_int

    def _create_or_update(self):
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        if stage is None:
            carb.log_warn("[AEC Primitive Mesh] No open stage was found.")
            return

        prim_path = self._path_model.get_value_as_string().strip() or DEFAULT_PATH
        if not prim_path.startswith("/"):
            prim_path = "/" + prim_path

        path = Sdf.Path(prim_path)
        if not path.IsAbsolutePath() or path.IsPropertyPath():
            carb.log_warn(f"[AEC Primitive Mesh] Invalid prim path: {prim_path}")
            return

        primitive_type = SUPPORTED_PRIMITIVES[self._primitive_index]
        width = max(self._width_model.get_value_as_float(), 0.001)
        depth = max(self._depth_model.get_value_as_float(), 0.001)
        height = max(self._height_model.get_value_as_float(), 0.001)
        segments = max(self._segments_model.get_value_as_int(), 1)

        UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
        UsdGeom.Xform.Define(stage, Sdf.Path("/World/Design"))
        prim_path = omni.usd.get_stage_next_free_path(stage, prim_path, False)
        prim = create_or_update_primitive_mesh(
            stage=stage,
            prim_path=prim_path,
            primitive_type=primitive_type,
            width=width,
            depth=depth,
            height=height,
            segments=segments,
        )

        usd_context.get_selection().set_selected_prim_paths([prim.GetPath().pathString], True)
        carb.log_info(
            "[AEC Primitive Mesh] Created "
            f"{primitive_type} at {prim.GetPath().pathString}"
        )
