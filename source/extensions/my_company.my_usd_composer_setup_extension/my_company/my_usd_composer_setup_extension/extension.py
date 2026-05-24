# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import inspect
import logging
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path


import carb
import omni.ext
import omni.kit.app
import omni.kit.commands
import omni.kit.menu.utils
import omni.kit.stage_templates as stage_templates
import omni.kit.ui
import omni.kit.window.property as property_window_ext
import omni.ui as ui
import omni.usd
from omni.kit.menu.utils import MenuLayout, MenuItemDescription
from omni.kit.property.usd import PrimPathWidget
from omni.kit.quicklayout import QuickLayout
from omni.kit.window.title import get_main_window_title
from pxr import UsdGeom

DATA_PATH = Path(carb.tokens.get_tokens_interface().resolve(
    "${my_company.my_usd_composer_setup_extension}")
)


async def _load_layout(layout_file: str, keep_windows_open=False):
    """Loads a provided layout file and ensures the viewport is set to FILL."""
    try:
        # few frames delay to avoid the conflict with the
        # layout of omni.kit.mainwindow
        for _ in range(3):
            await omni.kit.app.get_app().next_update_async()
        QuickLayout.load_file(layout_file, keep_windows_open)
    except:
        QuickLayout.load_file(layout_file)


class CreateSetupExtension(omni.ext.IExt):
    """Create Final Configuration"""
    def on_startup(self, _ext_id):
        """
        setup the window layout, menu, final configuration
        of the extensions etc
        """
        self._settings = carb.settings.get_settings()
        if self._settings and self._settings.get("/app/warmupMode"):
            # if warmup mode is enabled, we don't want to load the stage or
            # layout, just return
            return

        self._apply_stage_defaults()
        self._apply_viewport_guide_defaults()
        self._apply_transform_manipulator_defaults()
        self._apply_snap_defaults()
        carb.log_info("[Setup] LOADED")
        carb.log_info(f"[Setup] file={os.path.abspath(__file__)}")
        self._stage_verified = False
        self._stage_auto_framed = False
        self._stage_first_event_logged = False
        self._processed_stage_identifier = None
        self._stage_verify_frame_count = 0
        self._stage_update_sub = None
        self._stage_event_sub = omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event,
            name="my_own_software.setup.stage_verification",
        )

        self._menu_layout = []

        telemetry_logger = logging.getLogger("idl.telemetry.opentelemetry")
        telemetry_logger.setLevel(logging.ERROR)

        # this is a work around as some Extensions don't properly setup their
        # default setting in time
        self._set_defaults()

        # adjust couple of viewport settings
        self._settings.set("/app/viewport/boundingBoxes/enabled", True)

        # These two settings do not co-operate well on ADA cards, so for
        # now simulate a toggle of the present thread on startup to work around
        if self._settings.get("/exts/omni.kit.renderer.core/present/enabled") \
            and self._settings.get(
            "/exts/omni.kit.widget.viewport/autoAttach/mode"
        ):
            async def _toggle_present(settings, n_waits: int = 1):
                async def _toggle_setting(app, enabled: bool, n_waits: int):
                    for _ in range(n_waits):
                        await app.next_update_async()
                    settings.set(
                        "/exts/omni.kit.renderer.core/present/enabled",
                        enabled
                    )

                app = omni.kit.app.get_app()
                await _toggle_setting(app, False, n_waits)
                await _toggle_setting(app, True, n_waits)

            asyncio.ensure_future(_toggle_present(self._settings))

        # Setting and Saving FSD as a global change in preferences
        # Requires to listen for changes at the local path to update
        # Composer's persistent path.
        fabric_app_setting = self._settings.get("/app/useFabricSceneDelegate")
        fabric_persistent_setting = self._settings.get(
            "/persistent/app/useFabricSceneDelegate"
        )
        fabric_enabled: bool = fabric_app_setting if \
            fabric_persistent_setting is None else fabric_persistent_setting

        self._settings.set("/app/useFabricSceneDelegate", fabric_enabled)

        self._sub_fabric_delegate_changed = \
            omni.kit.app.SettingChangeSubscription(
                "/app/useFabricSceneDelegate",
                self._on_fabric_delegate_changed
            )

        # Adjust the Window Title to show the Create Version
        window_title = get_main_window_title()

        app_version = self._settings.get("/app/version")
        if not app_version:
            with open(
                carb.tokens.get_tokens_interface().resolve("${app}/../VERSION"),
                encoding="utf-8"
            ) as f:
                app_version = f.read()

        if app_version:
            if "+" in app_version:
                app_version, _ = app_version.split("+")

            # for RC version we remove some details
            if self._settings.get("/privacy/externalBuild"):
                if "-" in app_version:
                    app_version, _ = app_version.split("-")
                window_title.set_app_version(app_version)
            else:
                window_title.set_app_version(app_version)

        imgui_style_applied = False
        try:
            # using imgui directly to adjust some color and Variable
            import omni.kit.imgui as _imgui
            imgui = _imgui.acquire_imgui()
            if imgui.is_valid():
                imgui.push_style_color(_imgui.StyleColor.ScrollbarGrab, carb.Float4(0.4, 0.4, 0.4, 1))
                imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabHovered, carb.Float4(0.6, 0.6, 0.6, 1))
                imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabActive, carb.Float4(0.8, 0.8, 0.8, 1))
                imgui.push_style_var_float(_imgui.StyleVar.DockSplitterSize, 2)
                imgui_style_applied = True
        except ImportError:
            pass

        if not imgui_style_applied:
            carb.log_error("Style may not be as expected (carb.imgui was not valid)")

        layout_file = f"{DATA_PATH}/layouts/default.json"

        # Setting to hack few things in test run. Ideally we shouldn't need it.
        test_mode = self._settings.get("/app/testMode")

        if not test_mode:
            asyncio.ensure_future(_load_layout(layout_file, True))

        asyncio.ensure_future(self.__property_window())

        self.__menu_update()

        if not test_mode and not \
                self._settings.get("/app/content/emptyStageOnStart"):
            asyncio.ensure_future(self.__new_stage())

        startup_time = \
            omni.kit.app.get_app_interface().get_time_since_start_s()
        self._settings.set(
            "/crashreporter/data/startup_time", f"{startup_time}"
        )

        def show_documentation(*args):
            webbrowser.open(
                "https://docs.omniverse.nvidia.com/composer/latest/index.html"
            )
        self._help_menu_items = [
            MenuItemDescription(
                name="Documentation",
                onclick_fn=show_documentation,
                appear_after=[omni.kit.menu.utils.MenuItemOrder.FIRST]
            )
        ]
        omni.kit.menu.utils.add_menu_items(self._help_menu_items, name="Help")

    def _set_setting_with_warning(self, path, value):
        try:
            self._settings.set(path, value)
        except Exception as exc:
            carb.log_warn(f"[Setup] Could not set {path}: {exc}")

    def _apply_stage_defaults(self):
        setup_template_path = (
            "${my_company.my_usd_composer_setup_extension}/data/stage_templates"
        )

        self._set_setting_with_warning("/persistent/app/stage/upAxis", "Z")
        self._set_setting_with_warning(
            "/persistent/app/stage/metersPerUnit", 1.0
        )
        self._set_setting_with_warning(
            "/persistent/app/newStage/defaultUpAxis", "Z"
        )
        self._set_setting_with_warning(
            "/persistent/app/newStage/defaultMetersPerUnit", 1.0
        )
        self._set_setting_with_warning(
            "/persistent/app/newStage/defaultTemplate", "empty"
        )
        self._set_setting_with_warning(
            "/persistent/app/viewport/autoFrame/mode", "always"
        )
        self._set_setting_with_warning(
            "/persistent/app/viewport/autoFrame/singleCamera", True
        )
        self._set_setting_with_warning(
            "/persistent/app/viewport/autoFrame/implicitOnly", True
        )

        template_paths = self._settings.get("/persistent/app/newStage/templatePath")
        if template_paths is None:
            template_paths = []
        elif not isinstance(template_paths, (list, tuple)):
            template_paths = [template_paths]
        else:
            template_paths = list(template_paths)

        template_paths = [path for path in template_paths if path != setup_template_path]

        self._set_setting_with_warning(
            "/persistent/app/newStage/templatePath", template_paths
        )

        carb.log_info("[Setup] Applied defaults: upAxis=Z, metersPerUnit=1.0")
        carb.log_info(
            '[Setup] NewStage defaults: template="empty", setup templatePath removed'
        )
        carb.log_info("[Setup] Viewport defaults: AutoFrame=always")

    def _log_setting_transition(self, path, previous_value, new_value):
        carb.log_info(
            f"[Setup] Setting {path}: old={previous_value!r}, new={new_value!r}"
        )

    def _apply_viewport_guide_defaults(self):
        guide_setting_path = "/persistent/app/hydra/displayPurpose/guide"
        previous_guide_value = self._settings.get(guide_setting_path)
        self._set_setting_with_warning(guide_setting_path, True)
        self._log_setting_transition(
            guide_setting_path,
            previous_guide_value,
            self._settings.get(guide_setting_path),
        )

    def _apply_transform_manipulator_defaults(self):
        defaults = {
            "/persistent/exts/omni.kit.manipulator.prim.core/manipulator/placement": "Authored Pivot",
            "/app/transform/moveMode": "local",
            "/app/transform/rotateMode": "local",
        }
        for path, value in defaults.items():
            previous_value = self._settings.get(path)
            self._set_setting_with_warning(path, value)
            self._log_setting_transition(path, previous_value, self._settings.get(path))

        carb.log_info(
            "[Setup] Transform defaults: placement=Authored Pivot, moveMode=local, rotateMode=local"
        )

    def _apply_snap_defaults(self):
        provider_names_path = "/exts/omni.kit.manipulator.tool.snap/providerNames"
        snap_enabled_path = "/app/viewport/snapEnabled"
        mesh_provider_path = "/exts/omni.kit.manipulator.tool.mesh_snap/enableAllProviders"
        conform_target_path = "/persistent/exts/omni.kit.manipulator.tool.snap/conformToTarget"
        keep_spacing_path = "/persistent/exts/omni.kit.manipulator.tool.snap/keepSpacing"
        providers = [
            "Vertex (Mesh Based - Single-Face)",
            "Edge (Mesh Based - Single-Face)",
            "Surface (Mesh Based)",
        ]

        previous_enabled = self._settings.get(snap_enabled_path)
        previous_providers = self._settings.get(provider_names_path)
        self._set_setting_with_warning(mesh_provider_path, False)
        self._set_setting_with_warning(snap_enabled_path, True)
        self._set_setting_with_warning(provider_names_path, providers)
        self._set_setting_with_warning(conform_target_path, False)
        self._set_setting_with_warning(keep_spacing_path, False)
        carb.log_info(
            "[Setup] Snap defaults: "
            f"enabled {previous_enabled!r}->True, providers {previous_providers!r}->{providers!r}"
        )

    def _set_defaults(self):
        """
        This is trying to setup some defaults for extensions to avoid warnings.
        """
        self._settings.set_default("/persistent/app/omniverse/bookmarks", {})
        self._settings.set_default(
            "/persistent/app/stage/timeCodeRange", [0, 100]
        )

        self._settings.set_default(
            "/persistent/audio/context/closeAudioPlayerOnStop",
            False
        )

        self._settings.set_default(
            "/persistent/app/primCreation/PrimCreationWithDefaultXformOps",
            True
        )
        self._settings.set_default(
            "/persistent/app/primCreation/DefaultXformOpType",
            "Scale, Rotate, Translate"
        )
        self._settings.set_default(
            "/persistent/app/primCreation/DefaultRotationOrder",
            "ZYX"
        )
        self._settings.set_default(
            "/persistent/app/primCreation/DefaultXformOpPrecision",
            "Double"
        )

        # omni.kit.property.tagging
        self._settings.set_default(
            "/persistent/exts/omni.kit.property.tagging/showAdvancedTagView",
            False
        )
        self._settings.set_default(
            "/persistent/exts/omni.kit.property.tagging/showHiddenTags",
            False
        )
        self._settings.set_default(
            "/persistent/exts/omni.kit.property.tagging/modifyHiddenTags",
            False
        )

        self._settings.set_default(
            "/rtx/sceneDb/ambientLightIntensity", 0.0
        )  # set default ambientLight intensity to Zero

    def _on_fabric_delegate_changed(
            self, _v: str, event_type: carb.settings.ChangeEventType):
        if event_type == carb.settings.ChangeEventType.CHANGED:
            enabled: bool = self._settings.get_as_bool(
                "/app/useFabricSceneDelegate"
            )
            self._settings.set(
                "/persistent/app/useFabricSceneDelegate", enabled
            )

    def _on_stage_event(self, event):
        if not self._stage_first_event_logged:
            carb.log_info(f"[Setup] First stage event type={event.type}")
            carb.log_info("[Setup] starting verification loop NOW")
            self._stage_first_event_logged = True

        stage = omni.usd.get_context().get_stage()
        if stage:
            stage_identifier = stage.GetRootLayer().identifier
            if (
                self._processed_stage_identifier == stage_identifier
                and self._stage_verified
                and self._stage_auto_framed
            ):
                return

        if self._stage_update_sub is not None:
            return

        self._stage_verified = False
        self._stage_auto_framed = False
        self._ensure_stage_verification()

    def _ensure_stage_verification(self):
        if self._stage_verified:
            return

        if self._stage_update_sub is not None:
            return

        self._stage_verify_frame_count = 0
        self._stage_update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self._on_update_stage_verification,
            name="my_own_software.setup.update_stage_verification",
        )

    def _on_update_stage_verification(self, _event):
        if self._stage_verified and self._stage_auto_framed:
            self._clear_stage_update_subscription()
            return

        stage = omni.usd.get_context().get_stage()
        if stage:
            if not self._stage_verified:
                self._log_stage_verification(stage)

            if not self._stage_auto_framed and self._try_auto_frame_camera():
                self._stage_auto_framed = True
                carb.log_info("[Setup] Auto-framed camera on stage open")

            if self._stage_verified and self._stage_auto_framed:
                self._clear_stage_update_subscription()
                return

        self._stage_verify_frame_count += 1
        if self._stage_verify_frame_count >= 120:
            carb.log_warn(
                "[Setup] Stage verification skipped: no open stage after retry window."
            )
            if not self._stage_auto_framed:
                carb.log_warn(
                    "[Setup] Auto-frame skipped: no active viewport or stage after retry window."
                )
            self._clear_stage_update_subscription()

    def _log_stage_verification(self, stage):
        up_axis = UsdGeom.GetStageUpAxis(stage)
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        carb.log_info(
            f"[Setup] Stage verification: upAxis={up_axis}, metersPerUnit={meters_per_unit}"
        )
        self._processed_stage_identifier = stage.GetRootLayer().identifier
        self._stage_verified = True

    def _clear_stage_update_subscription(self):
        self._stage_update_sub = None

    def _try_auto_frame_camera(self):
        try:
            import omni.kit.viewport.utility as viewport_utility
        except Exception as exc:
            carb.log_warn(f"[Setup] Auto-frame unavailable: {exc}")
            return False

        try:
            return bool(viewport_utility.frame_viewport_selection())
        except Exception as exc:
            carb.log_warn(f"[Setup] Auto-frame failed: {exc}")
            return False

    async def __new_stage(self):
        """Create a new stage """
        # 5 frame delay to allow Layout
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()

        if omni.usd.get_context().can_open_stage():
            stage_templates.new_stage(template="empty")
            self._ensure_stage_verification()

    def _launch_app(self, app_id, console=True, custom_args=None):
        """launch another Kit app with the same settings"""
        app_path = carb.tokens.get_tokens_interface().resolve("${app}")
        kit_file_path = os.path.join(app_path, app_id)

        # https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
        # Validate input from command line (detected in static analysis)
        kit_exe = sys.argv[0]
        if not os.path.exists(kit_exe):
            print(f"cannot find executable{kit_exe}")
            return

        launch_args = [kit_exe]
        launch_args += [kit_file_path]
        if custom_args:
            launch_args.extend(custom_args)

        # Pass all exts folders
        exts_folders = self._settings.get("/app/exts/folders")
        if exts_folders:
            for folder in exts_folders:
                launch_args.extend(["--ext-folder", folder])

        kwargs = {"close_fds": False}
        if platform.system().lower() == "windows":
            if console:
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | \
                    subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(launch_args, **kwargs)

    def _show_ui_docs(self):
        """show the omniverse ui documentation as an external Application"""
        self._launch_app("omni.app.uidoc.kit")

    def _show_launcher(self):
        """show the omniverse ui documentation as an external Application"""
        self._launch_app(
            "omni.create.launcher.kit",
            console=False,
            custom_args={"--/app/auto_launch=false"}
        )

    async def __property_window(self):
        """Creates a propety window and sets column sizes."""
        await omni.kit.app.get_app().next_update_async()

        property_window = property_window_ext.get_window()
        property_window.set_scheme_delegate_layout(
            "Create Layout",
            ["basis_curves_prim", "path_prim", "material_prim",
             "xformable_prim", "shade_prim", "camera_prim"],
        )

        # expand width of path_items so "Instancable" doesn't get wrapped
        PrimPathWidget.set_path_item_padding(3.5)

    def __menu_update(self):
        """Update the menu"""
        self._menu_layout = [
            MenuLayout.Menu(
                "Window",
                [
                    MenuLayout.SubMenu(
                        "Animation",
                        [
                            MenuLayout.Item("Timeline"),
                            MenuLayout.Item("Sequencer"),
                            MenuLayout.Item("Curve Editor"),
                            MenuLayout.Item("Retargeting"),
                            MenuLayout.Item("Animation Graph"),
                            MenuLayout.Item("Animation Graph Samples"),
                        ],
                    ),
                    MenuLayout.SubMenu(
                        "Layout",
                        [
                            MenuLayout.Item("Quick Save", remove=True),
                            MenuLayout.Item("Quick Load", remove=True),
                        ],
                    ),
                    MenuLayout.SubMenu(
                        "Browsers",
                        [
                            MenuLayout.Item("Content", source="Window/Content"),
                            MenuLayout.Item("Materials"),
                            MenuLayout.Item("Skies"),
                        ],
                    ),
                    MenuLayout.SubMenu(
                        "Rendering",
                        [
                            MenuLayout.Item("Render Settings"),
                            MenuLayout.Item("Movie Capture"),
                            MenuLayout.Item("MDL Material Graph"),
                            MenuLayout.Item("Tablet XR"),
                        ],
                    ),
                    MenuLayout.SubMenu(
                        "Utilities",
                        [
                            MenuLayout.Item("Console"),
                            MenuLayout.Item("Profiler"),
                            MenuLayout.Item("USD Paths"),
                            MenuLayout.Item("Statistics"),
                            MenuLayout.Item("Activity Progress"),
                            MenuLayout.Item("Actions"),
                            MenuLayout.Item("Asset Validator"),
                        ],
                    ),
                    MenuLayout.Sort(
                        exclude_items=["Extensions"], sort_submenus=True
                    ),
                    MenuLayout.Item("New Viewport Window", remove=True),
                ],
            ),
            MenuLayout.Menu(
                "Layout",
                [
                    MenuLayout.Item("Default", source="Reset Layout"),
                    MenuLayout.Seperator(),
                    MenuLayout.Item(
                        "UI Toggle Visibility",
                        source="Window/UI Toggle Visibility"
                    ),
                    MenuLayout.Item(
                        "Fullscreen Mode", source="Window/Fullscreen Mode"
                    ),
                    MenuLayout.Seperator(),
                    MenuLayout.Item(
                        "Save Layout", source="Window/Layout/Save Layout..."
                    ),
                    MenuLayout.Item(
                        "Load Layout", source="Window/Layout/Load Layout..."
                    ),
                    MenuLayout.Seperator(),
                    MenuLayout.Item(
                        "Quick Save", source="Window/Layout/Quick Save"
                    ),
                    MenuLayout.Item(
                        "Quick Load", source="Window/Layout/Quick Load"
                    ),
                ],
            ),
        ]
        omni.kit.menu.utils.add_layout(self._menu_layout)

        self._layout_menu_items = []

        def add_layout_menu_entry(name, parameter, key):
            """Add a layout menu entry."""
            if inspect.isfunction(parameter):
                menu_dict = omni.kit.menu.utils.build_submenu_dict(
                    [
                        MenuItemDescription(name=f"Layout/{name}",
                                            onclick_fn=lambda: asyncio.ensure_future(parameter()),
                                            hotkey=(carb.input.KEYBOARD_MODIFIER_FLAG_CONTROL, key)),
                    ]
                )
            else:
                async def _active_layout(layout):
                    await _load_layout(layout)
                    # load layout file again to make sure layout correct
                    await _load_layout(layout)

                menu_dict = omni.kit.menu.utils.build_submenu_dict(
                    [
                        MenuItemDescription(name=f"Layout/{name}",
                                            onclick_fn=lambda: asyncio.ensure_future(_active_layout(f"{DATA_PATH}/layouts/{parameter}.json")),
                                            hotkey=(carb.input.KEYBOARD_MODIFIER_FLAG_CONTROL, key)),
                    ]
                )

            # add menu
            for group in menu_dict:
                omni.kit.menu.utils.add_menu_items(menu_dict[group], group)

            self._layout_menu_items.append(menu_dict)

        add_layout_menu_entry(
            "Reset Layout", "default", carb.input.KeyboardInput.KEY_1
        )

        # create Quick Load & Quick Save
        async def quick_save():
            QuickLayout.quick_save(None, None)

        async def quick_load():
            QuickLayout.quick_load(None, None)

        add_layout_menu_entry(
            "Quick Save", quick_save, carb.input.KeyboardInput.KEY_7
        )
        add_layout_menu_entry(
            "Quick Load", quick_load, carb.input.KeyboardInput.KEY_8
        )

        # open "Asset Stores" window
        ui.Workspace.show_window("Asset Stores")

    def on_shutdown(self):
        """Clean up the extension"""
        self._sub_fabric_delegate_changed = None
        self._stage_event_sub = None
        self._clear_stage_update_subscription()

        omni.kit.menu.utils.remove_layout(self._menu_layout)
        self._menu_layout = None

        for menu_dict in self._layout_menu_items:
            for group in menu_dict:
                omni.kit.menu.utils.remove_menu_items(menu_dict[group], group)

        self._layout_menu_items = None
        self._launcher_menu = None
        self._reset_menu = None
