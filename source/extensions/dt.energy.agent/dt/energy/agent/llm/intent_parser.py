from __future__ import annotations

import re
import unicodedata


DEFAULT_BLOCK_DIMS = (10.0, 8.0, 3.0)
DEFAULT_SKETCH_DIMS = (10.0, 8.0)
DEFAULT_IDF_PATH = "C:/temp/energy_model.idf"


def parse_intent(text: str) -> dict:
    normalized = normalize_text(text)
    dxf = parse_dxf_intent(normalized)
    if dxf is not None:
        return dxf
    sync = parse_thermalviz_sync_intent(normalized)
    if sync is not None:
        return sync
    for parser in (
        parse_modify_selected_sketch_and_rebuild_intent,
        parse_rebuild_selected_block_intent,
        parse_find_blocks_from_selected_sketch_intent,
        parse_create_sketch_and_extrude_intent,
        parse_create_sketch_intent,
        parse_extrude_sketch_intent,
        parse_sketch_footprint_intent,
        parse_validate_sketch_intent,
    ):
        action = parser(normalized)
        if action is not None:
            return action
    if parse_list_sketches_intent(normalized):
        return {"tool": "list_sketches", "args": {}}
    create = parse_create_block_intent(normalized)
    if create is not None:
        return create
    if parse_export_intent(normalized):
        return {"tool": "export_idf_placeholder", "args": {"output_path": DEFAULT_IDF_PATH}}
    if parse_validate_intent(normalized):
        return {"tool": "validate_aec_blocks", "args": {}}
    if parse_list_intent(normalized):
        return {"tool": "list_aec_blocks", "args": {}}
    if parse_surface_geometry_intent(normalized):
        return {"tool": "inspect_surface_geometry", "args": {}}
    if parse_selected_intent(normalized):
        return {"tool": "get_selected_aec_element", "args": {}}
    if parse_sketch_intent(normalized):
        return {"tool": "start_sketch_mode", "args": {}}
    if parse_analyze_scene_intent(normalized):
        return {"tool": "analyze_scene", "args": {}}
    return {"tool": "analyze_scene", "args": {}}


def parse_dxf_intent(text: str) -> dict | None:
    if not _has_any(text, ("dxf", "plano", "planos", "cad", "snap")):
        return None
    if _has_any(text, ("lista", "listar", "list", "muestra", "show", "hay")):
        return {"tool": "list_dxf_references", "args": {}}
    if _has_any(text, ("extrae", "extraer", "extract", "puntos", "points", "vertices", "snap")) and not _has_any(
        text, ("cercano", "nearest")
    ):
        return {"tool": "extract_dxf_snap_points", "args": {}}
    if _has_any(text, ("cercano", "nearest")):
        numbers = re.findall(r"-?\d+(?:[.,]\d+)?", text)
        position = [float(value.replace(",", ".")) for value in numbers[:3]] if len(numbers) >= 2 else [0.0, 0.0, 0.0]
        if len(position) == 2:
            position.append(0.0)
        return {"tool": "get_nearest_snap_point", "args": {"world_position": position, "max_distance": 0.25}}
    if _has_any(text, ("importa", "importar", "import", "carga", "cargar", "load")):
        path = _extract_dxf_path(text)
        args = {"file_path": path} if path else {"file_path": ""}
        return {"tool": "import_dxf_reference", "args": args}
    if _has_any(text, ("activa", "activar", "enable")) and _has_any(text, ("snap",)):
        return {"tool": "list_dxf_references", "args": {}}
    return None


def parse_create_block_intent(text: str) -> dict | None:
    if _has_any(text, ("sketch", "croquis", "planta", "rectangulo", "rectangle")):
        return None
    if not _has_any(text, ("bloque", "block", "volumen", "volume", "habitacion", "room", "zona", "zone")):
        return None
    if not _has_any(text, ("crea", "crear", "create", "haz", "hacer", "genera", "generar", "generate", "quiero", "bloque", "block")):
        return None
    width, depth, height = parse_dimensions(text)
    return {
        "tool": "create_aec_block",
        "args": {"name": "Block_01", "width": width, "depth": depth, "height": height},
    }


