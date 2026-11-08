"""Distinctive, world-anchored environmental effects for all 80 levels of ECHO-7.

Each level 1..80 has a deterministic atmospheric sub-profile (10 distinct room signatures
per chapter x 8 chapters = 80 unique level profiles). All effects are drawn on the
640x360 logical background surface BEFORE solid terrain, hazards, puzzle devices, and
the player, and never overlap solid tile interiors.
"""
from __future__ import annotations
import math
import pygame

SCALE = 2
LOGICAL_W = 640
LOGICAL_H = 360

# 80 unique level atmospheric descriptors (10 per chapter)
LEVEL_FX_NAMES: dict[int, str] = {
    # Chapter 1: Awakening (Levels 1-10)
    1: "cryo_wake_condensation", 2: "bench_oscilloscope_sweep", 3: "freight_hoist_dust_shaft",
    4: "cleanroom_uv_sterilizer", 5: "server_rack_heartbeat", 6: "centrifuge_strobe_hum",
    7: "specimen_stasis_bubbles", 8: "telemetry_uplink_pulses", 9: "calibration_grid_flicker",
    10: "sector_airlock_beacon",
    # Chapter 2: Mechanical Depths (Levels 11-20)
    11: "flywheel_grease_motes", 12: "stamping_press_heat_plume", 13: "conveyor_roller_sparks",
    14: "boiler_relief_wisps", 15: "chain_hoist_sway_links", 16: "foundry_ladle_glow",
    17: "gearbox_oil_drip", 18: "piston_manifold_exhaust", 19: "kiln_draft_embers",
    20: "turbine_hall_tachometer",
    # Chapter 3: Power Grid (Levels 21-30)
    21: "busbar_corona_discharge", 22: "transformer_hum_rings", 23: "capacitor_charge_ladder",
    24: "jacobs_ladder_arc", 25: "substation_phase_scope", 26: "hv_insulator_flashover",
    27: "feeder_conduit_packets", 28: "switchgear_relay_strobe", 29: "inductor_flux_halo",
    30: "grid_sync_oscillator",
    # Chapter 4: Surveillance Grid (Levels 31-40)
    31: "panopticon_laser_fan", 32: "crt_wall_scan_roll", 33: "iris_aperture_dilation",
    34: "fiber_trunk_data_burst", 35: "prism_refraction_motes", 36: "security_radar_sweep",
    37: "encrypted_matrix_rain", 38: "optical_bench_collimator", 39: "interlock_beacon_grid",
    40: "overwatch_citadel_pulse",
    # Chapter 5: Flood Control (Levels 41-50)
    41: "sluice_mist_plume", 42: "caisson_barometer_wave", 43: "pipe_flange_weeping",
    44: "buoyancy_tank_sonar", 45: "spillway_vapor_drift", 46: "hydro_manifold_cavitation",
    47: "penstock_pressure_rings", 48: "sump_pump_tach_pulse", 49: "condenser_droplet_chain",
    50: "main_weir_telemetry",
    # Chapter 6: Core Collapse (Levels 51-60)
    51: "slag_crucible_updraft", 52: "coolant_boil_geyser", 53: "containment_crack_flare",
    54: "thermal_siphon_shimmer", 55: "control_rod_chatter", 56: "furnace_tuyere_sparks",
    57: "overpressure_strobe_arc", 58: "core_flux_scintillation", 59: "blast_baffle_cinders",
    60: "reactor_scram_horizontals",
    # Chapter 7: Broken Spire (Levels 61-70)
    61: "shear_shaft_masonry_dust", 62: "severed_conduit_whip", 63: "sky_breach_light_shaft",
    64: "wind_tunnel_streaks", 65: "observatory_shutter_flutter", 66: "torn_truss_arc_snap",
    67: "high_altitude_graupel", 68: "stabilizer_gyro_wobble", 69: "fracture_vent_updraft",
    70: "spire_crown_lightning",
    # Chapter 8: Surface Breach (Levels 71-80)
    71: "outcrop_katabatic_gust", 72: "relay_dish_telemetry_beam", 73: "moss_spore_moon_drift",
    74: "watchtower_warning_sweep", 75: "ridge_ground_fog_bank", 76: "breached_roof_starlight",
    77: "viaduct_wind_eddies", 78: "comms_mast_strobe_pair", 79: "airlock_approach_beacons",
    80: "surface_breach_finale_aurora",
}


