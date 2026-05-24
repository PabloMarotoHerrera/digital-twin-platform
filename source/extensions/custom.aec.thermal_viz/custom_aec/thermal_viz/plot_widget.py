from __future__ import annotations

from statistics import fmean

import omni.ui as ui

from .signals import ThermalSignal
from .thermal_style import ComfortBand, comfort_hex, comfort_status


CHART_MIN_WIDTH = 360
CHART_HEIGHT = 210
PLOT_LEFT = 0
PLOT_RIGHT = 0
PLOT_TOP = 10
PLOT_BOTTOM = 34
GRID_COLOR = 0x223B4B63
AXIS_COLOR = 0x556A7C99
CURVE_GLOW = 0x3327F0FF
CURVE_COLOR = 0xFF31EAFF
MARKER_COLOR = 0xFFF5F7FF
TEXT_DIM = 0xFF8E98A6
TEXT_BRIGHT = 0xFFD8E6F5
PANEL_BG = 0xFF2B2B2B
PLOT_BG = 0xFF1F1F1F


class ThermalPlotWidget:
    def __init__(self):
        self._signal: ThermalSignal | None = None
        self._current_hour = 12.0
        self._comfort = ComfortBand()
        self._title_label: ui.Label | None = None
        self._comfort_label: ui.Label | None = None
        self._summary_label: ui.Label | None = None
        self._current_label: ui.Label | None = None
        self._chart_frame: ui.Frame | None = None
        with ui.VStack(spacing=4, height=0):
            with ui.HStack(height=22):
                self._title_label = ui.Label(
                    "THERMAL TWIN - TEMPERATURE",
                    style={"font_size": 12, "color": TEXT_BRIGHT},
                )
                ui.Spacer()
                self._comfort_label = ui.Label(
                    "",
                    style={"font_size": 12, "color": 0xFF8DFF38},
                )
            self._chart_frame = ui.Frame(
                width=ui.Percent(100),
                height=CHART_HEIGHT,
                style={"background_color": PANEL_BG, "border_radius": 8},
            )
            self._chart_frame.set_build_fn(self._build_chart)
            self._chart_frame.set_computed_content_size_changed_fn(self._on_chart_size_changed)
            self._summary_label = ui.Label("", word_wrap=True, style={"color": TEXT_BRIGHT})
            self._current_label = ui.Label("", word_wrap=True, style={"font_size": 14})

        self._refresh_text()

    def set_signal(self, signal: ThermalSignal | None, current_hour: float, comfort: ComfortBand):
        self._signal = signal
        self._current_hour = max(0.0, min(24.0, float(current_hour)))
        self._comfort = comfort
        self._refresh_text()
        if self._chart_frame is not None:
            self._chart_frame.rebuild()

    def _refresh_text(self):
        comfort_text = f"COMFORT {self._comfort.min_c:.1f}-{self._comfort.max_c:.1f}C"
        if self._title_label is not None:
            self._title_label.text = "THERMAL TWIN - TEMPERATURE"
        if self._comfort_label is not None:
            self._comfort_label.text = comfort_text
        if self._signal is None:
            if self._summary_label is not None:
                self._summary_label.text = "No thermal signal loaded."
            if self._current_label is not None:
                self._current_label.text = ""
            return

        values = self._signal.temperature_c
        current = _value_at_hour(self._signal, self._current_hour)
        status = comfort_status(current, self._comfort)
        current_hex = comfort_hex(current, self._comfort)
        if self._summary_label is not None:
            self._summary_label.text = (
                f"Temperature 24h | now {current:.1f} C | min {min(values):.1f} C | "
                f"max {max(values):.1f} C | avg {fmean(values):.1f} C | {comfort_text}"
            )
        if self._current_label is not None:
            self._current_label.text = (
                f"Current: {current:.1f} C | Status: {status} | "
                f"Hour: {self._current_hour:.2f} h"
            )
            self._current_label.style = {"color": current_hex}

    def _build_chart(self):
        chart_width = self._current_chart_width()
        plot_width = self._plot_width(chart_width)
        plot_height = self._plot_height()

        with ui.ZStack(content_clipping=True):
            ui.Rectangle(style={"background_color": PLOT_BG, "border_radius": 6})
            with ui.CanvasFrame(compatibility=0):
                with ui.ZStack(content_clipping=True):
                    if self._signal is None or not self._signal.temperature_c:
                        self._build_empty_state(chart_width, plot_width, plot_height)
                        return

                    timeline = self._signal.timeline_hours
                    values = self._signal.temperature_c
                    data_min = min(values)
                    data_max = max(values)
                    margin = max(0.6, (data_max - data_min) * 0.15)
                    y_min = min(data_min - margin, self._comfort.min_c - 0.35)
                    y_max = max(data_max + margin, self._comfort.max_c + 0.35)

                    self._draw_grid(chart_width, plot_width, plot_height)
                    self._draw_comfort_band(y_min, y_max, chart_width, plot_width, plot_height)

                    anchors = [
                        self._anchor_for_point(hour, value, y_min, y_max, chart_width, plot_width, plot_height)
                        for hour, value in zip(timeline, values)
                    ]
                    for start, end in zip(anchors, anchors[1:]):
                        ui.FreeLine(
                            start,
                            end,
                            alignment=ui.Alignment.UNDEFINED,
                            style={"color": CURVE_GLOW, "border_width": 5},
                        )
                    for start, end in zip(anchors, anchors[1:]):
                        ui.FreeLine(
                            start,
                            end,
                            alignment=ui.Alignment.UNDEFINED,
                            style={"color": CURVE_COLOR, "border_width": 2},
                        )

                    current_value = _value_at_hour(self._signal, self._current_hour)
                    marker_x = self._x_for_hour(self._current_hour, chart_width, plot_width)
                    marker_top = self._anchor_at(marker_x, PLOT_TOP)
                    marker_bottom = self._anchor_at(marker_x, PLOT_TOP + plot_height)
                    ui.FreeLine(
                        marker_top,
                        marker_bottom,
                        alignment=ui.Alignment.UNDEFINED,
                        style={"color": 0x55DFF7FF, "border_width": 1},
                    )

                    with ui.Placer(
                        offset_x=marker_x - 5,
                        offset_y=self._y_for_value(current_value, y_min, y_max, plot_height) - 5,
                    ):
                        ui.Circle(
                            width=10,
                            height=10,
                            style={
                                "background_color": comfort_hex(current_value, self._comfort),
                                "border_color": MARKER_COLOR,
                                "border_width": 2,
                            },
                        )

                    self._draw_y_labels(y_min, y_max, plot_height)
                    self._draw_x_labels(plot_width, plot_height)

    def _build_empty_state(self, chart_width: float, plot_width: float, plot_height: float):
        self._draw_grid(chart_width, plot_width, plot_height)
        with ui.Placer(offset_x=18, offset_y=CHART_HEIGHT / 2 - 8):
            ui.Label("No zone selected.", style={"color": TEXT_DIM, "font_size": 13})

    def _draw_grid(self, chart_width: float, plot_width: float, plot_height: float):
        with ui.Placer(offset_x=PLOT_LEFT, offset_y=PLOT_TOP):
            ui.Rectangle(width=plot_width, height=plot_height, style={"background_color": 0xFF242424})

        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            x = PLOT_LEFT + plot_width * fraction
            with ui.Placer(offset_x=x, offset_y=PLOT_TOP):
                ui.Rectangle(width=1, height=plot_height, style={"background_color": GRID_COLOR})
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = PLOT_TOP + plot_height * fraction
            with ui.Placer(offset_x=PLOT_LEFT, offset_y=y):
                ui.Rectangle(width=plot_width, height=1, style={"background_color": GRID_COLOR})

        with ui.Placer(offset_x=PLOT_LEFT, offset_y=PLOT_TOP + plot_height):
            ui.Rectangle(width=plot_width, height=1, style={"background_color": AXIS_COLOR})
        with ui.Placer(offset_x=PLOT_LEFT, offset_y=PLOT_TOP):
            ui.Rectangle(width=1, height=plot_height, style={"background_color": AXIS_COLOR})

    def _draw_comfort_band(self, y_min: float, y_max: float, chart_width: float, plot_width: float, plot_height: float):
        band_top = self._y_for_value(self._comfort.max_c, y_min, y_max, plot_height)
        band_bottom = self._y_for_value(self._comfort.min_c, y_min, y_max, plot_height)
        with ui.Placer(offset_x=PLOT_LEFT, offset_y=band_top):
            ui.Rectangle(
                width=plot_width,
                height=max(2, band_bottom - band_top),
                style={"background_color": 0x143A7A3A},
            )

        for target in (self._comfort.min_c, self._comfort.max_c):
            y = self._y_for_value(target, y_min, y_max, plot_height)
            start = self._anchor_at(PLOT_LEFT, y)
            end = self._anchor_at(PLOT_LEFT + plot_width, y)
            ui.FreeLine(
                start,
                end,
                alignment=ui.Alignment.UNDEFINED,
                style={"color": 0x553EF580, "border_width": 1},
            )

    def _draw_y_labels(self, y_min: float, y_max: float, plot_height: float):
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            value = y_max - (y_max - y_min) * fraction
            y = PLOT_TOP + plot_height * fraction - 7
            with ui.Placer(offset_x=4, offset_y=y):
                ui.Label(f"{value:>4.1f}", style={"font_size": 11, "color": TEXT_DIM})

    def _draw_x_labels(self, plot_width: float, plot_height: float):
        label_y = PLOT_TOP + plot_height + 6
        for hour, fraction in ((0, 0.0), (6, 0.25), (12, 0.5), (18, 0.75), (24, 1.0)):
            x = PLOT_LEFT + plot_width * fraction
            offset = -10
            if hour == 0:
                offset = 0
            elif hour == 24:
                offset = -22
            with ui.Placer(offset_x=x + offset, offset_y=label_y):
                ui.Label(f"{hour}H", style={"font_size": 11, "color": TEXT_DIM})

    def _anchor_for_point(self, hour: float, value: float, y_min: float, y_max: float, chart_width: float, plot_width: float, plot_height: float):
        return self._anchor_at(
            self._x_for_hour(hour, chart_width, plot_width),
            self._y_for_value(value, y_min, y_max, plot_height),
        )

    def _anchor_at(self, x: float, y: float):
        with ui.Placer(offset_x=float(x), offset_y=float(y)):
            return ui.Rectangle(width=2, height=2, style={"background_color": 0x01FFFFFF})

    def _x_for_hour(self, hour: float, chart_width: float, plot_width: float) -> float:
        clamped = max(0.0, min(24.0, float(hour)))
        return PLOT_LEFT + (clamped / 24.0) * plot_width

    def _y_for_value(self, value: float, y_min: float, y_max: float, plot_height: float) -> float:
        span = max(0.001, y_max - y_min)
        normalized = (float(value) - y_min) / span
        normalized = max(0.0, min(1.0, normalized))
        return PLOT_TOP + (1.0 - normalized) * plot_height

    def _plot_width(self, chart_width: float) -> float:
        return max(220.0, chart_width - PLOT_LEFT - PLOT_RIGHT)

    def _plot_height(self) -> float:
        return CHART_HEIGHT - PLOT_TOP - PLOT_BOTTOM

    def _on_chart_size_changed(self, *_args):
        if self._chart_frame is None:
            return
        self._chart_frame.rebuild()

    def _current_chart_width(self) -> float:
        if self._chart_frame is None:
            return CHART_MIN_WIDTH
        computed = float(getattr(self._chart_frame, "computed_width", 0.0) or 0.0)
        return max(CHART_MIN_WIDTH, computed - 2.0 if computed > 2.0 else computed)


def _value_at_hour(signal: ThermalSignal, hour: float) -> float:
    timeline = signal.timeline_hours
    values = signal.temperature_c
    if not timeline or not values:
        return 0.0
    clamped = max(0.0, min(24.0, float(hour)))
    nearest = min(range(len(timeline)), key=lambda index: abs(timeline[index] - clamped))
    return float(values[nearest])
