from __future__ import annotations

import json
import time
from datetime import datetime

import carb
import omni.ext
import omni.kit.app
import omni.kit.menu.utils
import omni.ui as ui
import omni.usd
from omni.kit.menu.utils import MenuItemDescription
from pxr import Sdf

from .data_sources import CsvTelemetrySource, JsonTelemetrySource, LiveStubTelemetrySource
from .model_access import SpaceInfo, find_spaces
from .mqtt_client import SimpleMqttClient
from .plot_widget import ThermalPlotWidget
from .signals import ThermalSignalProvider
from .thermal_style import ComfortBand, comfort_delta, comfort_hex, comfort_status
from .timeseries import TimeSeriesStore
from .ui_telemetry import build_telemetry_section
from .viewport_renderer import COLOR_MODE_PROXIES, COLOR_MODE_SURFACES, ThermalViewportRenderer
from .viewport_viz import TelemetryViewportVisualizer


PLAY_SPEEDS = ("x1", "x4", "x10")
PLAY_SPEED_MULTIPLIERS = (1.0, 4.0, 10.0)
BASE_HOURS_PER_SECOND = 0.25
MIN_UPDATE_INTERVAL_SECONDS = 1.0 / 12.0
TELEMETRY_MODES = ("Playback", "Live")


class AecThermalVizExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        self._window: ui.Window | None = None
        self._provider = ThermalSignalProvider(step_minutes=15)
        self._spaces: list[SpaceInfo] = []
        self._signals: dict[str, object] = {}
        self._zone_index = 0
        self._viz_enabled = False
        self._viz_mode_index = 1
        self._time_hour = 12.0
        self._is_playing = False
        self._play_speed_index = 0
        self._comfort_min = 21.0
        self._comfort_max = 24.0
        self._last_update_seconds: float | None = None
        self._update_subscription = None

        self._renderer = ThermalViewportRenderer()
        self._telemetry_visualizer = TelemetryViewportVisualizer()
        self._telemetry_store = TimeSeriesStore()
        self._csv_source = CsvTelemetrySource()
        self._json_source = JsonTelemetrySource()
        self._live_stub_source = LiveStubTelemetrySource()

        self._status_label: ui.Label | None = None
        self._viz_status_label: ui.Label | None = None
        self._current_value_label: ui.Label | None = None
        self._plot: ThermalPlotWidget | None = None
        self._telemetry_status_label: ui.Label | None = None
        self._mqtt_status_label: ui.Label | None = None

        self._zone_combo_model = None
        self._viz_mode_model = None
        self._time_model = None
        self._time_label: ui.Label | None = None
        self._play_speed_model = None
        self._comfort_min_model = None
        self._comfort_max_model = None
        self._telemetry_sensor_model = None
        self._telemetry_channel_model = None
        self._telemetry_path_model = None
        self._mqtt_host_model = None
        self._mqtt_port_model = None
        self._mqtt_topic_model = None

        self._telemetry_sensor_id = "sensor.space_01"
        self._telemetry_channel = "temp"
        self._telemetry_path = ""
        self._mqtt_host = "127.0.0.1"
        self._mqtt_port = 1883
        self._mqtt_topic = "aec/#"
        self._telemetry_mode_index = 0
        self._telemetry_mode_model = None
        self._live_sources: dict[str, dict[str, object]] = {}
        self._mqtt_client = SimpleMqttClient()

        self._menu_items = [
            MenuItemDescription(name="AEC Thermal", onclick_fn=self._show_window),
        ]
        omni.kit.menu.utils.add_menu_items(self._menu_items, "Window")
        carb.log_info("[AEC Thermal] Extension loaded")

    def on_shutdown(self):
        self._stop_playback()
        omni.kit.menu.utils.remove_menu_items(self._menu_items, "Window")
        self._menu_items = []
        if self._window is not None:
            self._window.visible = False
            self._window = None
        stage = omni.usd.get_context().get_stage()
        if stage is not None:
            self._renderer.clear(stage)
            self._telemetry_visualizer.clear(stage)
        self._status_label = None
        self._viz_status_label = None
        self._current_value_label = None
        self._plot = None
        self._telemetry_status_label = None
        self._mqtt_status_label = None
        self._zone_combo_model = None
        self._viz_mode_model = None
        self._time_model = None
        self._time_label = None
        self._play_speed_model = None
        self._comfort_min_model = None
        self._comfort_max_model = None
        self._telemetry_sensor_model = None
        self._telemetry_channel_model = None
        self._telemetry_path_model = None
        self._mqtt_host_model = None
        self._mqtt_port_model = None
        self._mqtt_topic_model = None
        self._telemetry_mode_model = None
        self._mqtt_client.disconnect()
        carb.log_info("[AEC Thermal] Extension shutdown")

    def _show_window(self):
        if self._window is None:
            self._window = ui.Window("AEC Thermal", width=620, height=840)
            self._build_window()
        self._window.visible = True

    def _build_window(self):
        self._refresh_zones(rebuild_window=False)
        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=8, height=0):
                    ui.Label("AEC Thermal Visualization", style={"font_size": 18})
                    ui.Label("Digital twin thermal preview for generated AEC spaces.", word_wrap=True)

                    with ui.CollapsableFrame("Zones", collapsed=False):
                        with ui.VStack(spacing=6):
                            self._status_label = ui.Label("")
                            ui.Button("Refresh Zones", clicked_fn=lambda: self._refresh_zones(rebuild_window=True))
                            zone_labels = self._zone_labels()
                            if zone_labels:
                                combo = ui.ComboBox(self._zone_index, *zone_labels)
                                self._zone_combo_model = combo.model
                                self._zone_combo_model.add_item_changed_fn(self._on_zone_changed)
                            else:
                                ui.Label("No Spaces found under /World/Building.")

                    build_telemetry_section(self)

                    with ui.CollapsableFrame("Signal", collapsed=False):
                        with ui.VStack(spacing=6):
                            ui.Label("Variable: Temperature")
                            self._plot = ThermalPlotWidget()
                            self._current_value_label = ui.Label("", word_wrap=True)

                    with ui.CollapsableFrame("Comfort", collapsed=False):
                        with ui.VStack(spacing=6):
                            self._comfort_min_model = self._float_slider_row("Comfort Min (C)", self._comfort_min, 16.0, 26.0)
                            self._comfort_max_model = self._float_slider_row("Comfort Max (C)", self._comfort_max, 18.0, 30.0)
                            with ui.HStack(spacing=4):
                                self._legend_chip("Cold", 0xFFFF4A16)
                                self._legend_chip("Comfort", 0xFF58F54A)
                                self._legend_chip("Hot", 0xFF5830FF)

                    with ui.CollapsableFrame("Viewport Heatmap", collapsed=False):
                        with ui.VStack(spacing=6):
                            ui.Label("Thermal overlay synchronized with the selected hour.")
                            with ui.HStack():
                                ui.Label("Mode", width=135)
                                mode_combo = ui.ComboBox(self._viz_mode_index, COLOR_MODE_SURFACES, COLOR_MODE_PROXIES)
                                self._viz_mode_model = mode_combo.model
                                self._viz_mode_model.add_item_changed_fn(self._on_viz_mode_changed)
                            self._time_model = self._time_slider_row("Time", self._time_hour)
                            with ui.HStack():
                                ui.Label("Speed", width=135)
                                speed_combo = ui.ComboBox(self._play_speed_index, *PLAY_SPEEDS)
                                self._play_speed_model = speed_combo.model
                                self._play_speed_model.add_item_changed_fn(self._on_play_speed_changed)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Enable / Update Heatmap", width=210, clicked_fn=self._enable_or_update_viz)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Play", width=100, clicked_fn=self._start_playback)
                                ui.Button("Pause", width=100, clicked_fn=self._stop_playback)
                                ui.Button("Reset", width=100, clicked_fn=self._reset_time)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Button("Disable Heatmap", width=170, clicked_fn=self._disable_viz)
                            self._viz_status_label = ui.Label("")

        self._update_status()
        self._update_plot()
        self._update_time_label()
        self._update_current_value()
        self._update_viz_status()
        self._update_telemetry_status()
        self._update_mqtt_status()

    def _refresh_zones(self, rebuild_window: bool):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            self._spaces = []
            self._signals = {}
            carb.log_warn("[AEC Thermal] No stage available while refreshing zones")
        else:
            self._spaces = find_spaces(stage)
            self._signals = self._provider.generate(self._spaces)
            carb.log_info(f"[AEC Thermal] Refreshed zones: {len(self._spaces)} spaces")

        if self._spaces:
            self._zone_index = min(self._zone_index, len(self._spaces) - 1)
            selected = self._spaces[self._zone_index]
            if not self._telemetry_sensor_id.startswith("sensor.") or self._telemetry_sensor_id.endswith("space_01"):
                self._telemetry_sensor_id = f"sensor.{selected.name}"
        else:
            self._zone_index = 0

        if rebuild_window and self._window is not None:
            self._window.visible = False
            self._window = None
            self._show_window()
            return

        self._update_status()
        self._update_plot()
        self._update_current_value()
        self._update_telemetry_status()
        if not rebuild_window:
            self._update_viz_status()

    def _on_zone_changed(self, model, _item):
        try:
            self._zone_index = model.get_item_value_model().as_int
        except AttributeError:
            self._zone_index = 0
        selected = self._selected_space()
        if selected is not None and self._telemetry_sensor_model is not None and not self._telemetry_store.has_binding(selected.path):
            self._telemetry_sensor_model.set_value(f"sensor.{selected.name}")
        self._update_status()
        self._update_plot()
        self._update_current_value()
        self._update_telemetry_status()
        if self._viz_enabled:
            self._apply_viz()

    def _on_telemetry_mode_changed(self, model, _item):
        try:
            self._telemetry_mode_index = model.get_item_value_model().as_int
        except AttributeError:
            self._telemetry_mode_index = 0
        self._update_telemetry_status()

    def _update_status(self):
        if self._status_label is None:
            return
        if not self._spaces:
            self._status_label.text = "Zones found: 0"
            return
        selected = self._spaces[self._zone_index]
        self._status_label.text = f"Zones found: {len(self._spaces)} | Selected: {selected.name}"

    def _update_plot(self):
        if self._plot is None:
            return
        if not self._spaces:
            self._plot.set_signal(None, self._time_hour, self._current_comfort())
            return
        selected = self._spaces[self._zone_index]
        self._plot.set_signal(self._active_signal_for_space(selected.path), self._time_hour, self._current_comfort())

    def _on_viz_mode_changed(self, model, _item):
        try:
            self._viz_mode_index = model.get_item_value_model().as_int
        except AttributeError:
            self._viz_mode_index = 0
        if self._viz_enabled:
            self._apply_viz()

    def _on_play_speed_changed(self, model, _item):
        try:
            self._play_speed_index = model.get_item_value_model().as_int
        except AttributeError:
            self._play_speed_index = 0
        self._update_viz_status()

    def _on_time_slider_changed(self, model):
        self._time_hour = max(0.0, min(24.0, self._model_float(model) * 24.0))
        self._update_time_label()
        self._update_plot()
        self._update_current_value()
        if self._viz_enabled:
            self._apply_viz()

    def _on_comfort_changed(self, _model):
        self._comfort_min = self._model_float(self._comfort_min_model) if self._comfort_min_model is not None else 21.0
        self._comfort_max = self._model_float(self._comfort_max_model) if self._comfort_max_model is not None else 24.0
        if self._comfort_max <= self._comfort_min:
            self._comfort_max = self._comfort_min + 0.1
        self._update_plot()
        self._update_current_value()
        if self._viz_enabled:
            self._apply_viz()

    def _enable_or_update_viz(self):
        self._viz_enabled = True
        self._apply_viz()

    def _disable_viz(self):
        self._stop_playback()
        self._viz_enabled = False
        stage = omni.usd.get_context().get_stage()
        if stage is not None:
            self._renderer.clear(stage)
            self._telemetry_visualizer.clear(stage)
        self._update_viz_status()
        carb.log_info("[AEC Thermal] Disabled viewport heatmap")

    def _apply_viz(self):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            carb.log_warn("[AEC Thermal] Cannot apply heatmap: no stage")
            self._update_viz_status("No stage available.")
            return
        if not self._spaces:
            self._refresh_zones(rebuild_window=False)
        if self._time_model is not None:
            self._time_hour = max(0.0, min(24.0, self._model_float(self._time_model) * 24.0))
        mode = self._current_viz_mode()
        selected = self._selected_space()
        active_signals = self._active_signal_map()
        if self._telemetry_store.active_zone_paths():
            count = self._telemetry_visualizer.apply(
                stage,
                self._spaces,
                active_signals,
                self._telemetry_store,
                self._time_hour,
                self._current_comfort(),
                selected.path if selected is not None else None,
                mode=mode,
            )
        else:
            count = self._renderer.apply(
                stage,
                self._spaces,
                active_signals,
                self._time_hour,
                mode,
                self._current_comfort(),
                selected.path if selected is not None else None,
            )
        self._update_time_label()
        self._update_current_value()
        self._update_viz_status(f"Enabled: {mode} at {self._time_hour:.2f}h, colored {count} prims.")

    def _start_playback(self):
        if self._telemetry_mode_index == 1 and not self._live_sources:
            self._set_telemetry_message("Bind at least one live source before starting Live mode.")
            return
        self._viz_enabled = True
        self._ensure_update_subscription()
        self._is_playing = True
        self._apply_viz()
        self._update_viz_status()
        carb.log_info("[AEC Thermal] Started viewport heatmap playback")

    def _stop_playback(self):
        self._is_playing = False
        self._last_update_seconds = None
        self._maybe_release_update_subscription()
        self._update_viz_status()

    def _reset_time(self):
        self._time_hour = 12.0
        self._set_time_slider_from_hour(self._time_hour)
        self._update_plot()
        self._update_current_value()
        if self._viz_enabled:
            self._apply_viz()

    def _on_update(self, _event):
        had_mqtt = self._consume_mqtt_messages()
        if not self._is_playing:
            if had_mqtt:
                self._update_plot()
                self._update_current_value()
                if self._viz_enabled:
                    self._apply_viz()
            self._update_mqtt_status()
            return
        now = time.perf_counter()
        if self._last_update_seconds is None:
            self._last_update_seconds = now
            return
        elapsed = now - self._last_update_seconds
        if elapsed < MIN_UPDATE_INTERVAL_SECONDS:
            return
        self._last_update_seconds = now

        previous_hour = self._time_hour
        speed = PLAY_SPEED_MULTIPLIERS[min(self._play_speed_index, len(PLAY_SPEED_MULTIPLIERS) - 1)]
        self._time_hour = (self._time_hour + elapsed * BASE_HOURS_PER_SECOND * speed) % 24.0
        if self._telemetry_mode_index == 1:
            if self._time_hour < previous_hour:
                self._reset_live_series()
            self._append_live_samples()
        self._set_time_slider_from_hour(self._time_hour)
        if self._time_model is None:
            self._apply_viz()
        self._update_mqtt_status()

    def _update_time_label(self):
        if self._time_label is None:
            return
        hours = int(self._time_hour)
        minutes = int(round((self._time_hour - hours) * 60.0))
        if minutes >= 60:
            hours += 1
            minutes = 0
        self._time_label.text = f"{self._time_hour:.2f} h ({hours:02d}:{minutes:02d})"

    def _update_viz_status(self, message: str | None = None):
        if self._viz_status_label is None:
            return
        if message is not None:
            self._viz_status_label.text = message
            return
        if self._viz_enabled:
            playback = f" | Playing {PLAY_SPEEDS[self._play_speed_index]}" if self._is_playing else ""
            self._viz_status_label.text = f"Enabled: {self._current_viz_mode()} at {self._time_hour:.2f}h{playback}."
        else:
            self._viz_status_label.text = "Disabled."

    def _update_telemetry_status(self):
        if self._telemetry_status_label is None:
            return
        selected = self._selected_space()
        if selected is None:
            self._telemetry_status_label.text = "No zone selected."
            return
        binding = self._telemetry_store.binding_for_zone(selected.path)
        if binding is None:
            mode_text = TELEMETRY_MODES[min(self._telemetry_mode_index, len(TELEMETRY_MODES) - 1)]
            self._telemetry_status_label.text = f"Mode: {mode_text} | No telemetry bound. Synthetic fallback active."
            return
        mode_text = TELEMETRY_MODES[min(self._telemetry_mode_index, len(TELEMETRY_MODES) - 1)]
        self._telemetry_status_label.text = (
            f"Mode: {mode_text} | Bound: {binding.sensor_id}/{binding.channel} | "
            f"source={binding.source_type} | {binding.source_ref}"
        )

    def _update_mqtt_status(self):
        if self._mqtt_status_label is not None:
            self._mqtt_status_label.text = f"MQTT: {self._mqtt_client.status}"

    def _current_viz_mode(self) -> str:
        return COLOR_MODE_PROXIES if self._viz_mode_index == 1 else COLOR_MODE_SURFACES

    def _current_comfort(self) -> ComfortBand:
        return ComfortBand(float(self._comfort_min), float(max(self._comfort_max, self._comfort_min + 0.1)))

    def _selected_space(self) -> SpaceInfo | None:
        if not self._spaces:
            return None
        return self._spaces[min(self._zone_index, len(self._spaces) - 1)]

    def _model_float(self, model) -> float:
        if hasattr(model, "get_value_as_float"):
            return float(model.get_value_as_float())
        return float(model.as_float)

    def _zone_labels(self) -> list[str]:
        return [f"{space.name}   ({space.path})" for space in self._spaces]

    def _set_time_slider_from_hour(self, value: float):
        if self._time_model is None:
            self._time_hour = max(0.0, min(24.0, value))
            self._update_time_label()
            return
        self._time_model.set_value(max(0.0, min(24.0, value)) / 24.0)

    def _time_slider_row(self, label: str, value: float):
        with ui.HStack():
            ui.Label(label, width=135)
            slider = ui.FloatSlider(
                precision=3,
                style={
                    "draw_mode": ui.SliderDrawMode.FILLED,
                    "background_color": 0xFF303030,
                    "secondary_color": 0xFF5A8FD8,
                },
            )
            slider.model.set_value(max(0.0, min(24.0, value)) / 24.0)
            slider.model.add_value_changed_fn(self._on_time_slider_changed)
            self._time_label = ui.Label("", width=100)
            return slider.model

    def _float_slider_row(self, label: str, value: float, min_value: float, max_value: float):
        with ui.HStack():
            ui.Label(label, width=135)
            slider = ui.FloatSlider(
                min=min_value,
                max=max_value,
                precision=2,
                style={
                    "draw_mode": ui.SliderDrawMode.FILLED,
                    "background_color": 0xFF252D38,
                    "secondary_color": 0xFF2DE68F,
                },
            )
            slider.model.set_value(value)
            slider.model.add_value_changed_fn(self._on_comfort_changed)
            label_widget = ui.Label(f"{value:.1f}", width=48)

            def _sync_label(model):
                label_widget.text = f"{self._model_float(model):.1f}"

            slider.model.add_value_changed_fn(_sync_label)
            return slider.model

    def _legend_chip(self, label: str, color: int):
        with ui.HStack(width=0):
            ui.Rectangle(width=16, height=14, style={"background_color": color, "border_radius": 3})
            ui.Label(label, width=76, style={"color": 0xFFC5D1DF})

    def _update_current_value(self):
        if self._current_value_label is None:
            return
        selected = self._selected_space()
        if selected is None:
            self._current_value_label.text = "No active thermal value."
            return
        signal = self._active_signal_for_space(selected.path)
        if signal is None:
            self._current_value_label.text = "No signal for selected zone."
            return
        value = _value_at_hour(signal, self._time_hour)
        comfort = self._current_comfort()
        status = comfort_status(value, comfort)
        delta = comfort_delta(value, comfort)
        self._current_value_label.text = (
            f"Current: {value:.1f} C | Status: {status} | Delta to comfort: {delta:+.1f} C"
        )
        try:
            self._current_value_label.style = {"color": comfort_hex(value, comfort)}
        except Exception:
            pass

    def _active_signal_for_space(self, space_path: str):
        return self._telemetry_store.series_for_zone(space_path) or self._signals.get(space_path)

    def _active_signal_map(self) -> dict[str, object]:
        active = dict(self._signals)
        for zone_path in self._telemetry_store.active_zone_paths():
            series = self._telemetry_store.series_for_zone(zone_path)
            if series is not None:
                active[zone_path] = series
        return active

    def _sync_telemetry_models(self):
        if self._telemetry_mode_model is not None:
            try:
                self._telemetry_mode_index = self._telemetry_mode_model.get_item_value_model().as_int
            except AttributeError:
                self._telemetry_mode_index = 0
        if self._telemetry_sensor_model is not None:
            self._telemetry_sensor_id = self._telemetry_sensor_model.get_value_as_string()
        if self._telemetry_channel_model is not None:
            self._telemetry_channel = self._telemetry_channel_model.get_value_as_string()
        if self._telemetry_path_model is not None:
            self._telemetry_path = self._telemetry_path_model.get_value_as_string()
        if self._mqtt_host_model is not None:
            self._mqtt_host = self._mqtt_host_model.get_value_as_string() or "127.0.0.1"
        if self._mqtt_port_model is not None:
            try:
                self._mqtt_port = int(self._mqtt_port_model.as_int)
            except AttributeError:
                self._mqtt_port = int(self._mqtt_port_model.get_value_as_int())
        if self._mqtt_topic_model is not None:
            self._mqtt_topic = self._mqtt_topic_model.get_value_as_string() or "aec/#"

    def _load_csv_for_selected_zone(self):
        self._load_dataset("csv")

    def _load_json_for_selected_zone(self):
        self._load_dataset("json")

    def _generate_live_stub_for_selected_zone(self):
        selected = self._selected_space()
        if selected is None:
            self._set_telemetry_message("Select a zone before generating telemetry.")
            return
        self._sync_telemetry_models()
        sensor_id = self._telemetry_sensor_id or f"sensor.{selected.name}"
        channel = self._telemetry_channel or "temp"
        self._telemetry_mode_index = 1
        if self._telemetry_mode_model is not None:
            self._telemetry_mode_model.get_item_value_model().set_value(self._telemetry_mode_index)
        self._live_sources[selected.path] = {
            "sensor_id": sensor_id,
            "channel": channel,
            "seed": selected.path,
            "source_type": self._live_stub_source.source_type,
            "source_ref": f"live://{sensor_id}/{channel}",
        }
        self._telemetry_store.bind_live_zone(
            selected.path,
            sensor_id,
            channel,
            source_type=self._live_stub_source.source_type,
            source_ref=f"live://{sensor_id}/{channel}",
        )
        self._telemetry_store.reset_live_zone(selected.path)
        self._append_live_sample_for_zone(selected.path, force=True)
        self._persist_zone_binding(
            selected.path,
            sensor_id,
            channel,
            self._live_stub_source.source_type,
            f"live://{sensor_id}/{channel}",
        )
        self._update_plot()
        self._update_current_value()
        self._update_telemetry_status()
        self._set_telemetry_message(
            f"Live stub bound to {selected.name}. Use Play/Pause below to stream samples in real time."
        )
        if self._viz_enabled:
            self._apply_viz()

    def _bind_mqtt_for_selected_zone(self):
        selected = self._selected_space()
        if selected is None:
            self._set_telemetry_message("Select a zone before binding MQTT.")
            return
        self._sync_telemetry_models()
        sensor_id = self._telemetry_sensor_id or f"sensor.{selected.name}"
        channel = self._telemetry_channel or "temp"
        self._telemetry_mode_index = 1
        if self._telemetry_mode_model is not None:
            self._telemetry_mode_model.get_item_value_model().set_value(self._telemetry_mode_index)
        self._live_sources[selected.path] = {
            "sensor_id": sensor_id,
            "channel": channel,
            "seed": selected.path,
            "source_type": "mqtt",
            "source_ref": self._mqtt_topic,
        }
        self._telemetry_store.bind_live_zone(
            selected.path,
            sensor_id,
            channel,
            source_type="mqtt",
            source_ref=self._mqtt_topic,
        )
        self._persist_zone_binding(selected.path, sensor_id, channel, "mqtt", self._mqtt_topic)
        self._update_telemetry_status()
        self._set_telemetry_message(f"MQTT binding ready for {selected.name}: {sensor_id}/{channel}")
        self._ensure_update_subscription()

    def _connect_mqtt(self):
        self._sync_telemetry_models()
        self._mqtt_client.connect(self._mqtt_host, self._mqtt_port, self._mqtt_topic)
        self._ensure_update_subscription()
        self._update_mqtt_status()

    def _disconnect_mqtt(self):
        self._mqtt_client.disconnect()
        self._maybe_release_update_subscription()
        self._update_mqtt_status()

    def _load_dataset(self, source_kind: str):
        selected = self._selected_space()
        if selected is None:
            self._set_telemetry_message("Select a zone before importing telemetry.")
            return
        self._sync_telemetry_models()
        self._telemetry_mode_index = 0
        if self._telemetry_mode_model is not None:
            self._telemetry_mode_model.get_item_value_model().set_value(self._telemetry_mode_index)
        if not self._telemetry_path.strip():
            self._set_telemetry_message("Enter a local CSV/JSON path first.")
            return
        try:
            if source_kind == "json":
                dataset = self._json_source.load(self._telemetry_path, sensor_id=self._telemetry_sensor_id or None)
            else:
                dataset = self._csv_source.load(self._telemetry_path, sensor_id=self._telemetry_sensor_id or None)
        except Exception as exc:
            carb.log_warn(f"[AEC Telemetry] Failed to load {source_kind}: {exc}")
            self._set_telemetry_message(f"Load failed: {exc}")
            return
        self._bind_dataset_to_selected_zone(dataset)

    def _bind_dataset_to_selected_zone(self, dataset):
        selected = self._selected_space()
        if selected is None:
            return
        self._live_sources.pop(selected.path, None)
        requested_channel = (self._telemetry_channel or "").strip()
        if requested_channel and requested_channel in dataset.channels:
            channel_name = requested_channel
        elif "temp" in dataset.channels:
            channel_name = "temp"
        elif "temperature" in dataset.channels:
            channel_name = "temperature"
        else:
            channel_name = next(iter(dataset.channels.keys()))
        series = dataset.channels[channel_name]
        self._telemetry_store.bind_zone(selected.path, dataset.sensor_id, channel_name, series)
        self._persist_zone_binding(selected.path, dataset.sensor_id, channel_name, dataset.source_type, dataset.source_ref)
        self._update_plot()
        self._update_current_value()
        self._update_telemetry_status()
        self._set_telemetry_message(
            f"Bound {selected.name} -> {dataset.sensor_id}/{channel_name} ({dataset.source_type}, {series.value_count} samples)"
        )
        if self._viz_enabled:
            self._apply_viz()

    def _append_live_samples(self):
        for zone_path in tuple(self._live_sources.keys()):
            self._append_live_sample_for_zone(zone_path)

    def _append_live_sample_for_zone(self, zone_path: str, force: bool = False):
        config = self._live_sources.get(zone_path)
        if config is None:
            return
        if not force and self._telemetry_mode_index != 1:
            return
        if str(config.get("source_type")) != self._live_stub_source.source_type:
            return
        sensor_id = str(config["sensor_id"])
        channel = str(config["channel"])
        seed = str(config["seed"])
        value = self._live_stub_source.sample_at(sensor_id=sensor_id, hour=self._time_hour, channel=channel, seed=seed)
        self._telemetry_store.append_sample(
            zone_path,
            sensor_id,
            channel,
            self._time_hour,
            value,
            source_type=str(config["source_type"]),
            source_ref=str(config["source_ref"]),
            max_points=288,
        )

    def _reset_live_series(self):
        for zone_path in tuple(self._live_sources.keys()):
            config = self._live_sources.get(zone_path)
            if config is not None and str(config.get("source_type")) == self._live_stub_source.source_type:
                self._telemetry_store.reset_live_zone(zone_path)

    def _consume_mqtt_messages(self) -> bool:
        messages = self._mqtt_client.poll_messages()
        if not messages:
            return False
        changed = False
        latest_hour = None
        for message in messages:
            payload = message.payload_json()
            if payload is None:
                continue
            sensor_id = str(payload.get("sensor_id") or "").strip()
            if not sensor_id:
                continue
            sample_hour = self._payload_hour(payload)
            latest_hour = sample_hour if latest_hour is None else sample_hour
            bound_zone = self._zone_path_from_payload(payload)
            payload_channels = payload.get("channels") if isinstance(payload.get("channels"), dict) else {}
            for zone_path, config in self._live_sources.items():
                if str(config.get("source_type")) != "mqtt":
                    continue
                if str(config.get("sensor_id")) != sensor_id:
                    continue
                if bound_zone is not None and bound_zone != zone_path:
                    continue
                channel = str(config.get("channel") or "temp")
                value = self._payload_channel_value(payload, payload_channels, channel)
                if value is None:
                    continue
                self._telemetry_store.append_sample(
                    zone_path,
                    sensor_id,
                    channel,
                    sample_hour,
                    value,
                    source_type="mqtt",
                    source_ref=message.topic,
                    max_points=720,
                )
                changed = True
        if changed and latest_hour is not None and self._telemetry_mode_index == 1:
            self._time_hour = latest_hour
            self._set_time_slider_from_hour(self._time_hour)
        return changed

    def _payload_channel_value(self, payload: dict, payload_channels: dict, channel: str) -> float | None:
        if channel in payload and payload[channel] is not None:
            try:
                return float(payload[channel])
            except (TypeError, ValueError):
                return None
        if channel in payload_channels and payload_channels[channel] is not None:
            try:
                return float(payload_channels[channel])
            except (TypeError, ValueError):
                return None
        if channel == "temp" and "temperature" in payload:
            try:
                return float(payload["temperature"])
            except (TypeError, ValueError):
                return None
        if "value" in payload and payload["value"] is not None:
            try:
                return float(payload["value"])
            except (TypeError, ValueError):
                return None
        return None

    def _zone_path_from_payload(self, payload: dict) -> str | None:
        zone_path = payload.get("zone_path")
        if isinstance(zone_path, str) and zone_path.strip():
            return zone_path.strip()
        zone_id = payload.get("zone_id")
        if isinstance(zone_id, str) and zone_id.strip():
            for space in self._spaces:
                if space.name == zone_id.strip():
                    return space.path
        return None

    def _payload_hour(self, payload: dict) -> float:
        timestamp = payload.get("timestamp")
        if timestamp is None:
            now = datetime.now()
            return now.hour + now.minute / 60.0 + now.second / 3600.0
        if isinstance(timestamp, (int, float)):
            value = float(timestamp)
            if value > 1_000_000_000_000:
                value /= 1000.0
            if value > 100000.0:
                dt = datetime.fromtimestamp(value)
                return dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            if value > 24.0:
                return (value / 3600.0) % 24.0
            return max(0.0, min(24.0, value))
        if isinstance(timestamp, str):
            text = timestamp.strip()
            if ":" in text:
                parts = [int(part) for part in text.split(":")]
                while len(parts) < 3:
                    parts.append(0)
                return parts[0] + parts[1] / 60.0 + parts[2] / 3600.0
            try:
                return self._payload_hour({"timestamp": float(text)})
            except ValueError:
                now = datetime.now()
                return now.hour + now.minute / 60.0 + now.second / 3600.0
        now = datetime.now()
        return now.hour + now.minute / 60.0 + now.second / 3600.0

    def _ensure_update_subscription(self):
        if self._update_subscription is None:
            self._last_update_seconds = time.perf_counter()
            self._update_subscription = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
                self._on_update,
                name="AEC Thermal playback",
            )

    def _maybe_release_update_subscription(self):
        if self._is_playing or self._mqtt_client.is_connected:
            return
        self._update_subscription = None

    def _persist_zone_binding(self, zone_path: str, sensor_id: str, channel: str, source_type: str, source_ref: str):
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return
        prim = stage.GetPrimAtPath(zone_path)
        if not prim.IsValid():
            return
        prim.CreateAttribute("aec:telemetry:sensorId", Sdf.ValueTypeNames.String).Set(sensor_id)
        prim.CreateAttribute("aec:telemetry:channel", Sdf.ValueTypeNames.String).Set(channel)
        prim.CreateAttribute("aec:telemetry:sourceType", Sdf.ValueTypeNames.String).Set(source_type)
        prim.CreateAttribute("aec:telemetry:sourceRef", Sdf.ValueTypeNames.String).Set(source_ref)

    def _set_telemetry_message(self, message: str):
        if self._telemetry_status_label is not None:
            self._telemetry_status_label.text = message


def _value_at_hour(signal, hour: float) -> float:
    timeline = signal.timeline_hours
    values = signal.temperature_c
    if not timeline or not values:
        return 0.0
    clamped = max(0.0, min(24.0, float(hour)))
    nearest = min(range(len(timeline)), key=lambda index: abs(timeline[index] - clamped))
    return float(values[nearest])
