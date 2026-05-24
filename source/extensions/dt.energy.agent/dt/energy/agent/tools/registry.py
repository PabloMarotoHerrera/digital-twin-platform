from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .aec_inspection import analyze_scene, get_selected_aec_element, inspect_surface_geometry, list_aec_blocks, validate_aec_blocks
from .aec_modeling_tools import assign_basic_energy_metadata, create_aec_block
from .dxf_tools import (
    create_sketch_from_dxf_polyline,
    extract_dxf_snap_points,
    get_nearest_snap_point,
    import_dxf_reference,
    list_dxf_references,
    trace_dxf_outline_to_sketch,
)
from .idf_tools import export_idf_placeholder
from .scene_tools import get_selected_prims, inspect_current_stage
from .simulation_tools import run_energyplus
from .thermal_sync_tools import sync_aec_block_to_thermalviz, sync_all_blocks_to_thermalviz
from .sketching_tools import (
    close_current_sketch,
    convert_closed_curve_to_thermal_zone,
    create_sketch_rectangle_and_extrude,
    create_sketch_rectangle,
    extrude_sketch_to_block,
    extrude_selected_sketch,
    find_blocks_from_sketch,
    get_block_source_sketch,
    get_sketch_footprint_points,
    list_sketches,
    modify_selected_sketch_and_rebuild,
    modify_sketch_and_rebuild,
    modify_sketch_rectangle,
    rebuild_block_from_sketch,
    start_sketch_mode,
    validate_sketch,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    callable: Callable
    description: str
    input_schema: dict
    category: str
    requires_confirmation: bool = False
    implemented: bool = True
    dangerous: bool = False


def _empty_schema():
    return {"type": "object", "properties": {}, "additionalProperties": False}


def _box_schema():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "width": {"type": "number", "exclusiveMinimum": 0},
            "depth": {"type": "number", "exclusiveMinimum": 0},
            "height": {"type": "number", "exclusiveMinimum": 0},
        },
        "required": ["width", "depth", "height"],
        "additionalProperties": False,
    }


def _prim_schema():
    return {
        "type": "object",
        "properties": {"prim_path": {"type": "string"}},
        "required": ["prim_path"],
        "additionalProperties": False,
    }


def _output_schema():
    return {
        "type": "object",
        "properties": {"output_path": {"type": "string"}},
        "required": ["output_path"],
        "additionalProperties": False,
    }


def _simulation_schema():
    return {
        "type": "object",
        "properties": {"idf_path": {"type": "string"}, "weather_path": {"type": "string"}},
        "required": ["idf_path", "weather_path"],
        "additionalProperties": False,
    }


def _sketch_rect_schema():
    return {
        "type": "object",
        "properties": {"width": {"type": "number"}, "depth": {"type": "number"}},
        "required": ["width", "depth"],
        "additionalProperties": False,
    }


def _height_schema():
    return {
        "type": "object",
        "properties": {"height": {"type": "number"}},
        "required": ["height"],
        "additionalProperties": False,
    }


def _sketch_path_schema():
    return {
        "type": "object",
        "properties": {"sketch_path": {"type": "string"}},
        "required": [],
        "additionalProperties": False,
    }


def _extrude_sketch_schema():
    return {
        "type": "object",
        "properties": {"sketch_path": {"type": "string"}, "height": {"type": "number", "exclusiveMinimum": 0}},
        "required": ["sketch_path", "height"],
        "additionalProperties": False,
    }


def _modify_sketch_schema():
    return {
        "type": "object",
        "properties": {
            "sketch_path": {"type": "string"},
            "width": {"type": "number", "exclusiveMinimum": 0},
            "depth": {"type": "number", "exclusiveMinimum": 0},
        },
        "required": ["sketch_path", "width", "depth"],
        "additionalProperties": False,
    }


def _modify_selected_sketch_schema():
    return {
        "type": "object",
        "properties": {
            "width": {"type": "number", "exclusiveMinimum": 0},
            "depth": {"type": "number", "exclusiveMinimum": 0},
        },
        "required": ["width", "depth"],
        "additionalProperties": False,
    }


def _block_path_schema():
    return {
        "type": "object",
        "properties": {"block_path": {"type": "string"}},
        "required": [],
        "additionalProperties": False,
    }


