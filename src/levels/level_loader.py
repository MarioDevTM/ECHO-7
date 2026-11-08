import json
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any
from src.core.settings import AUXILIARY_ROOMS, LEVELS_DIR
from src.levels.level_schema import schema_errors


CHAPTER_METADATA: dict[int, dict[str, Any]] = {
    1: {"chapter_id": 1, "title": "Chapter 1 — Awakening", "theme": "awakening",
        "description": "ECHO-7 research corridor, cryo-wake diagnostics, and primary interlocks.", "levels": list(range(1, 11))},
    2: {"chapter_id": 2, "title": "Chapter 2 — Mechanical Depths", "theme": "mechanical",
        "description": "Interior heavy fabrication halls, counterbalanced hoists, and presses.", "levels": list(range(11, 21))},
    3: {"chapter_id": 3, "title": "Chapter 3 — Power Grid", "theme": "power",
        "description": "High-voltage distribution bays, A/B bus routing, and latching relays.", "levels": list(range(21, 31))},
    4: {"chapter_id": 4, "title": "Chapter 4 — Surveillance Grid", "theme": "optical",
        "description": "Monitored security corridors, optical sightlines, and blind-spot routing.", "levels": list(range(31, 41))},
    5: {"chapter_id": 5, "title": "Chapter 5 — Flood Control", "theme": "environmental",
        "description": "Ruptured facility pipework, drainage basins, steam locks, and updrafts.", "levels": list(range(41, 51))},
    6: {"chapter_id": 6, "title": "Chapter 6 — Core Collapse", "theme": "furnace",
        "description": "Destabilizing central reactor core, thermal conveyors, and emergency locks.", "levels": list(range(51, 61))},
    7: {"chapter_id": 7, "title": "Chapter 7 — Broken Spire", "theme": "spire",
        "description": "Disintegrating upper interior spans, fracture seals, and relay memory.", "levels": list(range(61, 71))},
    8: {"chapter_id": 8, "title": "Chapter 8 — Surface Breach", "theme": "surface",
        "description": "Nocturnal moonlit escape across the exterior ruins beyond ECHO-7.", "levels": list(range(71, 81))},
}


def _base_room(width: int, height: int, floor_segments: list[list[int]]) -> list[list[int]]:
    """Builds outer facility walls, ceiling, and custom floor/platform segments."""
    tiles = [
        [0, 0, 40, height],
        [0, 0, width, 40],
        [width - 40, 0, 40, height],
    ]
    tiles.extend(floor_segments)
    return tiles