def parse_thermalviz_sync_intent(text: str) -> dict | None:
    if not _has_any(text, ("sincroniza", "sincronizar", "sync", "prepara", "preparar", "prepare")):
        return None
    if not _has_any(text, ("thermal", "thermalviz", "viz", "termica", "termico", "bloque", "bloques", "blocks", "modelo")):
        return None
    if _has_any(text, ("todos", "todas", "all", "modelo", "model")):
        return {"tool": "sync_all_blocks_to_thermalviz", "args": {}}
    if _has_any(text, ("seleccionado", "selected", "este", "this", "bloque", "block")):
        return {"tool": "sync_aec_block_to_thermalviz", "args": {}}
    return {"tool": "sync_all_blocks_to_thermalviz", "args": {}}


def parse_modify_selected_sketch_and_rebuild_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "planta", "rectangle", "rectangulo")):
        return None
    if not _has_any(text, ("modifica", "modificar", "cambia", "cambiar", "redimensiona", "resize", "actualiza", "update")):
        return None
    if not _has_any(text, ("seleccionado", "seleccionada", "selected", "este", "esta", "this")):
        return None
    width, depth = parse_plan_dimensions(text)
    return {"tool": "modify_selected_sketch_and_rebuild", "args": {"width": width, "depth": depth}}


def parse_rebuild_selected_block_intent(text: str) -> dict | None:
    if not _has_any(text, ("reconstruye", "reconstruir", "rebuild", "actualiza", "update")):
        return None
    if not _has_any(text, ("bloque", "block")):
        return None
    if not _has_any(text, ("seleccionado", "selected", "este", "this", "sketch", "croquis")):
        return None
    return {"tool": "rebuild_block_from_sketch", "args": {}}


def parse_find_blocks_from_selected_sketch_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "planta")):
        return None
    if not _has_any(text, ("bloques", "blocks", "asociados", "associated", "relacion", "relation", "dependen", "depend")):
        return None
    return {"tool": "find_blocks_from_sketch", "args": {}}


def parse_create_sketch_and_extrude_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "planta", "rectangulo", "rectangle")):
        return None
    if not _has_any(text, ("crea", "crear", "create", "haz", "hacer", "dibuja", "draw", "genera", "generar")):
        return None
    if not _has_any(text, ("extruye", "extruyela", "extruir", "extrude", "convierte", "convert", "bloque", "block")):
        return None
    width, depth, height = parse_dimensions(text)
    return {"tool": "create_sketch_rectangle_and_extrude", "args": {"width": width, "depth": depth, "height": height}}


def parse_create_sketch_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "planta", "rectangulo", "rectangle")):
        return None
    if not _has_any(text, ("crea", "crear", "create", "haz", "hacer", "dibuja", "draw", "genera", "generar")):
        return None
    width, depth = parse_plan_dimensions(text)
    return {"tool": "create_sketch_rectangle", "args": {"width": width, "depth": depth}}


def parse_extrude_sketch_intent(text: str) -> dict | None:
    if not _has_any(text, ("extruye", "extruyela", "extruir", "extrude", "convierte", "convert", "make")):
        return None
    if not _has_any(text, ("sketch", "croquis", "planta", "rectangulo", "rectangle", "este", "this", "seleccionado", "selected")):
        return None
    return {"tool": "extrude_selected_sketch", "args": {"height": parse_height(text)}}


def parse_sketch_footprint_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "planta", "huella", "footprint", "puntos", "points")):
        return None
    if _has_any(text, ("puntos", "points", "huella", "footprint", "geometria", "geometry")):
        return {"tool": "get_sketch_footprint_points", "args": {}}
    return None


