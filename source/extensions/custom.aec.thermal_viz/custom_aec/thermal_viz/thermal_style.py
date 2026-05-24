from __future__ import annotations

from dataclasses import dataclass

from pxr import Gf


@dataclass(frozen=True)
class ComfortBand:
    min_c: float = 21.0
    max_c: float = 24.0

    @property
    def midpoint(self) -> float:
        return (self.min_c + self.max_c) * 0.5


def comfort_delta(value_c: float, band: ComfortBand) -> float:
    if value_c < band.min_c:
        return value_c - band.min_c
    if value_c > band.max_c:
        return value_c - band.max_c
    return 0.0


def comfort_status(value_c: float, band: ComfortBand) -> str:
    if value_c < band.min_c:
        return "Cold"
    if value_c > band.max_c:
        return "Hot"
    return "Comfort"


def comfort_color_vec3(value_c: float, band: ComfortBand) -> Gf.Vec3f:
    r, g, b, _a = comfort_color_rgba(value_c, band, alpha=1.0)
    return Gf.Vec3f(r / 255.0, g / 255.0, b / 255.0)


def comfort_color_rgba(value_c: float, band: ComfortBand, alpha: float = 1.0) -> tuple[int, int, int, int]:
    if value_c < band.min_c:
        t = _clamp((value_c - (band.min_c - 2.2)) / 2.2, 0.0, 1.0)
        if t < 0.55:
            return _lerp_rgba((12, 44, 255, alpha), (0, 188, 255, alpha), t / 0.55)
        return _lerp_rgba((0, 188, 255, alpha), (64, 255, 210, alpha), (t - 0.55) / 0.45)
    if value_c <= band.max_c:
        t = _clamp((value_c - band.min_c) / max(band.max_c - band.min_c, 0.001), 0.0, 1.0)
        return _lerp_rgba((36, 240, 255, alpha), (82, 255, 98, alpha), min(1.0, t))

    t = _clamp((value_c - band.max_c) / 2.2, 0.0, 1.0)
    if t < 0.38:
        return _lerp_rgba((82, 255, 98, alpha), (255, 220, 48, alpha), t / 0.38)
    if t < 0.72:
        return _lerp_rgba((255, 220, 48, alpha), (255, 132, 36, alpha), (t - 0.38) / 0.34)
    return _lerp_rgba((255, 132, 36, alpha), (255, 40, 76, alpha), (t - 0.72) / 0.28)


def comfort_hex(value_c: float, band: ComfortBand) -> int:
    r, g, b, a = comfort_color_rgba(value_c, band)
    return (a << 24) | (b << 16) | (g << 8) | r


def _lerp_rgba(left, right, t: float) -> tuple[int, int, int, int]:
    t = _clamp(t, 0.0, 1.0)
    return (
        int(round(left[0] * (1.0 - t) + right[0] * t)),
        int(round(left[1] * (1.0 - t) + right[1] * t)),
        int(round(left[2] * (1.0 - t) + right[2] * t)),
        int(round(float(left[3]) * 255.0 * (1.0 - t) + float(right[3]) * 255.0 * t)),
    )


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
