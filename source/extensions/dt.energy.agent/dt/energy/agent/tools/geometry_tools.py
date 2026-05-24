from __future__ import annotations

from .aec_modeling_tools import create_aec_block


def create_thermal_zone_box(name: str = "Zone_01", width: float = 10.0, depth: float = 8.0, height: float = 3.0) -> dict:
    return create_aec_block(width=width, depth=depth, height=height, name=name.replace("Zone", "Block"))