def parse_validate_sketch_intent(text: str) -> dict | None:
    if not _has_any(text, ("sketch", "croquis", "rectangulo", "rectangle")):
        return None
    if _has_any(text, ("valida", "validar", "validate", "puede", "extruible", "extruir", "extrude")):
        return {"tool": "validate_sketch", "args": {}}
    return None


def parse_list_sketches_intent(text: str) -> bool:
    if not _has_any(text, ("sketch", "sketches", "croquis", "planta", "plantas", "rectangulo", "rectangulos")):
        return False
    return _has_any(text, ("lista", "listar", "list", "muestra", "show", "hay", "exist", "existing", "que"))


def parse_analyze_scene_intent(text: str) -> bool:
    return _has_any(text, ("analiza", "analizar", "analyze", "inspect", "inspecciona", "escena", "scene"))


def parse_validate_intent(text: str) -> bool:
    return _has_any(text, ("valida", "validar", "validate", "validacion", "validation", "check", "comprueba", "verifica"))


def parse_list_intent(text: str) -> bool:
    return _has_any(text, ("lista", "listar", "list", "muestra", "show")) and _has_any(
        text, ("zona", "zonas", "bloque", "bloques", "block", "blocks", "space", "spaces")
    )


def parse_export_intent(text: str) -> bool:
    return _has_any(text, ("exporta", "exportar", "export", "idf", "energyplus"))


def parse_selected_intent(text: str) -> bool:
    return _has_any(text, ("seleccion", "seleccionado", "selected", "selection"))


def parse_surface_geometry_intent(text: str) -> bool:
    return _has_any(text, ("inspecciona", "inspect", "audita", "debug")) and _has_any(
        text, ("surface", "superficie", "floor", "ceiling", "wall")
    )


def parse_sketch_intent(text: str) -> bool:
    return _has_any(text, ("croquis", "sketch", "dibuja", "draw", "contorno", "curve"))


def parse_dimensions(text: str) -> tuple[float, float, float]:
    compact_match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?!\d)",
        text,
    )
    if compact_match:
        return _positive_triplet(compact_match.groups())
    por_match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:por|by)\s*(\d+(?:[.,]\d+)?)\s*(?:por|by)\s*(\d+(?:[.,]\d+)?)(?!\d)",
        text,
    )
    if por_match:
        return _positive_triplet(por_match.groups())
    comma_match = re.search(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)(?!\d)",
        text,
    )
    if comma_match:
        return _positive_triplet(comma_match.groups())
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(numbers) >= 3:
        return _positive_triplet(numbers[:3])
    return DEFAULT_BLOCK_DIMS


def parse_plan_dimensions(text: str) -> tuple[float, float]:
    compact_match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?!\d)", text)
    if compact_match:
        return _positive_pair(compact_match.groups())
    por_match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:por|by)\s*(\d+(?:[.,]\d+)?)(?!\d)", text)
    if por_match:
        return _positive_pair(por_match.groups())
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(numbers) >= 2:
        return _positive_pair(numbers[:2])
    return DEFAULT_SKETCH_DIMS


def parse_height(text: str) -> float:
    height_match = re.search(r"(?:altura|height|to|a)\s*(\d+(?:[.,]\d+)?)", text)
    if height_match:
        return max(float(height_match.group(1).replace(",", ".")), 0.001)
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if numbers:
        return max(float(numbers[-1].replace(",", ".")), 0.001)
    return DEFAULT_BLOCK_DIMS[2]


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = value.replace("\u00d7", "x")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_dxf_path(text: str) -> str | None:
    match = re.search(r"([a-z]:[\\/][^\"']+?\.dxf)", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"(/[^\s\"']+?\.dxf)", text)
    if match:
        return match.group(1).strip()
    return None


def _positive_triplet(values) -> tuple[float, float, float]:
    numbers = [max(float(str(value).replace(",", ".")), 0.001) for value in values]
    return numbers[0], numbers[1], numbers[2]


def _positive_pair(values) -> tuple[float, float]:
    numbers = [max(float(str(value).replace(",", ".")), 0.001) for value in values]
    return numbers[0], numbers[1]


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)