def get_level_fx_name(level_num: int) -> str:
    lvl = max(1, min(80, int(level_num)))
    return LEVEL_FX_NAMES[lvl]


def _point_in_solid(wx: int, wy: int, world_tiles: list) -> bool:
    """Checks if a virtual-space point (wx, wy) lies inside any collidable solid tile."""
    for r in world_tiles:
        if r.x - 8 <= wx <= r.x + r.w + 8 and r.y - 8 <= wy <= r.y + r.h + 8:
            return True
    return False


def draw_level_specific_fx(
    surf: pygame.Surface,
    level_num: int,
    chapter: int,
    pal: dict[str, tuple[int, int, int]],
    cam_lx: int,
    cam_ly: int,
    base_ly: int,
    world_lw: int,
    world_lh: int,
    elapsed: float,
    reduced_motion: bool,
    powered: bool,
    world_tiles: list,
    active_signals: set[str] | None = None,
) -> None:
    """Renders the level's unique atmospheric effect layer across visible bays."""
    lvl = max(1, min(80, int(level_num)))
    ch = max(1, min(8, int(chapter)))
    sub_idx = (lvl - 1) % 10  # 0..9 unique variation within the chapter
    t = 0.0 if reduced_motion else elapsed
    active_col = pal["accent"] if powered else pal["hi"]
    warn_col = pal["warn"]

    bay_w = 120 + (sub_idx % 3) * 20
    first_bay = max(0, (cam_lx // bay_w) - 1)
    last_bay = min(world_lw // bay_w + 1, (cam_lx + LOGICAL_W) // bay_w + 1)

    for bay in range(first_bay, last_bay + 1):
        # Deterministic world-space anchor per level and bay
        seed = bay * 37 + lvl * 53 + ch * 19
        wx_l = bay * bay_w + (seed % max(24, bay_w - 32))
        wy_l = base_ly + 58 + ((seed * 7) % 176)
        sx = wx_l - cam_lx
        sy = wy_l - cam_ly
        if not (-32 <= sx < LOGICAL_W + 32 and -32 <= sy < LOGICAL_H + 32):
            continue
        # Never draw inside a solid terrain block
        if _point_in_solid(wx_l * SCALE, wy_l * SCALE, world_tiles):
            continue

        phase = t * (1.8 + sub_idx * 0.22) + bay * 0.9

        if ch == 1:
            if sub_idx in (0, 3, 6):
                # Vertical cleanroom/cryo light shaft with rising micro-motes
                pygame.draw.rect(surf, pal["recess"], (sx - 8, sy - 28, 16, 52))
                pygame.draw.line(surf, pal["edge"], (sx - 8, sy - 28), (sx - 8, sy + 24), 1)
                pygame.draw.line(surf, pal["edge"], (sx + 8, sy - 28), (sx + 8, sy + 24), 1)
                for m in range(3):
                    my = sy + 20 - int(((phase * 14 + m * 16) % 44))
                    mx = sx - 4 + ((m * 5 + sub_idx) % 9)
                    pygame.draw.rect(surf, active_col, (mx, my, 2, 2))
            elif sub_idx in (1, 4, 8):
                # Multi-channel diagnostic telemetry bar-graph & harmonic sine trace
                pygame.draw.rect(surf, pal["seam"], (sx - 16, sy - 10, 32, 20))
                pygame.draw.rect(surf, pal["edge"], (sx - 16, sy - 10, 32, 20), 1)
                for bar_i in range(5):
                    bh = 3 + int(6 * (0.5 + 0.5 * math.sin(phase * 1.5 + bar_i * 0.9 + sub_idx)))
                    bx = sx - 12 + bar_i * 5
                    pygame.draw.rect(surf, active_col if bar_i != 4 else warn_col, (bx, sy + 7 - bh, 3, bh))
            else:
                # Staggered lab specimen/centrifuge ring pulse
                rad = 6 + (sub_idx % 3) * 2
                pygame.draw.circle(surf, pal["seam"], (sx, sy), rad + 2)
                pygame.draw.circle(surf, pal["edge"], (sx, sy), rad + 2, 1)
                ang = phase * (1.6 if sub_idx % 2 == 0 else -1.6)
                px = sx + int(round(math.cos(ang) * rad))
                py = sy + int(round(math.sin(ang) * rad))
                pygame.draw.rect(surf, active_col, (px - 1, py - 1, 3, 3))

        elif ch == 2:
            if sub_idx in (0, 4, 6):
                # Counter-weighted chain hoist / oil-drip plumb line
                pygame.draw.line(surf, pal["edge"], (sx, sy - 34), (sx, sy + 18), 1)
                bob_y = sy - 8 + int(round(10 * math.sin(phase)))
                pygame.draw.rect(surf, pal["panel"], (sx - 5, bob_y - 4, 10, 8))
                pygame.draw.rect(surf, active_col, (sx - 2, bob_y - 1, 4, 2))
            elif sub_idx in (1, 5, 8):
                # Foundry crucible / kiln louver glow with rising thermal sparks
                pygame.draw.rect(surf, pal["seam"], (sx - 14, sy - 8, 28, 16))
                for slot in range(-5, 6, 4):
                    pygame.draw.line(surf, warn_col if powered else pal["edge"], (sx - 11, sy + slot), (sx + 11, sy + slot), 1)
                if not reduced_motion:
                    for sp_i in range(2):
                        spy = sy - 10 - int((phase * 18 + sp_i * 13) % 26)
                        spx = sx - 4 + int(3 * math.sin(phase + sp_i))
                        pygame.draw.rect(surf, active_col, (spx, spy, 2, 2))
            else:
                # Reciprocating rocker-arm & tachometer dial
                pygame.draw.circle(surf, pal["seam"], (sx, sy), 9)
                pygame.draw.circle(surf, pal["hi"], (sx, sy), 9, 1)
                arm_dx = int(round(7 * math.cos(phase * 1.4)))
                arm_dy = int(round(7 * math.sin(phase * 1.4)))
                pygame.draw.line(surf, active_col, (sx - arm_dx, sy - arm_dy), (sx + arm_dx, sy + arm_dy), 2)

        elif ch == 3:
            if sub_idx in (0, 3, 5):
                # Jacob's ladder climbing arc between twin V-horn electrodes
                pygame.draw.line(surf, pal["hi"], (sx - 4, sy + 14), (sx - 10, sy - 18), 2)
                pygame.draw.line(surf, pal["hi"], (sx + 4, sy + 14), (sx + 10, sy - 18), 2)
                climb = int((phase * 16) % 28)
                ay = sy + 12 - climb
                span = 4 + climb // 5
                jit = 0 if reduced_motion else ((int(phase * 12) + bay) % 3 - 1)
                pygame.draw.line(surf, active_col, (sx - span, ay), (sx, ay + jit), 1)
                pygame.draw.line(surf, active_col, (sx, ay + jit), (sx + span, ay), 1)
            elif sub_idx in (2, 6, 8):
                # Capacitor bank sequential charge ladder
                for rung in range(4):
                    ry = sy + 10 - rung * 7
                    lit = ((int(phase * 3) - rung) % 4) == 0 if not reduced_motion else (rung == 0)
                    col = active_col if lit else pal["edge"]
                    pygame.draw.rect(surf, col, (sx - 10, ry, 20, 4))
            else:
                # Substation phase-lock Lissajous / harmonic scope
                pygame.draw.rect(surf, pal["seam"], (sx - 13, sy - 11, 26, 22))
                pygame.draw.rect(surf, pal["edge"], (sx - 13, sy - 11, 26, 22), 1)
                pts = []
                for px_i in range(-9, 10, 3):
                    py_i = int(round(6 * math.sin(phase + px_i * (0.25 + 0.03 * sub_idx))))
                    pts.append((sx + px_i, sy + py_i))
                if len(pts) >= 2:
                    pygame.draw.lines(surf, active_col, False, pts, 1)

        elif ch == 4:
            if sub_idx in (0, 2, 5):
                # Panopticon iris / radar sweep reticle
                pygame.draw.circle(surf, pal["seam"], (sx, sy), 11)
                pygame.draw.circle(surf, pal["edge"], (sx, sy), 11, 1)
                pygame.draw.circle(surf, pal["recess"], (sx, sy), 6, 1)
                ang = phase * 1.1
                rx = sx + int(round(9 * math.cos(ang)))
                ry = sy + int(round(9 * math.sin(ang)))
                pygame.draw.line(surf, active_col, (sx, sy), (rx, ry), 1)
                pygame.draw.rect(surf, warn_col, (sx - 1, sy - 1, 2, 2))
            elif sub_idx in (1, 3, 6):
                # Vertical fiber-optic data packet columns
                for col_i in (-6, 0, 6):
                    pygame.draw.line(surf, pal["seam"], (sx + col_i, sy - 20), (sx + col_i, sy + 20), 2)
                    pkt_y = sy - 18 + int((phase * 18 + col_i * 7 + sub_idx * 5) % 34)
                    pygame.draw.rect(surf, active_col if col_i != 0 else warn_col, (sx + col_i - 1, pkt_y, 2, 4))
            else:
                # Optical collimator crosshairs with stepped focus brackets
                spread = 6 + int(round(3 * math.sin(phase)))
                pygame.draw.line(surf, pal["edge"], (sx - 12, sy), (sx + 12, sy), 1)
                pygame.draw.line(surf, pal["edge"], (sx, sy - 12), (sx, sy + 12), 1)
                pygame.draw.rect(surf, active_col, (sx - spread, sy - spread, spread * 2, spread * 2), 1)

        elif ch == 5:
            if sub_idx in (0, 4, 8):
                # High-pressure pipe flange condensation & mist plume (never a floor pool)
                pygame.draw.rect(surf, pal["panel"], (sx - 12, sy - 16, 24, 6))
                pygame.draw.rect(surf, pal["edge"], (sx - 12, sy - 16, 24, 6), 1)
                for d_i in range(2):
                    dy = sy - 8 + int((phase * 15 + d_i * 14) % 28)
                    pygame.draw.rect(surf, active_col, (sx - 4 + d_i * 8, dy, 2, 3))
            elif sub_idx in (1, 3, 6):
                # Caisson depth-sonar / pressure wave tube
                pygame.draw.rect(surf, pal["seam"], (sx - 7, sy - 22, 14, 44))
                pygame.draw.rect(surf, pal["edge"], (sx - 7, sy - 22, 14, 44), 1)
                lvl_y = sy + 6 - int(round(12 * math.sin(phase * 0.8)))
                pygame.draw.line(surf, active_col, (sx - 5, lvl_y), (sx + 5, lvl_y), 2)
            else:
                # Twin counter-balanced hydraulic manifold gauges
                for gx in (sx - 9, sx + 9):
                    pygame.draw.circle(surf, pal["seam"], (gx, sy), 7)
                    pygame.draw.circle(surf, pal["edge"], (gx, sy), 7, 1)
                    ga = -0.6 + 1.2 * math.sin(phase + gx * 0.2)
                    pygame.draw.line(surf, active_col, (gx, sy), (gx + int(5 * math.cos(ga)), sy + int(5 * math.sin(ga))), 1)

        elif ch == 6:
            if sub_idx in (0, 2, 5, 8):
                # Containment thermal vent with stepped ember updraft
                pygame.draw.rect(surf, pal["seam"], (sx - 12, sy - 14, 24, 28))
                pygame.draw.rect(surf, warn_col if powered else pal["edge"], (sx - 12, sy - 14, 24, 28), 1)
                for e_i in range(3):
                    ey = sy + 10 - int((phase * 20 + e_i * 9) % 24)
                    ex = sx - 6 + e_i * 6 + int(2 * math.sin(phase + e_i))
                    pygame.draw.rect(surf, active_col, (ex, ey, 2, 2))
            else:
                # Core flux control-rod position indicator & warning strobe
                pygame.draw.rect(surf, pal["recess"], (sx - 10, sy - 20, 20, 40))
                rod_h = 10 + int(round(12 * (0.5 + 0.5 * math.sin(phase * 1.3))))
                pygame.draw.rect(surf, warn_col, (sx - 6, sy - 18, 12, rod_h))
                pygame.draw.line(surf, active_col, (sx - 8, sy - 18 + rod_h), (sx + 8, sy - 18 + rod_h), 2)

        elif ch == 7:
            if sub_idx in (0, 3, 6):
                # Upper-spire wind-tunnel slipstream streaks & falling masonry dust
                for w_i in range(3):
                    wx_off = int((phase * 24 + w_i * 17) % 36) - 18
                    wy_off = (w_i - 1) * 9
                    pygame.draw.line(surf, pal["hi"], (sx + wx_off, sy + wy_off), (sx + wx_off + 7, sy + wy_off), 1)
            elif sub_idx in (1, 5, 9):
                # Severed high-altitude conduit with intermittent arc snap
                sway = int(round(4 * math.sin(phase)))
                pygame.draw.lines(surf, pal["edge"], False, [(sx, sy - 26), (sx + sway // 2, sy - 12), (sx + sway, sy)], 2)
                if int(phase * 3) % 4 == 0:
                    pygame.draw.line(surf, active_col, (sx + sway - 3, sy), (sx + sway + 3, sy + 3), 1)
                    pygame.draw.line(surf, active_col, (sx + sway + 3, sy), (sx + sway - 2, sy + 4), 1)
            else:
                # Broken stabilizer gyro, moving irregularly with a damaged bearing.
                pygame.draw.circle(surf, pal["edge"], (sx, sy), 10, 1)
                wobble = 0.38 * math.sin(phase * 1.3) + 0.11 * math.sin(phase * 3.4)
                dx = int(round(8 * math.cos(wobble)))
                dy = int(round(8 * math.sin(wobble)))
                pygame.draw.line(surf, active_col, (sx - dx, sy - dy), (sx + dx, sy + dy), 1)
                pygame.draw.rect(surf, pal["warn"], (sx + dx - 1, sy + dy - 1, 2, 2))

        elif ch == 8:
            if lvl == 80:
                # Level 80 Surface Breach Finale: multi-stage skyward aurora & extraction telemetry
                sigs = active_signals or set()
                stage_n = sum(s in sigs for s in ("west_record", "reserve_B", "evac_proof", "countdown"))
                aurora_y = 26 + (bay % 3) * 10
                for a_i in range(4):
                    ax = sx - 18 + a_i * 10 + int(round(4 * math.sin(phase * 0.7 + a_i)))
                    ah = 8 + stage_n * 4 + (a_i % 2) * 4
                    col = active_col if stage_n >= 2 else pal["edge"]
                    pygame.draw.line(surf, col, (ax, aurora_y), (ax, aurora_y + ah), 2)
            elif sub_idx in (0, 4, 6):
                # Nocturnal ridge ground-fog / katabatic wind drift above exterior stonework
                for f_i in range(2):
                    fx = sx - 16 + int((phase * 10 + f_i * 19) % 32)
                    fy = sy + f_i * 8
                    pygame.draw.line(surf, pal["mid"], (fx, fy), (fx + 14, fy), 2)
            else:
                # Exterior perimeter comms mast strobe & moon-dust motes
                pygame.draw.line(surf, pal["mid"], (sx, sy - 16), (sx, sy + 12), 2)
                on = (int(phase * 2) % 2 == 0) or reduced_motion
                pygame.draw.rect(surf, warn_col if on else pal["edge"], (sx - 1, sy - 18, 3, 3))
