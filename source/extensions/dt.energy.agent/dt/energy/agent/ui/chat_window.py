from __future__ import annotations

import asyncio
from datetime import datetime

import carb
import omni.kit.app
import omni.ui as ui

from ..core.agent_controller import AgentController


class ChatWindow:
    WINDOW_TITLE = "Energy Twin Agent"

    def __init__(self, controller: AgentController):
        self._controller = controller
        self._window: ui.Window | None = None
        self._history_frame: ui.ScrollingFrame | None = None
        self._history_label: ui.Label | None = None
        self._input_model: ui.SimpleStringModel | None = None
        self._history_entries: list[dict[str, str]] = []
        self._build_window()

    def show(self):
        if self._window is None:
            self._build_window()
        self._window.visible = True

    def destroy(self):
        if self._window is not None:
            self._window.visible = False
            self._window = None
        self._history_frame = None
        self._history_label = None
        self._input_model = None

    def _build_window(self):
        self._window = ui.Window(self.WINDOW_TITLE, width=560, height=640)
        with self._window.frame:
            with ui.VStack(spacing=8, height=0):
                ui.Label("Energy Twin Agent", style={"font_size": 20})
                with ui.HStack(spacing=6):
                    ui.Button("Analyze Scene", clicked_fn=self._analyze_scene)
                    ui.Button("Create Test Zone", clicked_fn=self._create_test_zone)
                    ui.Button("Validate Energy Model", clicked_fn=self._validate_energy_model)
                with ui.HStack(spacing=6):
                    ui.Button("List Sketches", clicked_fn=self._list_sketches)
                    ui.Button("Create Test Sketch", clicked_fn=self._create_test_sketch)
                    ui.Button("Extrude Selected Sketch", clicked_fn=self._extrude_selected_sketch)
                with ui.HStack(spacing=6):
                    ui.Button("Find Blocks From Selected Sketch", clicked_fn=self._find_blocks_from_selected_sketch)
                    ui.Button("Rebuild Selected Block", clicked_fn=self._rebuild_selected_block)
                    ui.Button("Sync All ThermalViz", clicked_fn=self._sync_all_thermalviz)
                with ui.HStack(spacing=6):
                    ui.Button("Import DXF Reference", clicked_fn=self._import_dxf_reference)
                    ui.Button("List DXF References", clicked_fn=self._list_dxf_references)

                self._history_frame = ui.ScrollingFrame(height=420)
                with self._history_frame:
                    self._history_label = ui.Label("", word_wrap=True)

                with ui.HStack(spacing=6):
                    input_field = ui.StringField(
                        tooltip="Ej: Crea un bloque de 10 x 8 x 3",
                    )
                    self._input_model = input_field.model
                    self._input_model.set_value("")
                    self._install_input_callbacks(input_field)
                    ui.Button("Send", width=80, clicked_fn=self._send_message)

        if not self._history_entries:
            self._append("Agent", "Ready. Mock LLM is active; no external model calls will be made.")

    def _send_message(self):
        text = self._input_model.get_value_as_string().strip() if self._input_model is not None else ""
        if not text:
            return
        self._append("User", text)
        if self._input_model is not None:
            self._input_model.set_value("")
        response = self._controller.handle_user_message(text)
        self._append_result(response)

    def _analyze_scene(self):
        self._append("User", "Analyze Scene")
        self._append_result(self._controller.execute_direct_tool("analyze_scene", {}))

    def _create_test_zone(self):
        self._append("User", "Create Test Zone")
        self._append_result(
            self._controller.execute_direct_tool(
                "create_aec_block",
                {"name": "Block_01", "width": 10.0, "depth": 8.0, "height": 3.0},
            )
        )

    def _validate_energy_model(self):
        self._append("User", "Validate Energy Model")
        self._append_result(self._controller.execute_direct_tool("validate_aec_blocks", {}))

    def _list_sketches(self):
        self._append("User", "List Sketches")
        self._append_result(self._controller.execute_direct_tool("list_sketches", {}))

    def _create_test_sketch(self):
        self._append("User", "Create Test Sketch")
        self._append_result(
            self._controller.execute_direct_tool(
                "create_sketch_rectangle",
                {"name": "Rect_01", "width": 10.0, "depth": 8.0},
            )
        )

    def _extrude_selected_sketch(self):
        self._append("User", "Extrude Selected Sketch")
        self._append_result(self._controller.execute_direct_tool("extrude_selected_sketch", {"height": 3.0}))

    def _find_blocks_from_selected_sketch(self):
        self._append("User", "Find Blocks From Selected Sketch")
        self._append_result(self._controller.execute_direct_tool("find_blocks_from_sketch", {}))

    def _rebuild_selected_block(self):
        self._append("User", "Rebuild Selected Block")
        self._append_result(self._controller.execute_direct_tool("rebuild_block_from_sketch", {}))

    def _sync_all_thermalviz(self):
        self._append("User", "Sync All ThermalViz")
        self._append_result(self._controller.execute_direct_tool("sync_all_blocks_to_thermalviz", {}))

    def _import_dxf_reference(self):
        self._append("User", "Import DXF Reference")
        self._append(
            "Agent",
            "Indica el path absoluto por chat, por ejemplo: importa dxf C:/temp/plano.dxf",
        )

    def _list_dxf_references(self):
        self._append("User", "List DXF References")
        self._append_result(self._controller.execute_direct_tool("list_dxf_references", {}))

    def _append_result(self, response: dict):
        if response.get("ok"):
            self._append("Agent", response.get("text") or response.get("message") or "Done.")
            carb.log_info(f"[Energy Twin Agent] Tool result: {response.get('tool', 'unknown')}")
        else:
            message = response.get("text") or response.get("message") or response.get("error") or "Unknown error"
            self._append("Agent", message)
            if response.get("error"):
                carb.log_error(f"[Energy Twin Agent] Tool failed: {message}")
            else:
                carb.log_info(f"[Energy Twin Agent] Tool returned validation issues: {response.get('tool', 'unknown')}")

    def _append(self, speaker: str, text: str):
        self._history_entries.append(
            {
                "speaker": speaker,
                "time": datetime.now().strftime("%H:%M:%S"),
                "text": text,
            }
        )
        if self._history_label is not None:
            self._history_label.text = "\n\n".join(_format_entry(entry) for entry in self._history_entries[-80:])
        self._scroll_to_bottom()

    def _install_input_callbacks(self, input_field):
        for attr_name, value in (
            ("placeholder_text", "Ej: Crea un bloque de 10 x 8 x 3"),
            ("placeholder", "Ej: Crea un bloque de 10 x 8 x 3"),
        ):
            try:
                setattr(input_field, attr_name, value)
                break
            except Exception:
                pass

        for method_name in ("set_key_pressed_fn", "set_key_press_fn"):
            method = getattr(input_field, method_name, None)
            if method is None:
                continue
            try:
                method(self._on_input_key_pressed)
                break
            except Exception:
                pass

        model = getattr(input_field, "model", None)
        for method_name in ("add_end_edit_fn",):
            method = getattr(model, method_name, None)
            if method is None:
                continue
            try:
                method(self._on_input_end_edit)
                break
            except Exception:
                pass

    def _on_input_key_pressed(self, *args):
        key = _first_key(args)
        modifiers = _first_modifier(args)
        if not _is_enter_key(key):
            return False
        shift_flag = getattr(carb.input, "KEYBOARD_MODIFIER_FLAG_SHIFT", 0)
        if modifiers & shift_flag:
            if self._input_model is not None:
                self._input_model.set_value(f"{self._input_model.get_value_as_string()}\n")
            return True
        self._send_message()
        return True

    def _on_input_end_edit(self, *_args):
        text = self._input_model.get_value_as_string().strip() if self._input_model is not None else ""
        if text:
            self._send_message()

    def _scroll_to_bottom(self):
        if self._history_frame is None:
            return
        asyncio.ensure_future(self._scroll_to_bottom_async())

    async def _scroll_to_bottom_async(self):
        await omni.kit.app.get_app().next_update_async()
        if self._history_frame is None:
            return
        for attr_name in ("scroll_y", "scroll_y_offset"):
            try:
                setattr(self._history_frame, attr_name, 1_000_000)
            except Exception:
                pass


def _format_entry(entry: dict[str, str]) -> str:
    speaker = "USER " if entry["speaker"] == "User" else "AGENT"
    return f"[{entry['time']}] {speaker}\n{entry['text']}"


def _first_key(args):
    for arg in args:
        if isinstance(arg, carb.input.KeyboardInput):
            return arg
        if isinstance(arg, int):
            name = str(arg).upper()
            if "ENTER" in name or "RETURN" in name:
                return arg
    return None


def _first_modifier(args) -> int:
    for arg in args:
        if isinstance(arg, int):
            return arg
    return 0


def _is_enter_key(key) -> bool:
    if key is None:
        return False
    enter_keys = []
    for name in ("ENTER", "NUMPAD_ENTER", "KEY_ENTER", "KEY_RETURN"):
        value = getattr(carb.input.KeyboardInput, name, None)
        if value is not None:
            enter_keys.append(value)
    return key in enter_keys or "ENTER" in str(key).upper() or "RETURN" in str(key).upper()
