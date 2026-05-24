from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

from .model_access import SpaceInfo


@dataclass(frozen=True)
class ThermalSignal:
    space_path: str
    timeline_hours: tuple[float, ...]
    temperature_c: tuple[float, ...]
    params: dict[str, float]


class ThermalSignalProvider:
    def __init__(self, step_minutes: int = 15):
        self._step_minutes = max(1, int(step_minutes))
        self._cache: dict[str, ThermalSignal] = {}

    @property
    def step_minutes(self) -> int:
        return self._step_minutes

    def generate(self, spaces: list[SpaceInfo]) -> dict[str, ThermalSignal]:
        result: dict[str, ThermalSignal] = {}
        for space in spaces:
            result[space.path] = self.signal_for_space(space)
        return result

    def signal_for_space(self, space: SpaceInfo) -> ThermalSignal:
        cached = self._cache.get(space.path)
        if cached is not None:
            return cached

        seed = _stable_seed(space.path)
        rng = random.Random(seed)
        timeline = tuple(i * self._step_minutes / 60.0 for i in range(int(24 * 60 / self._step_minutes) + 1))

        height_offset = 0.0
        if space.bounds_min is not None:
            height_offset = max(0.0, space.bounds_min[2]) * 0.18

        baseline = 21.0 + rng.uniform(-0.7, 1.0) + height_offset
        amplitude = 1.7 + rng.uniform(0.2, 1.1)
        solar_peak = 15.0 + rng.uniform(-1.0, 1.4)
        occupancy_peak = 9.5 + rng.uniform(-0.7, 0.8)
        evening_peak = 19.0 + rng.uniform(-0.8, 0.9)
        noise = 0.12 + rng.uniform(0.0, 0.18)

        values: list[float] = []
        for index, hour in enumerate(timeline):
            night_cooling = -0.75 * math.cos((hour / 24.0) * 2.0 * math.pi)
            solar_gain = 1.35 * _gaussian(hour, solar_peak, 3.2)
            morning_load = 0.42 * _gaussian(hour, occupancy_peak, 1.6)
            evening_load = 0.55 * _gaussian(hour, evening_peak, 2.1)
            hvac_setback = -0.35 * _gaussian(hour, 5.0, 2.8)
            slow_wave = amplitude * 0.45 * math.sin(((hour - 13.0) / 24.0) * 2.0 * math.pi)
            micro_noise = random.Random(seed + index * 7919).uniform(-noise, noise)
            value = baseline + slow_wave + night_cooling + solar_gain + morning_load + evening_load + hvac_setback + micro_noise
            values.append(round(value, 3))

        params = {
            "baseline": round(baseline, 3),
            "amplitude": round(amplitude, 3),
            "phase": round(solar_peak, 3),
            "solar_peak": round(solar_peak, 3),
            "occupancy_peak": round(occupancy_peak, 3),
            "noise": round(noise, 3),
            "t_min": min(values),
            "t_max": max(values),
            "t_avg": round(sum(values) / len(values), 3),
        }
        signal = ThermalSignal(
            space_path=space.path,
            timeline_hours=timeline,
            temperature_c=tuple(values),
            params=params,
        )
        self._cache[space.path] = signal
        return signal


def _stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _gaussian(hour: float, center: float, width: float) -> float:
    return math.exp(-0.5 * ((hour - center) / max(width, 0.001)) ** 2)