DEFAULT_LEVELS: dict[int, dict[str, Any]] = {
    # =========================================================================
    # CHAPTER 1 — THE AWAKENING (Levels 1 - 4)
    # =========================================================================
    1: {
        "level_id": 1,
        "hint_route": ["sw_intro", "plate_1"],
        "chapter": 1,
        "theme": "awakening",
        "name": "Chamber 01 // Awakening",
        "subtitle": "[A/D] Move, [Space] Jump, [S] Crouch, [W/S] Climb Ladders, [E] Interact, Push crates onto plates.",
        "width": 2600,
        "height": 760,
        "spawn": [100, 560],
        "exit": [2420, 540],
        "tiles": _base_room(
            2600,
            760,
            [
                [0, 620, 820, 140],
                [420, 540, 140, 80],
                [920, 620, 760, 140],
                [1160, 460, 260, 30],
                [1780, 620, 820, 140],
                [2080, 380, 40, 140],
                [1480, 320, 220, 30],
            ],
        ),
        "ladders": [
            {"x": 1130, "y": 460, "h": 160},
            {"x": 1450, "y": 320, "h": 140},
        ],
        "crates": [{"id": "c1_1", "x": 1020, "y": 560}],
        "plates": [{"link_id": "plate_1", "x": 1560, "y": 620}],
        "switches": [{"link_id": "sw_intro", "x": 1280, "y": 460, "mode": "permanent"}],
        "doors": [
            {
                "id": "d1_exit",
                "x": 2080,
                "y": 520,
                "w": 40,
                "h": 100,
                "required_links": ["plate_1", "sw_intro"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[1294, 460], [1294, 520], [2100, 520]], "link_id": "sw_intro"},
            {"points": [[1582, 620], [2100, 620], [2100, 580]], "link_id": "plate_1"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp1_1", "x": 960, "y": 620}],
        "spikes": [],
        "acids": [{"x": 820, "y": 650, "w": 100, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_01",
                "x": 1580,
                "y": 270,
                "title": "Cryo-Bay Log #01",
                "text": "Automated wake-up triggered. All surface comms offline for 1,400 days.",
            }
        ],
        "decorations": [
            {"type": "sign_arrow", "x": 220, "y": 570, "text": "SECTOR A ->"},
            {"type": "monitor", "x": 1210, "y": 410, "text": "AUX LOCK"},
            {"type": "pipe_h", "x": 100, "y": 80, "w": 2200},
        ],
        "solution_steps": [
            "Jump over the initial step and gap over the coolant pool to Checkpoint 1.",
            "Climb the ladder at x=1130 to activate switch 'sw_intro' (or climb higher to x=1450 for Log #01).",
            "Push crate 'c1_1' onto pressure plate 'plate_1' at x=1560 to open bulkhead 'd1_exit'.",
        ],
    },
    2: {
        "level_id": 2,
        "hint_route": ["sw_upper_gate", "plate_2a", "plate_2b"],
        "chapter": 1,
        "theme": "awakening",
        "name": "Chamber 02 // Locked Passage",
        "subtitle": "Coordinate dual weight plates and upper maintenance locks to clear the security corridor.",
        "width": 2700,
        "height": 800,
        "spawn": [100, 600],
        "exit": [2520, 580],
        "tiles": _base_room(
            2700,
            800,
            [
                [0, 660, 1100, 140],
                [520, 480, 420, 30],
                [1240, 660, 1460, 140],
                [1120, 420, 40, 140],
                [1500, 500, 360, 30],
                [2180, 420, 40, 140],
            ],
        ),
        "ladders": [
            {"x": 490, "y": 480, "h": 180},
            {"x": 1470, "y": 500, "h": 160},
        ],
        "crates": [
            {"id": "c2_upper", "x": 640, "y": 420},
            {"id": "c2_lower", "x": 1620, "y": 440},
        ],
        "plates": [
            {"link_id": "plate_2a", "x": 960, "y": 660},
            {"link_id": "plate_2b", "x": 1960, "y": 660},
        ],
        "switches": [
            {"link_id": "sw_upper_gate", "x": 860, "y": 480, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d2_mid",
                "x": 1120,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": ["sw_upper_gate"],
                "logic": "ALL",
            },
            {
                "id": "d2_exit",
                "x": 2180,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": ["plate_2a", "plate_2b"],
                "logic": "ALL",
            },
        ],
        "moving_platforms": [
            {
                "id": "mp2_bridge",
                "x": 1110,
                "y": 650,
                "w": 110,
                "h": 20,
                "end_x": 1110,
                "end_y": 650,
                "speed": 0,
                "required_links": [],
                "active_by_default": True,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[874, 480], [1140, 480], [1140, 560]], "link_id": "sw_upper_gate"},
            {"points": [[982, 660], [2200, 660]], "link_id": "plate_2a"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp2_1", "x": 1300, "y": 660}],
        "spikes": [{"x": 1720, "y": 642, "w": 96, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1100, "y": 690, "w": 140, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_02",
                "x": 560,
                "y": 430,
                "title": "Security Notice #04",
                "text": "Dual-weight interlocks prevent unmanned drones from breaching Sector B.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 780, "y": 430, "text": "GATE CTRL"},
            {"type": "warning_stripe", "x": 1100, "y": 640, "w": 140},
        ],
        "solution_steps": [
            "Climb the ladder at x=490, collect Log #02, activate 'sw_upper_gate', and push 'c2_upper' off the right ledge onto 'plate_2a'.",
            "Cross the bridge past 'd2_mid' to Checkpoint 'cp2_1'.",
            "Climb the ladder at x=1470, push 'c2_lower' off the right edge, and push it onto 'plate_2b' to open 'd2_exit'.",
        ],
    },
    3: {
        "level_id": 3,
        "hint_route": ["sw_conv_rev", "plate_assembly", "sw_bridge_3"],
        "chapter": 1,
        "theme": "awakening",
        "name": "Chamber 03 // The Assembly Line",
        "subtitle": "Reverse industrial conveyor belts to transport cargo crates and power the transfer bridge.",
        "width": 2800,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2620, 560],
        "tiles": _base_room(
            2800,
            780,
            [
                [0, 640, 1220, 140],
                [380, 470, 260, 30],
                [1620, 640, 1180, 140],
                [1880, 480, 280, 30],
                [2320, 400, 40, 140],
            ],
        ),
        "ladders": [
            {"x": 350, "y": 470, "h": 170},
            {"x": 1850, "y": 480, "h": 160},
        ],
        "crates": [{"id": "c3_cargo", "x": 760, "y": 560}],
        "plates": [{"link_id": "plate_assembly", "x": 1080, "y": 640}],
        "switches": [
            {"link_id": "sw_conv_rev", "x": 480, "y": 470, "mode": "toggle"},
            {"link_id": "sw_bridge_3", "x": 2020, "y": 480, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d3_exit",
                "x": 2320,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["plate_assembly", "sw_bridge_3"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp3_ferry",
                "x": 1240,
                "y": 620,
                "w": 130,
                "h": 22,
                "end_x": 1470,
                "end_y": 620,
                "speed": 130,
                "required_links": ["plate_assembly"],
                "active_by_default": False,
            }
        ],
        "conveyors": [
            {
                "id": "conv_3_1",
                "x": 620,
                "y": 640,
                "w": 380,
                "h": 16,
                "speed": -115.0,
                "reversed_by": "sw_conv_rev",
            }
        ],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[494, 470], [494, 640], [620, 640]], "link_id": "sw_conv_rev"},
            {"points": [[1102, 640], [1240, 640]], "link_id": "plate_assembly"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp3_1", "x": 1680, "y": 640}],
        "spikes": [],
        "acids": [{"x": 1220, "y": 670, "w": 400, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_03",
                "x": 1950,
                "y": 430,
                "title": "Logistics Memo #12",
                "text": "Conveyor drive polarity reversed during the evacuation rush.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 420, "y": 420, "text": "BELT DIR"},
            {"type": "sign_arrow", "x": 960, "y": 590, "text": "CARGO PAD"},
        ],
        "solution_steps": [
            "Climb the ladder at x=350 and toggle 'sw_conv_rev' so conveyor 'conv_3_1' pushes right instead of left.",
            "Guide crate 'c3_cargo' off the conveyor onto 'plate_assembly' to start platform 'mp3_ferry'.",
            "Ride 'mp3_ferry' across the acid vat, climb to 'sw_bridge_3', and exit through 'd3_exit'.",
        ],
    },
    4: {
        "level_id": 4,
        "hint_route": ["sw_laser_4", "plate_4", "sw_timed_4"],
        "chapter": 1,
        "theme": "awakening",
        "name": "Chamber 04 // Emergency Exit",
        "subtitle": "Park the shield crate on the laser safety pad, engage the override, then reach the timed lock.",
        "width": 2800,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2620, 560],
        "tiles": _base_room(
            2800,
            780,
            [
                [0, 640, 1340, 140],
                [1580, 640, 1220, 140],
                [1720, 470, 240, 30],
                [2340, 400, 40, 140],
            ],
        ),
        "ladders": [{"x": 1690, "y": 470, "h": 170}],
        "crates": [{"id": "c4_shield", "x": 380, "y": 580}],
        "plates": [{"link_id": "shield_4", "x": 620, "y": 640}, {"link_id": "plate_4", "x": 1180, "y": 640}],
        "switches": [
            {"link_id": "sw_laser_4", "x": 860, "y": 640, "mode": "permanent"},
            {
                "link_id": "sw_timed_4",
                "x": 1820,
                "y": 470,
                "mode": "timed",
                "duration": 6.0,
            },
        ],
        "doors": [
            {
                "id": "d4_exit",
                "x": 2340,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["plate_4", "sw_timed_4"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp4_cross",
                "x": 1350,
                "y": 620,
                "w": 110,
                "h": 22,
                "end_x": 1460,
                "end_y": 620,
                "speed": 120,
                "required_links": [],
                "active_by_default": True,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[874, 640], [640, 640], [640, 420]], "link_id": "sw_laser_4"},
            {"points": [[1834, 470], [2360, 470], [2360, 540]], "link_id": "sw_timed_4"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp4_1", "x": 1620, "y": 640}],
        "spikes": [{"x": 2040, "y": 622, "w": 80, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1340, "y": 670, "w": 240, "h": 110}],
        "lasers": [
            {
                "x": 640,
                "y": 420,
                "dir": [0, 1],
                "max_length": 220,
                "disabled_by": ["sw_laser_4", "shield_4"],
            }
        ],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_04",
                "x": 1760,
                "y": 420,
                "title": "Evacuation Directive",
                "text": "Personnel proceeding to Mechanical Depths must wear rated hazard suits.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 820, "y": 590, "text": "LASER OFF"},
            {"type": "sign_arrow", "x": 2200, "y": 590, "text": "ELEVATOR ->"},
        ],
        "solution_steps": [
            "Push 'c4_shield' onto the safety pad beneath the laser, jump over the parked crate, and hit 'sw_laser_4'.",
            "Push 'c4_shield' further right onto 'plate_4', then cross the moving platform to Checkpoint 'cp4_1'.",
            "Climb the ladder, trigger timed switch 'sw_timed_4', and sprint ([Shift]) over the spikes through 'd4_exit'.",
        ],
    },

    # =========================================================================
    # CHAPTER 2 — MECHANICAL DEPTHS (Levels 5 - 8)
    # =========================================================================
    5: {
        "level_id": 5,
        "hint_route": ["sw_elev_1", "plate_elev_2", "sw_top_lock"],
        "chapter": 2,
        "theme": "mechanical",
        "name": "Chamber 05 // The Elevator Shaft",
        "subtitle": "Ascend the multi-tier vertical foundry shaft by powering sequential cargo lifts.",
        "width": 2400,
        "height": 1080,
        "spawn": [120, 900],
        "exit": [2180, 240],
        "tiles": _base_room(
            2400,
            1080,
            [
                [0, 960, 1100, 120],
                [900, 700, 780, 40],
                [260, 460, 760, 40],
                [1140, 320, 1260, 40],
                [1960, 80, 40, 140],
            ],
        ),
        "ladders": [{"x": 1580, "y": 700, "h": 260}],
        "crates": [{"id": "c5_weight", "x": 1160, "y": 640}],
        "plates": [{"link_id": "plate_elev_2", "x": 1420, "y": 700}],
        "switches": [
            {"link_id": "sw_elev_1", "x": 620, "y": 960, "mode": "permanent"},
            {"link_id": "sw_top_lock", "x": 420, "y": 460, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d5_exit",
                "x": 1960,
                "y": 220,
                "w": 40,
                "h": 100,
                "required_links": ["sw_top_lock", "plate_elev_2"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp5_1",
                "x": 740,
                "y": 940,
                "w": 130,
                "h": 22,
                "end_x": 740,
                "end_y": 700,
                "speed": 115,
                "required_links": ["sw_elev_1"],
                "active_by_default": False,
            },
            {
                "id": "mp5_2",
                "x": 1000,
                "y": 680,
                "w": 130,
                "h": 22,
                "end_x": 1000,
                "end_y": 320,
                "speed": 120,
                "required_links": ["plate_elev_2"],
                "active_by_default": False,
            },
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[634, 960], [740, 960]], "link_id": "sw_elev_1"},
            {"points": [[1442, 700], [1060, 700]], "link_id": "plate_elev_2"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [
            {"id": "cp5_mid", "x": 960, "y": 700},
            {"id": "cp5_high", "x": 1220, "y": 320},
        ],
        "spikes": [{"x": 1520, "y": 302, "w": 96, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1100, "y": 990, "w": 1260, "h": 90}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_05",
                "x": 320,
                "y": 410,
                "title": "Shaft Inspection Report",
                "text": "Hoist motors recalibrated. Secondary lift requires 50kg counter-load.",
            }
        ],
        "decorations": [
            {"type": "sign_arrow", "x": 540, "y": 910, "text": "HOIST #1"},
            {"type": "monitor", "x": 370, "y": 410, "text": "UPPER BAY"},
        ],
        "solution_steps": [
            "Activate 'sw_elev_1' at the bottom floor and ride lift 'mp5_1' up to the middle tier (y=700).",
            "Push crate 'c5_weight' onto 'plate_elev_2' to activate the upper lift 'mp5_2'.",
            "Ride 'mp5_2' halfway, jump left onto the y=460 ledge to hit 'sw_top_lock' and grab Log #05, then ride 'mp5_2' to the top tier (y=320) and exit.",
        ],
    },
    6: {
        "level_id": 6,
        "hint_route": ["plate_6", "sw_crusher_halt", "sw_door_6"],
        "chapter": 2,
        "theme": "mechanical",
        "name": "Chamber 06 // Heavy Machinery",
        "subtitle": "Time your passage beneath hydraulic crushers and disable the stamping press to advance.",
        "width": 2800,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2620, 560],
        "tiles": _base_room(
            2800,
            780,
            [
                [0, 640, 2800, 140],
                [560, 380, 740, 40],
                [1480, 460, 280, 30],
                [2340, 400, 40, 140],
            ],
        ),
        "ladders": [{"x": 1450, "y": 460, "h": 180}],
        "crates": [{"id": "c6_press", "x": 420, "y": 580}],
        "plates": [{"link_id": "plate_6", "x": 1340, "y": 640}],
        "switches": [
            {"link_id": "sw_crusher_halt", "x": 1620, "y": 460, "mode": "permanent"},
            {"link_id": "sw_door_6", "x": 2120, "y": 640, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d6_exit",
                "x": 2340,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["plate_6", "sw_door_6"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [
            {
                "id": "conv_6_1",
                "x": 620,
                "y": 640,
                "w": 560,
                "h": 16,
                "speed": 95.0,
                "reversed_by": None,
            }
        ],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[1634, 460], [1900, 460], [1900, 420]], "link_id": "sw_crusher_halt"}
        ],
        "mirrors": [],
        "crushers": [
            {
                "id": "cr6_1",
                "x": 760,
                "y": 420,
                "w": 72,
                "h": 40,
                "travel": 220,
                "period": 2.6,
                "disabled_by": [],
            },
            {
                "id": "cr6_2",
                "x": 1880,
                "y": 420,
                "w": 84,
                "h": 40,
                "travel": 220,
                "period": 1.6,
                "disabled_by": ["sw_crusher_halt"],
            },
        ],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp6_1", "x": 1400, "y": 640}],
        "spikes": [],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_06",
                "x": 1540,
                "y": 410,
                "title": "Foundry Safety Bulletin",
                "text": "Hydraulic press #2 governors failed. Engage manual override on catwalk before passing.",
            }
        ],
        "decorations": [
            {"type": "warning_stripe", "x": 620, "y": 620, "w": 560},
            {"type": "monitor", "x": 1580, "y": 410, "text": "PRESS HALT"},
        ],
        "solution_steps": [
            "Push crate 'c6_press' onto conveyor 'conv_6_1' and time your run past oscillating crusher 'cr6_1'.",
            "Push 'c6_press' onto 'plate_6' at x=1340 and touch Checkpoint 'cp6_1'.",
            "Climb the catwalk at x=1450 to hit 'sw_crusher_halt' (stopping fast crusher 'cr6_2'), then hit 'sw_door_6' and exit.",
        ],
    },
    7: {
        "level_id": 7,
        "hint_route": ["plate_counter_1", "sw_lift_7", "plate_counter_2"],
        "chapter": 2,
        "theme": "mechanical",
        "name": "Chamber 07 // Counterbalance",
        "subtitle": "Balance two suspended cargo lifts with crates to unlock the upper foundry lock.",
        "width": 2800,
        "height": 840,
        "spawn": [100, 640],
        "exit": [2600, 420],
        "tiles": _base_room(
            2800,
            840,
            [
                [0, 700, 960, 140],
                [1220, 560, 640, 280],
                [2100, 500, 700, 340],
                [2380, 260, 40, 140],
            ],
        ),
        "ladders": [],
        "crates": [
            {"id": "c7_a", "x": 380, "y": 640},
            {"id": "c7_b", "x": 1380, "y": 500},
        ],
        "plates": [
            {"link_id": "plate_counter_1", "x": 760, "y": 700},
            {"link_id": "plate_counter_2", "x": 1720, "y": 560},
        ],
        "switches": [
            {"link_id": "sw_lift_7", "x": 1520, "y": 560, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d7_exit",
                "x": 2380,
                "y": 400,
                "w": 40,
                "h": 100,
                "required_links": ["plate_counter_1", "plate_counter_2"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp7_counter",
                "x": 980,
                "y": 680,
                "w": 130,
                "h": 22,
                "end_x": 1080,
                "end_y": 560,
                "speed": 105,
                "required_links": ["plate_counter_1"],
                "active_by_default": False,
            },
            {
                "id": "mp7_high",
                "x": 1880,
                "y": 540,
                "w": 130,
                "h": 22,
                "end_x": 1960,
                "end_y": 500,
                "speed": 110,
                "required_links": ["sw_lift_7"],
                "active_by_default": False,
            },
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[782, 700], [980, 700]], "link_id": "plate_counter_1"},
            {"points": [[1742, 560], [2400, 560], [2400, 500]], "link_id": "plate_counter_2"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp7_1", "x": 1280, "y": 560}],
        "spikes": [],
        "acids": [
            {"x": 960, "y": 730, "w": 260, "h": 110},
            {"x": 1860, "y": 730, "w": 240, "h": 110},
        ],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_07",
                "x": 2200,
                "y": 440,
                "title": "Chief Engineer's Note",
                "text": "The counterweight bridges hold steady even when primary power fluctuates.",
            }
        ],
        "decorations": [
            {"type": "sign_arrow", "x": 660, "y": 650, "text": "COUNTERWEIGHT 1"},
        ],
        "solution_steps": [
            "Push crate 'c7_a' onto 'plate_counter_1' to activate diagonal lift 'mp7_counter'.",
            "Ride 'mp7_counter' to the middle platform (Checkpoint 'cp7_1'), activate 'sw_lift_7', and push 'c7_b' onto 'plate_counter_2'.",
            "Cross 'mp7_high' to the upper deck and exit through 'd7_exit'.",
        ],
    },
    8: {
        "level_id": 8,
        "hint_route": ["seq_8_1", "seq_8_2", "seq_8_3", "plate_8_core"],
        "chapter": 2,
        "theme": "mechanical",
        "name": "Chamber 08 // Factory Shutdown",
        "subtitle": "Execute the 3-step shutdown sequence (Left -> Upper -> Right) to halt the foundry crushers.",
        "width": 2900,
        "height": 800,
        "spawn": [100, 600],
        "exit": [2720, 580],
        "tiles": _base_room(
            2900,
            800,
            [
                [0, 660, 1140, 140],
                [420, 490, 260, 30],
                [1420, 660, 1480, 140],
                [1020, 420, 40, 140],
                [2460, 420, 40, 140],
            ],
        ),
        "ladders": [{"x": 390, "y": 490, "h": 170}],
        "crates": [{"id": "c8_core", "x": 1600, "y": 600}],
        "plates": [{"link_id": "plate_8_core", "x": 2240, "y": 660}],
        "switches": [
            {"link_id": "seq_8_1", "x": 260, "y": 660, "mode": "sequence"},
            {"link_id": "seq_8_2", "x": 540, "y": 490, "mode": "sequence"},
            {"link_id": "seq_8_3", "x": 840, "y": 660, "mode": "sequence"},
        ],
        "doors": [
            {
                "id": "d8_mid",
                "x": 1020,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": ["seq_factory_8"],
                "logic": "ALL",
            },
            {
                "id": "d8_exit",
                "x": 2460,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": ["seq_factory_8", "plate_8_core"],
                "logic": "ALL",
            },
        ],
        "moving_platforms": [
            {
                "id": "mp8_ferry",
                "x": 1150,
                "y": 640,
                "w": 130,
                "h": 22,
                "end_x": 1280,
                "end_y": 640,
                "speed": 125,
                "required_links": [],
                "active_by_default": True,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [],
        "mirrors": [],
        "crushers": [
            {
                "id": "cr8_1",
                "x": 1920,
                "y": 420,
                "w": 90,
                "h": 40,
                "travel": 240,
                "period": 1.8,
                "disabled_by": ["seq_factory_8"],
            }
        ],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp8_1", "x": 1480, "y": 660}],
        "spikes": [],
        "acids": [{"x": 1140, "y": 690, "w": 280, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [
            {"group_id": "seq_factory_8", "order": ["seq_8_1", "seq_8_2", "seq_8_3"]}
        ],
        "collectibles": [
            {
                "id": "log_08",
                "x": 460,
                "y": 440,
                "title": "Foundry Shutdown Protocol",
                "text": "Sequence order: Floor Intake (1) -> Catwalk Bus (2) -> Bulkhead Relay (3).",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 220, "y": 610, "text": "SEQ [1]"},
            {"type": "monitor", "x": 500, "y": 440, "text": "SEQ [2]"},
            {"type": "monitor", "x": 800, "y": 610, "text": "SEQ [3]"},
        ],
        "solution_steps": [
            "Activate switches 'seq_8_1' (left floor), 'seq_8_2' (catwalk), and 'seq_8_3' (right floor) in order to unlock 'd8_mid' and disable crusher 'cr8_1'.",
            "Cross 'mp8_ferry' to Checkpoint 'cp8_1', push crate 'c8_core' past the halted crusher onto 'plate_8_core', and exit.",
        ],
    },

    # =========================================================================
    # CHAPTER 3 — POWER AND ENERGY (Levels 9 - 12)
    # =========================================================================
    9: {
        "level_id": 9,
        "hint_route": ["gen_9_1", "gen_9_2", "plate_9"],
        "chapter": 3,
        "theme": "power",
        "name": "Chamber 09 // Power Failure",
        "subtitle": "Interact with backup generators [E] to energize power cables, lifts, and substation gates.",
        "width": 2800,
        "height": 800,
        "spawn": [100, 600],
        "exit": [2620, 580],
        "tiles": _base_room(
            2800,
            800,
            [
                [0, 660, 1080, 140],
                [1360, 660, 1440, 140],
                [1620, 480, 320, 30],
                [2360, 420, 40, 140],
            ],
        ),
        "ladders": [{"x": 1590, "y": 480, "h": 180}],
        "crates": [{"id": "c9_cell", "x": 1480, "y": 600}],
        "plates": [{"link_id": "plate_9", "x": 2120, "y": 660}],
        "switches": [],
        "doors": [
            {
                "id": "d9_exit",
                "x": 2360,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": ["gen_9_1", "gen_9_2", "plate_9"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp9_lift",
                "x": 1100,
                "y": 640,
                "w": 130,
                "h": 22,
                "end_x": 1220,
                "end_y": 640,
                "speed": 125,
                "required_links": ["gen_9_1"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [
            {"link_id": "gen_9_1", "x": 560, "y": 660, "duration": 0.0},
            {"link_id": "gen_9_2", "x": 1780, "y": 480, "duration": 0.0},
        ],
        "cables": [
            {"points": [[584, 660], [1100, 660]], "link_id": "gen_9_1"},
            {"points": [[1804, 480], [2380, 480], [2380, 560]], "link_id": "gen_9_2"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp9_1", "x": 1420, "y": 660}],
        "spikes": [{"x": 2490, "y": 642, "w": 80, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1080, "y": 690, "w": 280, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_09",
                "x": 1680,
                "y": 430,
                "title": "Grid Collapse Log",
                "text": "Main reactor scrammed. Auxiliary diesel-electric turbines remain operational.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 500, "y": 610, "text": "GEN-A"},
            {"type": "monitor", "x": 1720, "y": 430, "text": "GEN-B"},
        ],
        "solution_steps": [
            "Start generator 'gen_9_1' at x=560 to power bridge 'mp9_lift' across the acid gap.",
            "Climb the ladder at x=1590 to start 'gen_9_2' and collect Log #09.",
            "Jump or push crate 'c9_cell' onto 'plate_9' at x=2120 to open 'd9_exit'.",
        ],
    },
    10: {
        "level_id": 10,
        "hint_route": ["seq_10_1", "seq_10_2", "seq_10_3", "sw_cond_10a", "sw_cond_10b"],
        "chapter": 3,
        "theme": "power",
        "name": "Chamber 10 // Circuit Breaker",
        "subtitle": "Close the 3-breaker relay sequence, then synchronize the dual timed high-voltage conduits.",
        "width": 2800,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2620, 560],
        "tiles": _base_room(
            2800,
            780,
            [
                [0, 640, 1180, 140],
                [1400, 640, 1400, 140],
                [1620, 480, 280, 30],
                [1040, 400, 40, 140],
                [2340, 400, 40, 140],
            ],
        ),
        "ladders": [{"x": 1590, "y": 480, "h": 160}],
        "crates": [],
        "plates": [],
        "switches": [
            {"link_id": "seq_10_1", "x": 300, "y": 640, "mode": "sequence"},
            {"link_id": "seq_10_2", "x": 580, "y": 640, "mode": "sequence"},
            {"link_id": "seq_10_3", "x": 860, "y": 640, "mode": "sequence"},
            {
                "link_id": "sw_cond_10a",
                "x": 1740,
                "y": 480,
                "mode": "timed",
                "duration": 6.5,
            },
            {
                "link_id": "sw_cond_10b",
                "x": 2080,
                "y": 640,
                "mode": "timed",
                "duration": 6.5,
            },
        ],
        "doors": [
            {
                "id": "d10_mid",
                "x": 1040,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["seq_circuit_10"],
                "logic": "ALL",
            },
            {
                "id": "d10_exit",
                "x": 2340,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["sw_cond_10a", "sw_cond_10b"],
                "logic": "ALL",
            },
        ],
        "moving_platforms": [
            {
                "id": "mp10_bridge",
                "x": 1190,
                "y": 620,
                "w": 110,
                "h": 22,
                "end_x": 1280,
                "end_y": 620,
                "speed": 120,
                "required_links": [],
                "active_by_default": True,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[1754, 480], [2360, 480], [2360, 540]], "link_id": "sw_cond_10a"},
            {"points": [[2094, 640], [2360, 640]], "link_id": "sw_cond_10b"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp10_1", "x": 1460, "y": 640}],
        "spikes": [],
        "acids": [{"x": 1180, "y": 670, "w": 220, "h": 110}],
        "lasers": [],
        "optical_beams": [],
        "sequences": [
            {"group_id": "seq_circuit_10", "order": ["seq_10_1", "seq_10_2", "seq_10_3"]}
        ],
        "collectibles": [
            {
                "id": "log_10",
                "x": 1660,
                "y": 430,
                "title": "Substation Schematic",
                "text": "Dual timed breakers prevent arc-flash. Trigger upper bus before floor bus.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 260, "y": 590, "text": "RELAY 1"},
            {"type": "monitor", "x": 540, "y": 590, "text": "RELAY 2"},
            {"type": "monitor", "x": 820, "y": 590, "text": "RELAY 3"},
        ],
        "solution_steps": [
            "Flip 'seq_10_1', 'seq_10_2', and 'seq_10_3' from left to right to open 'd10_mid'.",
            "Cross 'mp10_bridge' to Checkpoint 'cp10_1', climb the ladder, trigger 'sw_cond_10a', drop down to trigger 'sw_cond_10b', and sprint through 'd10_exit'.",
        ],
    },
    11: {
        "level_id": 11,
        "hint_route": ["sw_beam_11", "opt_11_main", "plate_11_lens"],
        "chapter": 3,
        "theme": "power",
        "name": "Chamber 11 // Laser Laboratory",
        "subtitle": "Unblock and align the optical calibration beam using rotatable mirrors [E] to unlock the chamber.",
        "width": 2700,
        "height": 760,
        "spawn": [100, 560],
        "exit": [2520, 540],
        "tiles": _base_room(
            2700,
            760,
            [
                [220, 450, 352, 16],
                [380, 366, 192, 14],
                [558, 380, 14, 70],
                [0, 620, 1240, 140],
                [1460, 620, 1240, 140],
                [2260, 380, 40, 140],
            ],
        ),
        "ladders": [
            {'x': 190, 'y': 450, 'h': 170},
        ],
        "crates": [{"id": "c11_lens_crate", "x": 520, "y": 560}],
        "plates": [{"link_id": "plate_11_lens", "x": 920, "y": 620}],
        "switches": [
            {'link_id': 'archive_11_a', 'x': 244, 'y': 450, 'mode': 'sequence'},
            {'link_id': 'archive_11_b', 'x': 318, 'y': 450, 'mode': 'sequence'},
            {"link_id": "sw_beam_11", "x": 260, "y": 620, "mode": "permanent"},
        ],
        "doors": [
            {'id': 'archive_11_gate', 'x': 380, 'y': 380, 'w': 18, 'h': 70, 'required_links': ['archive_11']},
            {
                "id": "d11_exit",
                "x": 2260,
                "y": 520,
                "w": 40,
                "h": 100,
                "required_links": ["opt_11_main", "plate_11_lens"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp11_bridge",
                "x": 1250,
                "y": 600,
                "w": 110,
                "h": 22,
                "end_x": 1340,
                "end_y": 600,
                "speed": 115,
                "required_links": ["opt_11_main"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[654, 488], [654, 450], [1250, 450], [1250, 598]], "link_id": "opt_11_main"},
        ],
        "mirrors": [
            {"id": "m11_1", "x": 640, "y": 580, "orientation": 1},
        ],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp11_1", "x": 1520, "y": 620}],
        "spikes": [{"x": 1840, "y": 602, "w": 96, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1240, "y": 650, "w": 220, "h": 110}],
        "lasers": [],
        "optical_beams": [
            {
                "link_id": "opt_11_main",
                "x": 360,
                "y": 598,
                "dir": [1, 0],
                "max_length": 440,
                "receiver": [645, 478, 18, 20],
                "enabled_by": "sw_beam_11",
            }
        ],
        "sequences": [
            {'group_id': 'archive_11', 'order': ['archive_11_a', 'archive_11_b']},
        ],
        "collectibles": [
            {'id': 'archive_log_11', 'x': 489, 'y': 416, 'title': 'Shift handover', 'text': 'Both inspectors signed off. The last shift never clocked out.'},
            {
                "id": "log_11",
                "x": 1680,
                "y": 560,
                "title": "Photonics Lab Note",
                "text": "Calibration note: tilt the silver face toward the ceiling pickup.",
            }
        ],
        "decorations": [
            {'type': 'monitor', 'x': 242, 'y': 370, 'text': 'ARCHIVE  1 > 2'},
            {"type": "monitor", "x": 220, "y": 570, "text": "EMITTER"},
        ],
        "solution_steps": [
            "Activate 'sw_beam_11' to fire the optical beam, then push crate 'c11_lens_crate' out of the beam path onto 'plate_11_lens' at x=920.",
            "Rotate the mirror to aim upward. With 'opt_11_main' hitting its receiver, cross 'mp11_bridge' to Checkpoint 'cp11_1', jump the spikes, and exit.",
        ],
    },
    12: {
        "level_id": 12,
        "hint_route": ["gen_12_main", "opt_12_cal", "plate_12_hold", "sw_overload_12"],
        "chapter": 3,
        "theme": "power",
        "name": "Chamber 12 // Overload",
        "subtitle": "Power the emitter generator, clear the optical path to disable the security laser, and sprint out.",
        "width": 2900,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2720, 560],
        "tiles": _base_room(
            2900,
            780,
            [
                [0, 640, 1300, 140],
                [1540, 640, 1360, 140],
                [2440, 400, 40, 140],
            ],
        ),
        "ladders": [],
        "crates": [{"id": "c12_block", "x": 540, "y": 580}],
        "plates": [{"link_id": "plate_12_hold", "x": 980, "y": 640}],
        "switches": [
            {
                "link_id": "sw_overload_12",
                "x": 2120,
                "y": 640,
                "mode": "timed",
                "duration": 5.5,
            }
        ],
        "doors": [
            {
                "id": "d12_exit",
                "x": 2440,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["gen_12_main", "opt_12_cal", "plate_12_hold", "sw_overload_12"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp12_bridge",
                "x": 1310,
                "y": 620,
                "w": 110,
                "h": 22,
                "end_x": 1420,
                "end_y": 620,
                "speed": 130,
                "required_links": ["opt_12_cal"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [{"link_id": "gen_12_main", "x": 240, "y": 640, "duration": 0.0}],
        "cables": [
            {"points": [[264, 640], [360, 640], [360, 618]], "link_id": "gen_12_main"},
            {"points": [[760, 618], [1820, 618], [1820, 420]], "link_id": "opt_12_cal"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp12_1", "x": 1600, "y": 640}],
        "spikes": [],
        "acids": [{"x": 1300, "y": 670, "w": 240, "h": 110}],
        "lasers": [
            {
                "x": 1820,
                "y": 420,
                "dir": [0, 1],
                "max_length": 220,
                "disabled_by": ["opt_12_cal"],
                "period": 2.0,
                "duty_cycle": 0.6,
            }
        ],
        "optical_beams": [
            {
                "link_id": "opt_12_cal",
                "x": 360,
                "y": 618,
                "dir": [1, 0],
                "max_length": 440,
                "receiver": [760, 604, 18, 28],
                "enabled_by": "gen_12_main",
            }
        ],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_12",
                "x": 1960,
                "y": 580,
                "title": "Chief Physicist's Log",
                "text": "Optical interlock tied directly to laser grid. Keep the beam clear at all costs.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 200, "y": 590, "text": "MAIN GEN"},
        ],
        "solution_steps": [
            "Start 'gen_12_main', push 'c12_block' out of the optical beam onto 'plate_12_hold' at x=980.",
            "The optical beam 'opt_12_cal' activates 'mp12_bridge' and disables the laser at x=1820.",
            "Cross to Checkpoint 'cp12_1', hit timed switch 'sw_overload_12', and sprint through 'd12_exit'.",
        ],
    },

    # =========================================================================
    # CHAPTER 4 — ENVIRONMENTAL CONTROL (Levels 13 - 16)
    # =========================================================================
    13: {
        "level_id": 13,
        "hint_route": ["valve_13_drain", "plate_13_dry", "sw_13_lock"],
        "chapter": 4,
        "theme": "environmental",
        "name": "Chamber 13 // Flooded Corridor",
        "subtitle": "Turn the drainage valve [E] to lower the flooded basin and access the submerged pressure plate.",
        "width": 2800,
        "height": 820,
        "spawn": [100, 520],
        "exit": [2620, 500],
        "tiles": _base_room(
            2800,
            820,
            [
                [0, 580, 760, 240],
                [760, 720, 840, 100],
                [1600, 580, 1200, 240],
                [980, 440, 380, 30],
                [2340, 340, 40, 140],
            ],
        ),
        "ladders": [
            {"x": 730, "y": 580, "h": 140},
            {"x": 1570, "y": 580, "h": 140},
        ],
        "crates": [{"id": "c13_basin", "x": 920, "y": 660}],
        "plates": [{"link_id": "plate_13_dry", "x": 1360, "y": 720}],
        "switches": [
            {"link_id": "sw_13_lock", "x": 1960, "y": 580, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d13_exit",
                "x": 2340,
                "y": 480,
                "w": 40,
                "h": 100,
                "required_links": ["valve_13_drain", "plate_13_dry", "sw_13_lock"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [
            {
                "id": "wz_13_1",
                "x": 760,
                "y": 600,
                "w": 840,
                "h": 120,
                "drained_y": 705,
                "controlled_by": "valve_13_drain",
                "toxic": False,
            }
        ],
        "valves": [{"link_id": "valve_13_drain", "x": 580, "y": 580}],
        "generators": [],
        "cables": [
            {"points": [[594, 580], [760, 580], [760, 680]], "link_id": "valve_13_drain"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp13_1", "x": 1660, "y": 580}],
        "spikes": [],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_13",
                "x": 1140,
                "y": 390,
                "title": "Hydro-Control Log",
                "text": "Drainage valves purge auxiliary basins in 3 seconds, allowing heavy crate handling.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 520, "y": 530, "text": "DRAIN VALVE"},
        ],
        "solution_steps": [
            "Turn 'valve_13_drain' at x=580 to lower the water level in 'wz_13_1'.",
            "Climb down into the basin, push crate 'c13_basin' onto 'plate_13_dry' at x=1360, and climb out via the right ladder.",
            "Hit 'sw_13_lock' at x=1960 and exit through 'd13_exit'.",
        ],
    },
    14: {
        "level_id": 14,
        "hint_route": ["sw_fan_14", "plate_14_high", "sw_14_gate"],
        "chapter": 4,
        "theme": "environmental",
        "name": "Chamber 14 // Ventilation",
        "subtitle": "Activate the vertical wind turbine to ride the updraft to the upper ventilation deck.",
        "width": 2800,
        "height": 840,
        "spawn": [100, 640],
        "exit": [2600, 380],
        "tiles": _base_room(
            2800,
            840,
            [
                [0, 700, 1280, 140],
                [1280, 460, 1520, 380],
                [2340, 220, 40, 140],
            ],
        ),
        "ladders": [],
        "crates": [{"id": "c14_aero", "x": 1520, "y": 400, "mass": 0.72}],
        "plates": [{"link_id": "plate_14_high", "x": 1960, "y": 460}],
        "switches": [
            {"link_id": "sw_fan_14", "x": 640, "y": 700, "mode": "permanent"},
            {"link_id": "sw_14_gate", "x": 2180, "y": 460, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d14_exit",
                "x": 2340,
                "y": 360,
                "w": 40,
                "h": 100,
                "required_links": ["plate_14_high", "sw_14_gate"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [
            {
                "id": "wind_14_lift",
                "x": 1060,
                "y": 380,
                "w": 180,
                "h": 320,
                "vx": 0.0,
                "vy": -2300.0,
                "controlled_by": "sw_fan_14",
                "active_by_default": False,
            }
        ],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[654, 700], [1060, 700]], "link_id": "sw_fan_14"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp14_1", "x": 1360, "y": 460}],
        "spikes": [],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_14",
                "x": 880,
                "y": 640,
                "title": "HVAC Engineering Note",
                "text": "Intake turbine #4 generates sufficient vertical thrust to lift a suited operator.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 580, "y": 650, "text": "TURBINE ON"},
        ],
        "solution_steps": [
            "Activate 'sw_fan_14' at x=640 to start vertical updraft 'wind_14_lift' at x=1060.",
            "Step into the wind column and ride it up to the y=460 deck (Checkpoint 'cp14_1').",
            "Push crate 'c14_aero' onto 'plate_14_high', activate 'sw_14_gate', and exit.",
        ],
    },
    15: {
        "level_id": 15,
        "hint_route": ["valve_15_steam", "plate_15", "valve_15_aux"],
        "chapter": 4,
        "theme": "environmental",
        "name": "Chamber 15 // Pressure System",
        "subtitle": "Shut off high-pressure steam vents using manual valves before crossing the pipework.",
        "width": 2800,
        "height": 780,
        "spawn": [100, 580],
        "exit": [2620, 560],
        "tiles": _base_room(
            2800,
            780,
            [
                [220, 470, 352, 16],
                [380, 386, 192, 14],
                [558, 400, 14, 70],
                [0, 640, 2800, 140],
                [1280, 470, 320, 30],
                [2340, 400, 40, 140],
            ],
        ),
        "ladders": [
            {'x': 190, 'y': 470, 'h': 170},{"x": 1250, "y": 470, "h": 170}],
        "crates": [{"id": "c15_pipe", "x": 620, "y": 580}],
        "plates": [{"link_id": "plate_15", "x": 1120, "y": 640}],
        "switches": [
            {'link_id': 'archive_15_a', 'x': 244, 'y': 470, 'mode': 'sequence'},
            {'link_id': 'archive_15_b', 'x': 318, 'y': 470, 'mode': 'sequence'},
        ],
        "doors": [
            {'id': 'archive_15_gate', 'x': 380, 'y': 400, 'w': 18, 'h': 70, 'required_links': ['archive_15']},
            {
                "id": "d15_exit",
                "x": 2340,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["valve_15_steam", "valve_15_aux", "plate_15"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [
            {"link_id": "valve_15_steam", "x": 420, "y": 640},
            {"link_id": "valve_15_aux", "x": 1460, "y": 470},
        ],
        "generators": [],
        "cables": [
            {"points": [[434, 640], [860, 640]], "link_id": "valve_15_steam"},
            {"points": [[1474, 470], [2360, 470], [2360, 540]], "link_id": "valve_15_aux"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [
            {
                "id": "sv_15_1",
                "x": 860,
                "y": 500,
                "w": 36,
                "h": 140,
                "period": 2.4,
                "duty_cycle": 0.55,
                "disabled_by": ["valve_15_steam"],
            },
            {
                "id": "sv_15_2",
                "x": 1920,
                "y": 500,
                "w": 36,
                "h": 140,
                "period": 2.6,
                "duty_cycle": 0.5,
                "disabled_by": [],
            },
        ],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp15_1", "x": 1680, "y": 640}],
        "spikes": [],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [
            {'group_id': 'archive_15', 'order': ['archive_15_a', 'archive_15_b']},
        ],
        "collectibles": [
            {'id': 'archive_log_15', 'x': 489, 'y': 436, 'title': 'Steam inspector', 'text': 'The isolation wheel still turns by hand during a blackout.'},
            {
                "id": "log_15",
                "x": 1340,
                "y": 420,
                "title": "Thermal Line Report",
                "text": "Ruptured steam lines vent superheated vapor. Close isolation valves prior to transit.",
            }
        ],
        "decorations": [
            {'type': 'monitor', 'x': 242, 'y': 390, 'text': 'ARCHIVE  1 > 2'},
            {"type": "monitor", "x": 360, "y": 590, "text": "VALVE #1"},
        ],
        "solution_steps": [
            "Turn 'valve_15_steam' at x=420 to shut off steam vent 'sv_15_1', then push 'c15_pipe' onto 'plate_15'.",
            "Climb the ladder at x=1250 to turn 'valve_15_aux' and grab Log #15.",
            "Time your run past periodic steam vent 'sv_15_2' at x=1920 and exit through 'd15_exit'.",
        ],
    },
    16: {
        "level_id": 16,
        "hint_route": ["plate_16_anchor", "gen_16_1", "valve_16_1"],
        "chapter": 4,
        "theme": "environmental",
        "name": "Chamber 16 // Structural Failure",
        "subtitle": "Sprint across unstable collapsing catwalks and power the rescue lift to clear the chasm.",
        "width": 2900,
        "height": 800,
        "spawn": [100, 580],
        "exit": [2720, 560],
        "tiles": _base_room(
            2900,
            800,
            [
                [0, 640, 680, 160],
                [1240, 640, 580, 160],
                [2080, 640, 820, 160],
                [2460, 400, 40, 140],
            ],
        ),
        "ladders": [],
        "crates": [{"id": "c16_anchor", "x": 1340, "y": 580}],
        "plates": [{"link_id": "plate_16_anchor", "x": 1680, "y": 640}],
        "switches": [],
        "doors": [
            {
                "id": "d16_exit",
                "x": 2460,
                "y": 540,
                "w": 40,
                "h": 100,
                "required_links": ["gen_16_1", "valve_16_1", "plate_16_anchor"],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp16_rescue",
                "x": 1840,
                "y": 620,
                "w": 110,
                "h": 22,
                "end_x": 1950,
                "end_y": 620,
                "speed": 125,
                "required_links": ["gen_16_1"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [{"link_id": "valve_16_1", "x": 2240, "y": 640}],
        "generators": [{"link_id": "gen_16_1", "x": 1480, "y": 640, "duration": 0.0}],
        "cables": [
            {"points": [[1504, 640], [1840, 640]], "link_id": "gen_16_1"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [
            {
                "id": "sv_16_1",
                "x": 2360,
                "y": 500,
                "w": 36,
                "h": 140,
                "period": 2.0,
                "duty_cycle": 0.6,
                "disabled_by": ["valve_16_1"],
            }
        ],
        "collapsing_platforms": [
            {"id": "cp_plat_16_1", "x": 720, "y": 630, "w": 120, "h": 18, "delay": 0.45, "respawn": 2.5},
            {"id": "cp_plat_16_2", "x": 900, "y": 630, "w": 120, "h": 18, "delay": 0.45, "respawn": 2.5},
            {"id": "cp_plat_16_3", "x": 1080, "y": 630, "w": 120, "h": 18, "delay": 0.45, "respawn": 2.5},
        ],
        "checkpoints": [
            {"id": "cp16_1", "x": 1280, "y": 640},
            {"id": "cp16_2", "x": 2120, "y": 640},
        ],
        "spikes": [],
        "acids": [
            {"x": 680, "y": 680, "w": 560, "h": 120},
            {"x": 1820, "y": 680, "w": 260, "h": 120},
        ],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_16",
                "x": 480,
                "y": 580,
                "title": "Structural Integrity Alert",
                "text": "Catwalk supports corroded over the coolant trench. Do not linger on spans.",
            }
        ],
        "decorations": [
            {"type": "warning_stripe", "x": 680, "y": 640, "w": 560},
        ],
        "solution_steps": [
            "Sprint and jump across the three collapsing platforms ('cp_plat_16_1' to '3') to Checkpoint 'cp16_1'.",
            "Push 'c16_anchor' onto 'plate_16_anchor' and start generator 'gen_16_1' to power 'mp16_rescue'.",
            "Cross 'mp16_rescue' to Checkpoint 'cp16_2', turn 'valve_16_1' to shut off 'sv_16_1', and exit.",
        ],
    },

    # =========================================================================
    # CHAPTER 5 — THE FINAL EXPERIMENT (Levels 17 - 20)
    # =========================================================================
    17: {
        "level_id": 17,
        "hint_route": ["gen_17_west", "opt_17_sync", "plate_17_core", "gen_17_east"],
        "chapter": 5,
        "theme": "core",
        "name": "Chamber 17 // System Reboot",
        "subtitle": "Bring both West and East sub-generators online and align the optical sync beam.",
        "width": 2900,
        "height": 800,
        "spawn": [100, 600],
        "exit": [2720, 580],
        "tiles": _base_room(
            2900,
            800,
            [
                [0, 660, 1260, 140],
                [1520, 660, 1380, 140],
                [1720, 480, 340, 30],
                [2460, 420, 40, 140],
            ],
        ),
        "ladders": [{"x": 1690, "y": 480, "h": 180}],
        "crates": [{"id": "c17_lens", "x": 540, "y": 600}],
        "plates": [{"link_id": "plate_17_core", "x": 980, "y": 660}],
        "switches": [],
        "doors": [
            {
                "id": "d17_exit",
                "x": 2460,
                "y": 560,
                "w": 40,
                "h": 100,
                "required_links": [
                    "gen_17_west",
                    "gen_17_east",
                    "opt_17_sync",
                    "plate_17_core",
                ],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [
            {
                "id": "mp17_bridge",
                "x": 1280,
                "y": 640,
                "w": 115,
                "h": 22,
                "end_x": 1390,
                "end_y": 640,
                "speed": 130,
                "required_links": ["opt_17_sync"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [
            {"link_id": "gen_17_west", "x": 240, "y": 660, "duration": 0.0},
            {"link_id": "gen_17_east", "x": 1880, "y": 480, "duration": 0.0},
        ],
        "cables": [
            {"points": [[264, 660], [360, 660], [360, 638]], "link_id": "gen_17_west"},
            {"points": [[1904, 480], [2480, 480], [2480, 560]], "link_id": "gen_17_east"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp17_1", "x": 1580, "y": 660}],
        "spikes": [{"x": 2140, "y": 642, "w": 96, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1260, "y": 690, "w": 260, "h": 110}],
        "lasers": [],
        "optical_beams": [
            {
                "link_id": "opt_17_sync",
                "x": 360,
                "y": 638,
                "dir": [1, 0],
                "max_length": 440,
                "receiver": [760, 624, 18, 28],
                "enabled_by": "gen_17_west",
            }
        ],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_17",
                "x": 1780,
                "y": 430,
                "title": "Core Reboot Protocol",
                "text": "West and East substations must be phase-locked before entering the central core.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 190, "y": 610, "text": "WEST GEN"},
            {"type": "monitor", "x": 1820, "y": 430, "text": "EAST GEN"},
        ],
        "solution_steps": [
            "Start 'gen_17_west' and push 'c17_lens' out of the beam onto 'plate_17_core' at x=980.",
            "Cross 'mp17_bridge' (powered by 'opt_17_sync') to Checkpoint 'cp17_1'.",
            "Climb the ladder to start 'gen_17_east' and grab Log #17, then jump the spikes and exit.",
        ],
    },
    18: {
        "level_id": 18,
        "hint_route": ["seq_18_1", "seq_18_2", "seq_18_3", "sw_wind_18", "plate_18_heavy"],
        "chapter": 5,
        "theme": "core",
        "name": "Chamber 18 // The Core",
        "subtitle": "Complete the 3-node core sequence, engage the wind lift, and place the heavy core stabilizer.",
        "width": 2900,
        "height": 840,
        "spawn": [100, 640],
        "exit": [2700, 400],
        "tiles": _base_room(
            2900,
            840,
            [
                [0, 700, 1340, 140],
                [1340, 480, 1560, 360],
                [980, 460, 40, 140],
                [2440, 240, 40, 140],
            ],
        ),
        "ladders": [],
        "crates": [{"id": "c18_heavy", "x": 1620, "y": 420}],
        "plates": [{"link_id": "plate_18_heavy", "x": 2120, "y": 480}],
        "switches": [
            {"link_id": "seq_18_1", "x": 260, "y": 700, "mode": "sequence"},
            {"link_id": "seq_18_2", "x": 520, "y": 700, "mode": "sequence"},
            {"link_id": "seq_18_3", "x": 780, "y": 700, "mode": "sequence"},
            {"link_id": "sw_wind_18", "x": 1080, "y": 700, "mode": "permanent"},
        ],
        "doors": [
            {
                "id": "d18_mid",
                "x": 980,
                "y": 600,
                "w": 40,
                "h": 100,
                "required_links": ["seq_core_18"],
                "logic": "ALL",
            },
            {
                "id": "d18_exit",
                "x": 2440,
                "y": 380,
                "w": 40,
                "h": 100,
                "required_links": ["seq_core_18", "plate_18_heavy"],
                "logic": "ALL",
            },
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [
            {
                "id": "wind_18_core",
                "x": 1160,
                "y": 400,
                "w": 160,
                "h": 300,
                "vx": 0.0,
                "vy": -2300.0,
                "controlled_by": "sw_wind_18",
                "active_by_default": False,
            }
        ],
        "water_zones": [],
        "valves": [],
        "generators": [],
        "cables": [
            {"points": [[1094, 700], [1160, 700]], "link_id": "sw_wind_18"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp18_1", "x": 1440, "y": 480}],
        "spikes": [{"x": 2270, "y": 462, "w": 80, "h": 18, "orientation": "up"}],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [
            {"group_id": "seq_core_18", "order": ["seq_18_1", "seq_18_2", "seq_18_3"]}
        ],
        "collectibles": [
            {
                "id": "log_18",
                "x": 2260,
                "y": 420,
                "title": "Experiment ECHO-7 Dossier",
                "text": "The facility was built as an autonomous subterranean biosphere. No surface exit was ever planned.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 220, "y": 650, "text": "CORE 1"},
            {"type": "monitor", "x": 480, "y": 650, "text": "CORE 2"},
            {"type": "monitor", "x": 740, "y": 650, "text": "CORE 3"},
        ],
        "solution_steps": [
            "Activate 'seq_18_1', 'seq_18_2', and 'seq_18_3' in order to open 'd18_mid'.",
            "Hit 'sw_wind_18' and ride the updraft 'wind_18_core' to Checkpoint 'cp18_1' on the upper deck.",
            "Push crate 'c18_heavy' onto 'plate_18_heavy' (or jump the spikes after positioning) and exit through 'd18_exit'.",
        ],
    },
    19: {
        "level_id": 19,
        "hint_route": ["valve_19_coolant", "gen_19_stabilizer", "sw_19_sprint"],
        "chapter": 5,
        "theme": "core",
        "name": "Chamber 19 // Containment Failure",
        "subtitle": "Drain the reactor basin, power the crusher stabilizer, and beat the timed lockdown door.",
        "width": 2900,
        "height": 820,
        "spawn": [100, 520],
        "exit": [2720, 500],
        "tiles": _base_room(
            2900,
            820,
            [
                [0, 580, 720, 240],
                [720, 720, 760, 100],
                [1480, 580, 1420, 240],
                [2460, 340, 40, 140],
            ],
        ),
        "ladders": [
            {"x": 690, "y": 580, "h": 140},
            {"x": 1450, "y": 580, "h": 140},
        ],
        "crates": [],
        "plates": [],
        "switches": [
            {
                "link_id": "sw_19_sprint",
                "x": 2120,
                "y": 580,
                "mode": "timed",
                "duration": 5.5,
            }
        ],
        "doors": [
            {
                "id": "d19_exit",
                "x": 2460,
                "y": 480,
                "w": 40,
                "h": 100,
                "required_links": [
                    "valve_19_coolant",
                    "gen_19_stabilizer",
                    "sw_19_sprint",
                ],
                "logic": "ALL",
            }
        ],
        "moving_platforms": [],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [
            {
                "id": "wz_19_1",
                "x": 720,
                "y": 600,
                "w": 760,
                "h": 120,
                "drained_y": 705,
                "controlled_by": "valve_19_coolant",
                "toxic": False,
            }
        ],
        "valves": [{"link_id": "valve_19_coolant", "x": 520, "y": 580}],
        "generators": [
            {"link_id": "gen_19_stabilizer", "x": 1100, "y": 720, "duration": 0.0}
        ],
        "cables": [
            {"points": [[1124, 720], [1820, 720], [1820, 340]], "link_id": "gen_19_stabilizer"}
        ],
        "mirrors": [],
        "crushers": [
            {
                "id": "cr19_1",
                "x": 1800,
                "y": 340,
                "w": 90,
                "h": 40,
                "travel": 240,
                "period": 1.5,
                "disabled_by": ["gen_19_stabilizer"],
            }
        ],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [{"id": "cp19_1", "x": 1560, "y": 580}],
        "spikes": [{"x": 2260, "y": 562, "w": 80, "h": 18, "orientation": "up"}],
        "acids": [],
        "lasers": [],
        "optical_beams": [],
        "sequences": [],
        "collectibles": [
            {
                "id": "log_19",
                "x": 920,
                "y": 660,
                "title": "Emergency Broadcast",
                "text": "Containment seals failing across Sector E. Surface freight elevator unlocked at Chamber 20.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 460, "y": 530, "text": "BASIN DRAIN"},
        ],
        "solution_steps": [
            "Turn 'valve_19_coolant' at x=520 to drain the basin, climb down, grab Log #19, and start 'gen_19_stabilizer' at x=1100.",
            "Climb out to Checkpoint 'cp19_1', pass halted crusher 'cr19_1', trigger 'sw_19_sprint', and sprint over the spikes through 'd19_exit'.",
        ],
    },
    20: {
        "level_id": 20,
        "hint_route": ["gen_20_alpha", "opt_20_final", "plate_20_lens_park", "seq_20_1", "seq_20_2", "seq_20_3", "plate_20_omega", "sw_20_final_sprint"],
        "chapter": 5,
        "theme": "core",
        "name": "Chamber 20 // Final Escape",
        "subtitle": "Synthesize all facility systems: power the optical array, complete the ignition sequence, shield the laser, and escape!",
        "width": 3200,
        "height": 820,
        "spawn": [90, 620],
        "exit": [3020, 600],
        "tiles": _base_room(
            3200,
            820,
            [
                [0, 680, 1280, 140],
                [520, 510, 240, 30],
                [1560, 680, 1640, 140],
                [1160, 440, 40, 140],
                [2820, 440, 40, 140],
            ],
        ),
        "ladders": [{"x": 490, "y": 510, "h": 170}],
        "crates": [
            {"id": "c20_lens", "x": 380, "y": 620},
            {"id": "c20_omega", "x": 1720, "y": 620},
        ],
        "plates": [
            {"link_id": "plate_20_lens_park", "x": 1040, "y": 680},
            {"link_id": "plate_20_omega", "x": 2360, "y": 680},
        ],
        "switches": [
            {"link_id": "seq_20_1", "x": 580, "y": 510, "mode": "sequence"},
            {"link_id": "seq_20_2", "x": 700, "y": 510, "mode": "sequence"},
            {"link_id": "seq_20_3", "x": 920, "y": 680, "mode": "sequence"},
            {
                "link_id": "sw_20_final_sprint",
                "x": 2500,
                "y": 680,
                "mode": "timed",
                "duration": 5.5,
            },
        ],
        "doors": [
            {
                "id": "d20_mid",
                "x": 1160,
                "y": 580,
                "w": 40,
                "h": 100,
                "required_links": ["seq_escape_20", "opt_20_final", "plate_20_lens_park"],
                "logic": "ALL",
            },
            {
                "id": "d20_exit",
                "x": 2820,
                "y": 580,
                "w": 40,
                "h": 100,
                "required_links": [
                    "seq_escape_20",
                    "opt_20_final",
                    "plate_20_omega",
                    "sw_20_final_sprint",
                ],
                "logic": "ALL",
            },
        ],
        "moving_platforms": [
            {
                "id": "mp20_ferry",
                "x": 1290,
                "y": 660,
                "w": 130,
                "h": 22,
                "end_x": 1420,
                "end_y": 660,
                "speed": 135,
                "required_links": ["opt_20_final"],
                "active_by_default": False,
            }
        ],
        "conveyors": [],
        "wind_zones": [],
        "water_zones": [],
        "valves": [],
        "generators": [{"link_id": "gen_20_alpha", "x": 180, "y": 680, "duration": 0.0}],
        "cables": [
            {"points": [[204, 680], [280, 680], [280, 658]], "link_id": "gen_20_alpha"},
            {"points": [[660, 658], [1180, 658]], "link_id": "opt_20_final"},
        ],
        "mirrors": [],
        "crushers": [],
        "steam_vents": [],
        "collapsing_platforms": [],
        "checkpoints": [
            {"id": "cp20_1", "x": 1620, "y": 680},
            {"id": "cp20_2", "x": 2260, "y": 680},
        ],
        "spikes": [{"x": 2640, "y": 662, "w": 80, "h": 18, "orientation": "up"}],
        "acids": [{"x": 1280, "y": 710, "w": 280, "h": 110}],
        "lasers": [
            {
                "x": 2120,
                "y": 440,
                "dir": [0, 1],
                "max_length": 240,
                "disabled_by": ["plate_20_omega"],
                "period": 2.2,
                "duty_cycle": 0.5,
            }
        ],
        "optical_beams": [
            {
                "link_id": "opt_20_final",
                "x": 280,
                "y": 658,
                "dir": [1, 0],
                "max_length": 400,
                "receiver": [660, 644, 18, 28],
                "enabled_by": "gen_20_alpha",
            }
        ],
        "sequences": [
            {"group_id": "seq_escape_20", "order": ["seq_20_1", "seq_20_2", "seq_20_3"]}
        ],
        "collectibles": [
            {
                "id": "log_20",
                "x": 1920,
                "y": 620,
                "title": "Surface Ascent Telemetry",
                "text": "External hatch unlocked. Daylight sensors registering clear skies above Sector 7.",
            }
        ],
        "decorations": [
            {"type": "monitor", "x": 540, "y": 460, "text": "IGN [1]"},
            {"type": "monitor", "x": 660, "y": 460, "text": "IGN [2]"},
            {"type": "monitor", "x": 880, "y": 630, "text": "IGN [3]"},
            {"type": "sign_arrow", "x": 2900, "y": 630, "text": "SURFACE LIFT"},
        ],
        "solution_steps": [
            "Start 'gen_20_alpha' and push 'c20_lens' out of the optical beam onto 'plate_20_lens_park' at x=1040.",
            "Climb the ladder at x=490 to hit 'seq_20_1' and 'seq_20_2', then drop down and hit 'seq_20_3' to open 'd20_mid'.",
            "Ride 'mp20_ferry' to Checkpoint 'cp20_1', push 'c20_omega' past the periodic laser onto 'plate_20_omega' at x=2360.",
            "Trigger timed switch 'sw_20_final_sprint', sprint over the final spikes through 'd20_exit', and reach the surface portal.",
        ],
    },
}


class LevelValidator:
    """Validates level JSON dictionaries for structural, spatial, and puzzle-link integrity."""

    @staticmethod
    def validate(data: dict[str, Any]) -> list[str]:
        errors = schema_errors(data)
        if errors:
            return errors
        lvl_id = data.get("level_id", "?")

        width = data.get("width", 0)
        height = data.get("height", 0)
        if not isinstance(width, int) or width < 640 or not isinstance(height, int) or height < 480:
            errors.append(f"Level {lvl_id}: Invalid dimensions ({width}x{height}).")

        spawn = data.get("spawn")
        if not (isinstance(spawn, list) and len(spawn) == 2):
            errors.append(f"Level {lvl_id}: Missing or invalid player 'spawn'.")
        elif not (0 <= spawn[0] <= width and 0 <= spawn[1] <= height):
            errors.append(f"Level {lvl_id}: Spawn {spawn} is out of level bounds.")

        exit_pos = data.get("exit")
        if not (isinstance(exit_pos, list) and len(exit_pos) == 2):
            errors.append(f"Level {lvl_id}: Missing or invalid level 'exit'.")
        elif not (0 <= exit_pos[0] <= width and 0 <= exit_pos[1] <= height):
            errors.append(f"Level {lvl_id}: Exit {exit_pos} is out of level bounds.")

        if not data.get("tiles"):
            errors.append(f"Level {lvl_id}: Level has no solid 'tiles'.")

        # Gather all valid signal producers
        producers: set[str] = set()
        for p in data.get("plates", []):
            if p.get("link_id"):
                producers.add(p["link_id"])
        for sw in data.get("switches", []):
            if sw.get("link_id"):
                producers.add(sw["link_id"])
        for ob in data.get("optical_beams", []):
            if ob.get("link_id"):
                producers.add(ob["link_id"])
        for seq in data.get("sequences", []):
            if seq.get("group_id"):
                producers.add(seq["group_id"])
            for step_link in seq.get("order", []):
                if step_link not in {sw["link_id"] for sw in data.get("switches", []) if sw.get("mode") == "sequence"}:
                    errors.append(
                        f"Level {lvl_id}: Sequence '{seq.get('group_id')}' references unknown switch '{step_link}'."
                    )
        for gen in data.get("generators", []):
            if gen.get("link_id"):
                producers.add(gen["link_id"])
        for v in data.get("valves", []):
            if v.get("link_id"):
                producers.add(v["link_id"])

        for relay in data.get("latching_relays", []):
            producers.add(relay["link_id"])
        for inv in data.get("signal_inverters", []):
            producers.add(inv["link_id"])
        for panel in data.get("routing_consoles", []):
            producers.update((panel["a_signal"], panel["b_signal"]))
        for relay in data.get("latching_relays", []):
            for link in relay.get("required_links", []):
                if link not in producers:
                    errors.append(f"Relay {relay['link_id']} needs unknown signal {link}")
        for inv in data.get("signal_inverters", []):
            if inv.get("input") not in producers:
                errors.append(f"Inverted signal {inv['link_id']} has unknown input")
            if inv.get("water_zone") and inv["water_zone"] not in {
                zone["id"] for zone in data.get("water_zones", [])
            }:
                errors.append(f"Inverted signal {inv['link_id']} has unknown water zone")
        buses = {}
        for panel in data.get("routing_consoles", []):
            route = panel["route_id"]
            outputs = (panel["a_signal"], panel["b_signal"])
            if route in buses and buses[route] != outputs:
                errors.append(f"Route {route} has inconsistent output signals")
            buses[route] = outputs
            for link in panel.get("required_links", []):
                if link not in producers:
                    errors.append(f"Routing panel {panel['id']} requires unknown signal {link}")

        for link in data.get("hint_route", []):
            if link not in producers:
                errors.append(f"Unknown hint route signal {link}")
        for cable in data.get("cables", []):
            if cable["link_id"] not in producers:
                errors.append(f"Unknown cable signal {cable['link_id']}")
        beam_power = {b["link_id"]: [b["enabled_by"]] if b.get("enabled_by") else []
                      for b in data.get("optical_beams", [])}
        try:
            tuple(TopologicalSorter(beam_power).static_order())
        except CycleError as exc:
            errors.append(f"Optical power dependency cycle: {exc.args[1]}")
        # Verify all signal consumers reference existing producers
        for d in data.get("doors", []):
            for req in d.get("required_links", []):
                if req not in producers:
                    errors.append(
                        f"Level {lvl_id}: Door '{d.get('id')}' requires unknown signal '{req}'."
                    )
        for mp in data.get("moving_platforms", []):
            for req in mp.get("required_links", []):
                if req not in producers:
                    errors.append(
                        f"Level {lvl_id}: MovingPlatform '{mp.get('id')}' requires unknown signal '{req}'."
                    )
        for ls in data.get("lasers", []):
            for req in ls.get("disabled_by", []):
                if req not in producers:
                    errors.append(
                        f"Level {lvl_id}: Laser references unknown disabling signal '{req}'."
                    )
        for cr in data.get("crushers", []):
            for req in cr.get("disabled_by", []):
                if req not in producers:
                    errors.append(
                        f"Level {lvl_id}: Crusher '{cr.get('id')}' references unknown signal '{req}'."
                    )
        for sv in data.get("steam_vents", []):
            for req in sv.get("disabled_by", []):
                if req not in producers:
                    errors.append(
                        f"Level {lvl_id}: SteamVent '{sv.get('id')}' references unknown signal '{req}'."
                    )
        for ob in data.get("optical_beams", []):
            en = ob.get("enabled_by")
            if en and en not in producers:
                errors.append(
                    f"Level {lvl_id}: OpticalBeam '{ob.get('link_id')}' enabled_by unknown signal '{en}'."
                )
        for wz in data.get("water_zones", []):
            ctrl = wz.get("controlled_by")
            if ctrl and ctrl not in producers:
                errors.append(
                    f"Level {lvl_id}: WaterZone '{wz.get('id')}' controlled_by unknown signal '{ctrl}'."
                )
        for wind in data.get("wind_zones", []):
            ctrl = wind.get("controlled_by")
            if ctrl and ctrl not in producers:
                errors.append(
                    f"Level {lvl_id}: WindZone '{wind.get('id')}' controlled_by unknown signal '{ctrl}'."
                )
        for conv in data.get("conveyors", []):
            power = conv.get("powered_by")
            if power and power not in producers:
                errors.append(f"Unknown conveyor power signal {power}")
            rev = conv.get("reversed_by")
            if rev and rev not in producers:
                errors.append(
                    f"Level {lvl_id}: Conveyor '{conv.get('id')}' reversed_by unknown signal '{rev}'."
                )

        return errors


class LevelLoader:
    """Manages the 80 JSON rooms across eight chapters."""

    TOTAL_LEVELS = 80
    TOTAL_CHAPTERS = 8

    def __init__(self, levels_dir: Path = LEVELS_DIR) -> None:
        self.levels_dir = Path(levels_dir)

    def ensure_default_levels(self, overwrite_outdated: bool = False) -> None:
        """Explicitly provision missing files. Existing authored files always win."""
        self.levels_dir.mkdir(parents=True, exist_ok=True)
        for number, data in DEFAULT_LEVELS.items():
            path = self.levels_dir / f"level_{number:02d}.json"
            if not path.exists():
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_level_data(self, level_num: int) -> dict[str, Any]:
        path = self.levels_dir / f"level_{level_num:02d}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("level_id") != level_num:
                raise ValueError("Expected a level object with matching level_id")
            errors = LevelValidator.validate(data)
            if errors:
                raise ValueError(" | ".join(errors))
            return data
        except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
            raise ValueError(f"{path.name}: {exc}") from exc

    def validate_all_levels(self) -> dict[int, list[str]]:
        report = {}
        for number in range(1, self.TOTAL_LEVELS + 1):
            try:
                self.load_level_data(number)
                report[number] = []
            except ValueError as exc:
                report[number] = [str(exc)]
        return report

    @staticmethod
    def get_chapter_metadata(chapter_num: int) -> dict[str, Any]:
        return CHAPTER_METADATA.get(chapter_num, CHAPTER_METADATA[1])

    @staticmethod
    def get_chapter_for_level(level_num: int) -> int:
        return max(1, min(8, (int(level_num) - 1) // 10 + 1))