def _surface_path_schema():
    return {
        "type": "object",
        "properties": {"surface_path": {"type": "string"}},
        "required": [],
        "additionalProperties": False,
    }


def _dxf_import_schema():
    return {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "scale": {"type": "number", "exclusiveMinimum": 0},
            "z": {"type": "number"},
        },
        "required": ["file_path"],
        "additionalProperties": False,
    }


def _dxf_reference_schema():
    return {
        "type": "object",
        "properties": {"reference_path": {"type": "string"}},
        "required": [],
        "additionalProperties": False,
    }


def _nearest_snap_schema():
    return {
        "type": "object",
        "properties": {
            "world_position": {},
            "max_distance": {"type": "number", "minimum": 0},
        },
        "required": ["world_position"],
        "additionalProperties": False,
    }


def _dxf_polyline_schema():
    return {
        "type": "object",
        "properties": {"reference_path": {"type": "string"}, "polyline_id": {"type": "string"}},
        "required": ["reference_path", "polyline_id"],
        "additionalProperties": False,
    }


TOOLS = [
    ToolSpec("analyze_scene", analyze_scene, "Analyze AEC blocks, spaces, surfaces, materials, and selection.", _empty_schema(), "scene"),
    ToolSpec("inspect_current_stage", inspect_current_stage, "Compatibility alias for raw stage inspection.", _empty_schema(), "scene"),
    ToolSpec("get_selected_prims", get_selected_prims, "Compatibility raw selected prim paths.", _empty_schema(), "scene"),
    ToolSpec("get_selected_aec_element", get_selected_aec_element, "Describe the selected AEC element.", _empty_schema(), "scene"),
    ToolSpec("inspect_surface_geometry", inspect_surface_geometry, "Inspect mesh points, face indices, bbox, and footprint match for an AEC surface.", _surface_path_schema(), "scene"),
    ToolSpec("create_aec_block", create_aec_block, "Create a primitive AEC block through the existing modeling helpers.", _box_schema(), "aec_modeling"),
    ToolSpec("create_thermal_zone_box", create_aec_block, "Compatibility alias: creates an AEC primitive block, not /ThermalZones.", _box_schema(), "aec_modeling"),
    ToolSpec("list_aec_blocks", list_aec_blocks, "List detected AEC blocks.", _empty_schema(), "aec_modeling"),
    ToolSpec("validate_aec_blocks", validate_aec_blocks, "Validate AEC blocks for placeholder IDF export readiness.", _empty_schema(), "aec_modeling"),
    ToolSpec("validate_energy_model", validate_aec_blocks, "Compatibility alias for AEC energy validation.", _empty_schema(), "thermal"),
    ToolSpec("assign_basic_energy_metadata", assign_basic_energy_metadata, "Assign basic aec:* energy metadata.", _prim_schema(), "thermal"),
    ToolSpec("assign_basic_thermal_properties", assign_basic_energy_metadata, "Compatibility alias for aec:* energy metadata.", _prim_schema(), "thermal"),
    ToolSpec("sync_aec_block_to_thermalviz", sync_aec_block_to_thermalviz, "Synchronize one AEC block with energy metadata, thermal material, and ThermalViz registry.", _block_path_schema(), "thermal"),
    ToolSpec("sync_all_blocks_to_thermalviz", sync_all_blocks_to_thermalviz, "Synchronize all AEC blocks under /World/Building with ThermalViz readiness metadata.", _empty_schema(), "thermal"),
    ToolSpec("export_idf_placeholder", export_idf_placeholder, "Export a placeholder IDF summary from AEC blocks and spaces.", _output_schema(), "idf"),
    ToolSpec("export_idf", export_idf_placeholder, "Compatibility alias for placeholder IDF export.", _output_schema(), "idf"),
    ToolSpec("run_energyplus", run_energyplus, "Future EnergyPlus runner. Disabled in this MVP.", _simulation_schema(), "simulation", requires_confirmation=True, dangerous=True),
    ToolSpec("start_sketch_mode", start_sketch_mode, "Future DesignBuilder-like sketch mode entry point.", _empty_schema(), "sketching", implemented=False),
    ToolSpec("list_sketches", list_sketches, "List BasisCurves sketches and extrusion readiness.", _empty_schema(), "sketching"),
    ToolSpec("create_sketch_rectangle", create_sketch_rectangle, "Create an AEC rectangle sketch under /World/Building/Sketches.", _sketch_rect_schema(), "sketching"),
    ToolSpec("validate_sketch", validate_sketch, "Validate a BasisCurves sketch for extrusion.", _sketch_path_schema(), "sketching"),
    ToolSpec("get_sketch_footprint_points", get_sketch_footprint_points, "Return real sketch footprint points in stage/world coordinates.", _sketch_path_schema(), "sketching"),
    ToolSpec("find_blocks_from_sketch", find_blocks_from_sketch, "Find AEC blocks related to a source sketch.", _sketch_path_schema(), "sketching"),
    ToolSpec("get_block_source_sketch", get_block_source_sketch, "Read the source sketch relationship from an AEC block.", _block_path_schema(), "sketching"),
    ToolSpec("extrude_sketch_to_block", extrude_sketch_to_block, "Extrude a closed sketch to an AEC block.", _extrude_sketch_schema(), "sketching"),
    ToolSpec("extrude_selected_sketch", extrude_selected_sketch, "Extrude the selected sketch to an AEC block.", _height_schema(), "sketching"),
    ToolSpec("modify_sketch_rectangle", modify_sketch_rectangle, "Resize an existing rectangle sketch.", _modify_sketch_schema(), "sketching"),
    ToolSpec("modify_sketch_and_rebuild", modify_sketch_and_rebuild, "Resize a rectangle sketch and rebuild associated AEC blocks.", _modify_sketch_schema(), "sketching"),
    ToolSpec("modify_selected_sketch_and_rebuild", modify_selected_sketch_and_rebuild, "Resize the selected rectangle sketch and rebuild associated AEC blocks.", _modify_selected_sketch_schema(), "sketching"),
    ToolSpec("rebuild_block_from_sketch", rebuild_block_from_sketch, "Rebuild an extruded block from its source sketch relationship.", _block_path_schema(), "sketching"),
    ToolSpec("create_sketch_rectangle_and_extrude", create_sketch_rectangle_and_extrude, "Create a rectangle sketch and immediately extrude it.", _box_schema(), "sketching"),
    ToolSpec("close_current_sketch", close_current_sketch, "Future close-current-contour tool.", _empty_schema(), "sketching", implemented=False),
    ToolSpec("convert_closed_curve_to_thermal_zone", convert_closed_curve_to_thermal_zone, "Future closed-curve to thermal-zone conversion tool.", _empty_schema(), "sketching", implemented=False),
    ToolSpec("import_dxf_reference", import_dxf_reference, "Import a DXF as a drawing/snap reference under /World/Building/DXFReferences.", _dxf_import_schema(), "sketching"),
    ToolSpec("list_dxf_references", list_dxf_references, "List imported DXF drawing references.", _empty_schema(), "sketching"),
    ToolSpec("extract_dxf_snap_points", extract_dxf_snap_points, "List stored snap vertices/endpoints for a DXF reference.", _dxf_reference_schema(), "sketching"),
    ToolSpec("get_nearest_snap_point", get_nearest_snap_point, "Find the nearest enabled DXF snap point to a world position.", _nearest_snap_schema(), "sketching"),
    ToolSpec("create_sketch_from_dxf_polyline", create_sketch_from_dxf_polyline, "Future DXF polyline to sketch conversion.", _dxf_polyline_schema(), "sketching", implemented=False),
    ToolSpec("trace_dxf_outline_to_sketch", trace_dxf_outline_to_sketch, "Future automatic DXF outline tracing.", _dxf_reference_schema(), "sketching", implemented=False),
]

_TOOL_BY_NAME = {tool.name: tool for tool in TOOLS}


def get_tool(name: str) -> ToolSpec | None:
    return _TOOL_BY_NAME.get(name)


def tool_schemas() -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "category": tool.category,
            "dangerous": tool.dangerous,
            "requires_confirmation": tool.requires_confirmation,
            "implemented": tool.implemented,
        }
        for tool in TOOLS
    ]
