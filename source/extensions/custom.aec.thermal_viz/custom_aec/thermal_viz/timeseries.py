from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


InterpolationMode = Literal["nearest", "linear"]


@dataclass(frozen=True)
class TelemetrySeries:
    sensor_id: str
    channel: str
    timeline_hours: tuple[float, ...]
    temperature_c: tuple[float, ...]
    source_type: str = "unknown"
    source_ref: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def value_count(self) -> int:
        return len(self.temperature_c)

    @property
    def min_value(self) -> float:
        return min(self.temperature_c) if self.temperature_c else 0.0

    @property
    def max_value(self) -> float:
        return max(self.temperature_c) if self.temperature_c else 0.0


@dataclass(frozen=True)
class ZoneTelemetryBinding:
    zone_path: str
    sensor_id: str
    channel: str
    source_type: str
    source_ref: str = ""


@dataclass
class MutableTelemetrySeries:
    sensor_id: str
    channel: str
    timeline_hours: list[float]
    temperature_c: list[float]
    source_type: str = "unknown"
    source_ref: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_snapshot(self) -> TelemetrySeries:
        return TelemetrySeries(
            sensor_id=self.sensor_id,
            channel=self.channel,
            timeline_hours=tuple(self.timeline_hours),
            temperature_c=tuple(self.temperature_c),
            source_type=self.source_type,
            source_ref=self.source_ref,
            metadata=dict(self.metadata),
        )


class TimeSeriesStore:
    def __init__(self):
        self._zone_bindings: dict[str, ZoneTelemetryBinding] = {}
        self._series_by_key: dict[tuple[str, str], MutableTelemetrySeries] = {}

    def clear(self):
        self._zone_bindings.clear()
        self._series_by_key.clear()

    def bind_zone(self, zone_path: str, sensor_id: str, channel: str, series: TelemetrySeries):
        key = (sensor_id, channel)
        self._series_by_key[key] = MutableTelemetrySeries(
            sensor_id=series.sensor_id,
            channel=series.channel,
            timeline_hours=list(series.timeline_hours),
            temperature_c=list(series.temperature_c),
            source_type=series.source_type,
            source_ref=series.source_ref,
            metadata=dict(series.metadata),
        )
        self._zone_bindings[zone_path] = ZoneTelemetryBinding(
            zone_path=zone_path,
            sensor_id=sensor_id,
            channel=channel,
            source_type=series.source_type,
            source_ref=series.source_ref,
        )

    def bind_live_zone(self, zone_path: str, sensor_id: str, channel: str, source_type: str = "live_stub", source_ref: str = ""):
        key = (sensor_id, channel)
        existing = self._series_by_key.get(key)
        if existing is None:
            existing = MutableTelemetrySeries(
                sensor_id=sensor_id,
                channel=channel,
                timeline_hours=[],
                temperature_c=[],
                source_type=source_type,
                source_ref=source_ref,
                metadata={"mode": "live"},
            )
            self._series_by_key[key] = existing
        self._zone_bindings[zone_path] = ZoneTelemetryBinding(
            zone_path=zone_path,
            sensor_id=sensor_id,
            channel=channel,
            source_type=source_type,
            source_ref=source_ref,
        )

    def append_sample(
        self,
        zone_path: str,
        sensor_id: str,
        channel: str,
        hour: float,
        value: float,
        *,
        source_type: str = "live_stub",
        source_ref: str = "",
        max_points: int = 288,
    ):
        key = (sensor_id, channel)
        series = self._series_by_key.get(key)
        if series is None:
            series = MutableTelemetrySeries(
                sensor_id=sensor_id,
                channel=channel,
                timeline_hours=[],
                temperature_c=[],
                source_type=source_type,
                source_ref=source_ref,
                metadata={"mode": "live"},
            )
            self._series_by_key[key] = series
        self._zone_bindings[zone_path] = ZoneTelemetryBinding(
            zone_path=zone_path,
            sensor_id=sensor_id,
            channel=channel,
            source_type=source_type,
            source_ref=source_ref,
        )

        hour = max(0.0, min(24.0, float(hour)))
        value = float(value)
        if series.timeline_hours and abs(series.timeline_hours[-1] - hour) < 1e-6:
            series.temperature_c[-1] = value
        else:
            series.timeline_hours.append(hour)
            series.temperature_c.append(value)
        if max_points > 0 and len(series.timeline_hours) > max_points:
            overflow = len(series.timeline_hours) - max_points
            del series.timeline_hours[:overflow]
            del series.temperature_c[:overflow]

    def has_binding(self, zone_path: str) -> bool:
        return zone_path in self._zone_bindings

    def binding_for_zone(self, zone_path: str) -> ZoneTelemetryBinding | None:
        return self._zone_bindings.get(zone_path)

    def series_for_zone(self, zone_path: str) -> TelemetrySeries | None:
        binding = self._zone_bindings.get(zone_path)
        if binding is None:
            return None
        series = self._series_by_key.get((binding.sensor_id, binding.channel))
        return series.to_snapshot() if series is not None else None

    def value_for_zone(self, zone_path: str, hour: float, interpolation: InterpolationMode = "linear") -> float | None:
        series = self.series_for_zone(zone_path)
        if series is None:
            return None
        return sample_series(series, hour, interpolation=interpolation)

    def active_zone_paths(self) -> tuple[str, ...]:
        return tuple(sorted(self._zone_bindings.keys()))

    def reset_live_zone(self, zone_path: str):
        binding = self._zone_bindings.get(zone_path)
        if binding is None:
            return
        key = (binding.sensor_id, binding.channel)
        series = self._series_by_key.get(key)
        if series is None:
            return
        series.timeline_hours.clear()
        series.temperature_c.clear()

    def is_live_zone(self, zone_path: str) -> bool:
        binding = self._zone_bindings.get(zone_path)
        if binding is None:
            return False
        return binding.source_type.startswith("live")


def sample_series(series: TelemetrySeries, hour: float, interpolation: InterpolationMode = "linear") -> float:
    timeline = series.timeline_hours
    values = series.temperature_c
    if not timeline or not values:
        return 0.0

    target = max(0.0, min(24.0, float(hour)))
    if target <= timeline[0]:
        return float(values[0])
    if target >= timeline[-1]:
        return float(values[-1])

    if interpolation == "nearest":
        nearest = min(range(len(timeline)), key=lambda index: abs(timeline[index] - target))
        return float(values[nearest])

    for index in range(1, len(timeline)):
        left_hour = timeline[index - 1]
        right_hour = timeline[index]
        if target <= right_hour:
            left_value = float(values[index - 1])
            right_value = float(values[index])
            span = max(1e-6, right_hour - left_hour)
            t = (target - left_hour) / span
            return left_value * (1.0 - t) + right_value * t

    return float(values[-1])
