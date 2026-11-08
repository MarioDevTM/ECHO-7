"""Validate the JSON fields consumed by the runtime before constructing entities."""
import math
import pygame
from src.core.settings import PLAYER_WIDTH, PLAYER_HEIGHT

FIELDS = {
    "crates": "id x y", "doors": "id x y w h", "moving_platforms": "id x y w h end_x end_y",
    "collapsing_platforms": "id x y w h", "checkpoints": "id x y", "collectibles": "id x y",
    "plates": "link_id x y", "switches": "link_id x y", "generators": "link_id x y",
    "valves": "link_id x y", "mirrors": "id x y", "conveyors": "id x y w h speed",
    "wind_zones": "id x y w h", "water_zones": "id x y w h drained_y",
    "lasers": "x y dir max_length", "optical_beams": "link_id x y dir max_length receiver",
    "sequences": "group_id order", "cables": "link_id points", "steam_vents": "id x y w h",
    "crushers": "id x y w h travel", "acids": "x y w h", "spikes": "x y w h",
    "ladders": "x y h", "decorations": "type x y",
    "latching_relays": "link_id x y", "routing_consoles": "id x y",
    "signal_inverters": "link_id input", "npcs": "id x y",
    "springs": "id x y w", "dash_recharges": "id x y",
    "one_way_platforms": "id x y w", "dash_barriers": "id x y w h",
}


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def vector(value, length):
    return isinstance(value, list) and len(value) == length and all(number(x) for x in value)


def field_valid(key, value):
    if key in ("id", "group_id", "link_id", "type", "input"):
        return isinstance(value, str) and bool(value)
    if key == "dir":
        return value in ([1, 0], [-1, 0], [0, 1], [0, -1])
    if key == "receiver":
        return vector(value, 4) and min(value[2:]) > 0
    if key == "order":
        return isinstance(value, list) and bool(value) and all(isinstance(x, str) for x in value)
    if key == "points":
        return isinstance(value, list) and len(value) >= 2 and all(vector(p, 2) for p in value)
    return number(value) and (key not in ("w", "h", "max_length") or value > 0)


def schema_errors(data):
    errors = []
    tiles = []
    for category in (*FIELDS, "tiles", "hint_route"):
        if category in data and not isinstance(data[category], list):
            errors.append(f"{category} must be a list")
    if errors:
        return errors
    abilities = data.get('abilities', {})
    if not isinstance(abilities, dict) or any(k not in ('wall_jump', 'dash')
            or type(v) is not bool for k, v in abilities.items()):
        errors.append('abilities must map wall_jump/dash to booleans')
    for tile in data.get("tiles", []):
        if not vector(tile, 4) or min(tile[2:]) <= 0:
            errors.append(f"Invalid tile rectangle {tile!r}")
        else:
            tiles.append(pygame.Rect(tile))
    seen = set()
    for category, fields in FIELDS.items():
        for index, item in enumerate(data.get(category, [])):
            label = f"{category}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            for key in fields.split():
                if not field_valid(key, item.get(key)):
                    errors.append(f"{label}.{key} is missing or invalid")
            if category == "doors" and all(number(item.get(k)) for k in ("x", "y", "w", "h")):
                opening = pygame.Rect(*(item[k] for k in ("x", "y", "w", "h")))
                if any(tile.contains(opening) for tile in tiles):
                    errors.append(f"{label}: a solid tile fills the entire doorway")
            identifier = item.get("id") or item.get("group_id") or item.get("link_id")
            if category != "cables" and isinstance(identifier, str):
                if identifier in seen:
                    errors.append(f"{label}: duplicate ID {identifier}")
                seen.add(identifier)
            for key in ("speed", "duration", "mass", "period", "vx", "vy", "delay", "respawn", "impulse"):
                if key in item and not number(item[key]):
                    errors.append(f"{label}.{key} must be a finite number")
            if "logic" in item and item["logic"] not in ("ALL", "ANY", "all", "any"):
                errors.append(f"{label}.logic must be ALL or ANY")
            if category in ('springs', 'one_way_platforms', 'dash_barriers') and number(item.get('w')) and item['w'] <= 0:
                errors.append(f"{label}.w must be positive")
            if category in ('springs', 'one_way_platforms', 'dash_barriers') and number(item.get('h', 1)) and item.get('h', 1) <= 0:
                errors.append(f"{label}.h must be positive")
            if category == "mirrors" and item.get("orientation", 0) not in (0, 1):
                errors.append(f"{label}.orientation must be 0 or 1")
            if category == "water_zones" and all(number(item.get(k)) for k in ("y", "h", "drained_y")):
                if not item["y"] <= item["drained_y"] <= item["y"] + item["h"]:
                    errors.append(f"{label}.drained_y must be inside the basin")
            if category == "latching_relays" and not item.get("required_links"):
                errors.append(f"{label}.required_links must be a non-empty signal list")
            if category == "routing_consoles":
                for k in ("route_id", "a_signal", "b_signal"):
                    if not isinstance(item.get(k), str) or not item[k]:
                        errors.append(f"{label}.{k} is required")
            for key in ("required_links", "disabled_by"):
                if key in item and not (isinstance(item[key], list) and all(isinstance(v, str) for v in item[key])):
                    errors.append(f"{label}.{key} must be a list of signal IDs")
    if not all(isinstance(data.get(k), int) for k in ("width", "height")):
        return errors + ["Missing integer level dimensions"]
    bounds = pygame.Rect(0, 0, data["width"], data["height"])
    probes = [("spawn", data.get("spawn"), PLAYER_WIDTH, PLAYER_HEIGHT), ("exit", data.get("exit"), 48, 80)]
    for cp in data.get("checkpoints", []):
        if isinstance(cp, dict) and number(cp.get("x")) and number(cp.get("y")):
            probes.append((cp.get("id"), [cp["x"], cp["y"] - 48], PLAYER_WIDTH, PLAYER_HEIGHT))
    for name, position, width, height in probes:
        if not vector(position, 2):
            errors.append(f"Invalid {name} position")
        else:
            rect = pygame.Rect(*position, width, height)
            if not bounds.contains(rect) or rect.collidelist(tiles) >= 0:
                errors.append(f"{name} intersects terrain or level bounds")
    return errors
