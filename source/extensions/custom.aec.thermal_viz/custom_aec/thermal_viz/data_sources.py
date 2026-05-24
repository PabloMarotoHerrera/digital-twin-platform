from __future__ import annotations

import csv
import json
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .timeseries import TelemetrySeries


@dataclass(frozen=True)
class TelemetryDataset:
    sensor_id: str
    source_type: str
    source_ref: str
    channels: dict[str, TelemetrySeries]


class TelemetrySource(ABC):
    source_type = "unknown"


class LiveTelemetrySource(TelemetrySource, ABC):
    @abstractmethod
    def sample_at(self, sensor_id: str, hour: float, channel: str = "temp", seed: str | None = None) -> float:
        raise NotImplementedError


class CsvTelemetrySource(TelemetrySource):
    source_type = "csv"

    def load(self, path: str, sensor_id: str | None = None) -> TelemetryDataset:
        file_path = Path(path)
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            if not fieldnames:
                raise ValueError("CSV without header.")
            timestamp_key = fieldnames[0]
            channel_names = [name for name in fieldnames[1:] if name]
            if not channel_names:
                raise ValueError("CSV must contain at least one value column after timestamp.")

            raw_timestamps: list[str] = []
            raw_channels: dict[str, list[float]] = {name: [] for name in channel_names}
            for row in reader:
                timestamp_text = str(row.get(timestamp_key, "")).strip()
                if not timestamp_text:
                    continue
                raw_timestamps.append(timestamp_text)
                for name in channel_names:
                    raw_channels[name].append(_coerce_float(row.get(name)))

        if not raw_timestamps:
            raise ValueError("CSV has no valid rows.")

        timeline = _normalize_timestamps(raw_timestamps)
        sid = sensor_id or file_path.stem
        channels: dict[str, TelemetrySeries] = {}
        for name, values in raw_channels.items():
            channels[name] = TelemetrySeries(
                sensor_id=sid,
                channel=name,
                timeline_hours=timeline,
                temperature_c=tuple(values),
                source_type=self.source_type,
                source_ref=str(file_path),
                metadata={"format": "csv"},
            )

        return TelemetryDataset(
            sensor_id=sid,
            source_type=self.source_type,
            source_ref=str(file_path),
            channels=channels,
        )


class JsonTelemetrySource(TelemetrySource):
    source_type = "json"

    def load(self, path: str, sensor_id: str | None = None) -> TelemetryDataset:
        file_path = Path(path)
        payload = json.loads(file_path.read_text(encoding="utf-8"))

        if isinstance(payload, dict) and "samples" in payload:
            samples = payload["samples"]
        else:
            samples = payload

        if not isinstance(samples, list) or not samples:
            raise ValueError("JSON telemetry must contain a non-empty list of samples.")

        first = samples[0]
        if not isinstance(first, dict) or "timestamp" not in first:
            raise ValueError("JSON samples must contain a 'timestamp' field.")

        channel_names = [key for key in first.keys() if key != "timestamp"]
        if not channel_names:
            raise ValueError("JSON telemetry must contain at least one data channel.")

        raw_timestamps: list[str] = []
        raw_channels: dict[str, list[float]] = {name: [] for name in channel_names}
        for sample in samples:
            raw_timestamps.append(str(sample["timestamp"]))
            for name in channel_names:
                raw_channels[name].append(_coerce_float(sample.get(name)))

        timeline = _normalize_timestamps(raw_timestamps)
        sid = sensor_id or file_path.stem
        channels = {
            name: TelemetrySeries(
                sensor_id=sid,
                channel=name,
                timeline_hours=timeline,
                temperature_c=tuple(values),
                source_type=self.source_type,
                source_ref=str(file_path),
                metadata={"format": "json"},
            )
            for name, values in raw_channels.items()
        }
        return TelemetryDataset(sensor_id=sid, source_type=self.source_type, source_ref=str(file_path), channels=channels)


class LiveStubTelemetrySource(LiveTelemetrySource):
    source_type = "live_stub"

    def generate(self, sensor_id: str, channel: str = "temp", seed: str | None = None, step_minutes: int = 5) -> TelemetryDataset:
        stable_seed = hash(seed or sensor_id) & 0xFFFFFFFF
        rng = random.Random(stable_seed)
        step_minutes = max(1, int(step_minutes))
        timeline = tuple(i * step_minutes / 60.0 for i in range(int(24 * 60 / step_minutes) + 1))
        baseline = 21.0 + rng.uniform(-1.0, 1.0)
        amplitude = 1.6 + rng.uniform(0.6, 1.3)
        phase = 13.0 + rng.uniform(-2.0, 2.0)
        values = []
        for idx, hour in enumerate(timeline):
            wave = amplitude * math.sin(((hour - phase) / 24.0) * math.tau)
            noise = random.Random(stable_seed + idx * 97).uniform(-0.18, 0.18)
            values.append(round(baseline + wave + noise, 3))

        series = TelemetrySeries(
            sensor_id=sensor_id,
            channel=channel,
            timeline_hours=timeline,
            temperature_c=tuple(values),
            source_type=self.source_type,
            source_ref=f"live://{sensor_id}/{channel}",
            metadata={"mode": "simulated-stream"},
        )
        return TelemetryDataset(
            sensor_id=sensor_id,
            source_type=self.source_type,
            source_ref=series.source_ref,
            channels={channel: series},
        )

    def sample_at(self, sensor_id: str, hour: float, channel: str = "temp", seed: str | None = None) -> float:
        stable_seed = hash(seed or sensor_id) & 0xFFFFFFFF
        rng = random.Random(stable_seed)
        baseline = 21.0 + rng.uniform(-1.0, 1.0)
        amplitude = 1.6 + rng.uniform(0.6, 1.3)
        phase = 13.0 + rng.uniform(-2.0, 2.0)
        wave = amplitude * math.sin(((hour - phase) / 24.0) * math.tau)
        noise_index = int(round(hour * 60.0 / 5.0))
        noise = random.Random(stable_seed + noise_index * 97).uniform(-0.18, 0.18)
        return round(baseline + wave + noise, 3)


def _normalize_timestamps(raw_values: list[str]) -> tuple[float, ...]:
    if not raw_values:
        return tuple()

    if any(":" in value for value in raw_values):
        return tuple(_parse_hhmmss(value) for value in raw_values)

    numeric = [float(value) for value in raw_values]
    first = numeric[0]
    if abs(first) > 100000.0:
        if abs(first) > 1_000_000_000_000:
            numeric = [value / 1000.0 for value in numeric]
        first = numeric[0]
        return tuple(max(0.0, (value - first) / 3600.0) for value in numeric)

    if any(value > 24.0 for value in numeric):
        return tuple(value / 3600.0 for value in numeric)

    return tuple(numeric)


def _parse_hhmmss(text: str) -> float:
    parts = [int(part) for part in text.strip().split(":")]
    while len(parts) < 3:
        parts.append(0)
    hour, minute, second = parts[:3]
    return hour + minute / 60.0 + second / 3600.0


def _coerce_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
