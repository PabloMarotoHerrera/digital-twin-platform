from __future__ import annotations

from .aec_inspection import validate_aec_blocks
from .aec_modeling_tools import assign_basic_energy_metadata


def assign_basic_thermal_properties(prim_path: str) -> dict:
    return assign_basic_energy_metadata(prim_path)


def validate_energy_model() -> dict:
    return validate_aec_blocks()

