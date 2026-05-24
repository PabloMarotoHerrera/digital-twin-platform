from __future__ import annotations

from pxr import Usd

from .model_access import SpaceInfo
from .thermal_style import ComfortBand
from .timeseries import TimeSeriesStore
from .viewport_renderer import ThermalViewportRenderer


class TelemetryViewportVisualizer:
    def __init__(self):
        self._renderer = ThermalViewportRenderer()

    def clear(self, stage: Usd.Stage):
        self._renderer.clear(stage)

    def apply(
        self,
        stage: Usd.Stage,
        spaces: list[SpaceInfo],
        signals: dict[str, object],
        store: TimeSeriesStore,
        hour: float,
        comfort: ComfortBand,
        selected_space_path: str | None = None,
        mode: str = "Color surfaces",
    ) -> int:
        active = dict(signals)
        for zone_path in store.active_zone_paths():
            series = store.series_for_zone(zone_path)
            if series is not None:
                active[zone_path] = series
        return self._renderer.apply(
            stage,
            spaces,
            active,
            hour,
            mode,
            comfort,
            selected_space_path=selected_space_path,
        )
