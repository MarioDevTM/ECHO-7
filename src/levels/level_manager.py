import math
import random
import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLORS, CHAPTER_THEMES, AUXILIARY_ROOMS
from src.core.camera import Camera
from src.visuals.scene_renderer import SceneRenderer
from src.entities.player import Player
from src.entities.crate import Crate
from src.entities.moving_platform import MovingPlatform
from src.puzzles.hints import next_hint
from src.puzzles.routing import LatchingRelay, RoutingConsole
from src.entities.npc import FacilityNPC
from src.ui.text_layout import wrap_text, paginate, draw_lines, draw_fitted
from src.ui import components as ui
from src.puzzles.pressure_plate import PressurePlate
from src.puzzles.switch import Switch
from src.puzzles.door import Door
from src.puzzles.puzzle_manager import (
    PuzzleManager,
    OpticalBeam,
    Generator,
    Valve,
    PowerCable,
    RotatableMirror,
    ConveyorBelt,
    WindZone,
    WaterZone,
    CollapsingPlatform,
)
from src.systems.collision import CollisionSystem
from src.systems.precision import PrecisionWorld
from src.systems.checkpoint import Checkpoint, CheckpointManager
from src.systems.hazards import (
    SpikeHazard,
    AcidHazard,
    LaserHazard,
    CrusherHazard,
    SteamVentHazard,
    HazardManager,
)


class LevelManager:
    """Coordinates entities, puzzles, hazards, checkpoints, collectibles, and chapter themes."""

    def __init__(self, level_loader, save_manager, audio) -> None:
        self.level_loader = level_loader
        self.save_manager = save_manager
        self.audio = audio

        self.current_level_num = 1
        self.level_name = ""
        self.level_subtitle = ""
        self.theme_name = "awakening"
        self.width = VIRTUAL_WIDTH
        self.height = VIRTUAL_HEIGHT

        self.tiles: list[pygame.Rect] = []
        self.ladders: list[pygame.Rect] = []
        self.crates: list[Crate] = []
        self.moving_platforms: list[MovingPlatform] = []
        self.collectibles: list[dict] = []
        self.decorations: list[dict] = []
        self.player = Player(100, 100)
        self.exit_rect = pygame.Rect(0, 0, 44, 68)

        self.camera = Camera(self.width, self.height)
        self.scenery = SceneRenderer()
        self.puzzle_manager = PuzzleManager(audio)
        self.checkpoint_manager = CheckpointManager((100.0, 100.0), audio)
        self.hazard_manager = HazardManager(self.height)
        self.precision = PrecisionWorld({})
        self.precision_at_checkpoint = self.precision.snapshot()

        self.death_timer = 0.0
        self.death_particles: list[list[float]] = []
        self.ambient_particles: list[list[float]] = []
        self.portal_timer = 0.0
        self.log_banner_timer = 0.0
        self.log_banner_text = ""

        self.font_hud = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 17)
        self.font_dialogue = pygame.font.SysFont("consolas", 21)
        self.font_title_dialogue = pygame.font.SysFont("consolas", 20, bold=True)
        self.labels = {}

    def load_level(self, level_num: int) -> None:
        data = self.level_loader.load_level_data(level_num)
        self.labels.clear()
        self.hint_route = data.get("hint_route", [])
        self.hint_notes = data.get("hint_notes", {})
        self.hint_link, self.hint_depth = None, 0
        self.pending_events = []
        self.physics_time = 0.0
        chapter = data.get("chapter", (level_num - 1) // 10 + 1)
        if self.audio:
            if level_num == 80 and hasattr(self.audio, "start_level_80_finale_ascent"):
                self.audio.start_level_80_finale_ascent()
            elif self.audio.current_chapter_track != chapter or self.audio.in_finale:
                self.audio.start_ambient(chapter)
        self.respawn_grace = 0.0
        self.hazards_at_checkpoint = []
        self.current_level_num = level_num
        self.level_name = data.get("name", f"Chamber {level_num:02d}")
        self.level_subtitle = data.get("subtitle", "")
        self.theme_name = data.get("theme", "awakening")
        self.width = int(data.get("width", 2400))
        self.height = int(data.get("height", 720))

        spawn = data.get("spawn", [100, 500])
        self.player = Player(spawn[0], spawn[1])
        abilities = data.get('abilities', {})
        self.player.can_wall_jump = bool(abilities.get('wall_jump', False))
        self.player.can_dash = bool(abilities.get('dash', False))
        self.precision = PrecisionWorld(data)
        self.precision_at_checkpoint = self.precision.snapshot()
        # Only real terrain supports wall jumping, never locked machinery doors.
        self.player.wall_surfaces = []  # assigned once level tiles are loaded

        exit_pos = data.get("exit", [2200, 500])
        self.exit_rect = pygame.Rect(exit_pos[0], exit_pos[1], 48, 80)

        self.tiles = [pygame.Rect(*t) for t in data.get("tiles", [])]
        self.scenery.set_level_tiles(self.tiles)
        self.player.wall_surfaces = self.tiles
        self.ladders = [
            pygame.Rect(l["x"], l["y"], 28, l["h"]) for l in data.get("ladders", [])
        ]
        self.crates = [
            Crate(c["id"], c["x"], c["y"], c.get("mass", 1.0), c.get("buoyant", True)) for c in data.get("crates", [])
        ]
        self.moving_platforms = [
            MovingPlatform(
                mp["id"],
                mp["x"],
                mp["y"],
                mp["w"],
                mp["h"],
                mp["end_x"],
                mp["end_y"],
                mp.get("speed", 100.0),
                mp.get("required_links", []),
                mp.get("logic", "ALL"),
                mp.get("active_by_default", True),
            )
            for mp in data.get("moving_platforms", [])
        ]

        self.puzzle_manager = PuzzleManager(self.audio)
        for p in data.get("plates", []):
            self.puzzle_manager.add_plate(
                PressurePlate(p["link_id"], p["x"], p["y"])
            )
        for sw in data.get("switches", []):
            self.puzzle_manager.add_switch(
                Switch(
                    sw["link_id"],
                    sw["x"],
                    sw["y"],
                    sw.get("mode", "toggle"),
                    sw.get("duration", 0.0),
                )
            )
        for relay in data.get("latching_relays", []):
            self.puzzle_manager.latching_relays.append(LatchingRelay(
                relay["link_id"], relay["x"], relay["y"], relay["required_links"]))
        for panel in data.get("routing_consoles", []):
            self.puzzle_manager.routing_consoles.append(RoutingConsole(
                panel["id"], panel["route_id"], panel["x"], panel["y"],
                panel["a_signal"], panel["b_signal"], panel.get("required_links", [])))
            self.puzzle_manager.route_modes.setdefault(panel["route_id"], 0)
        self.puzzle_manager.signal_inverters = {
            inv["link_id"]: (inv["input"], inv.get("water_zone"))
            for inv in data.get("signal_inverters", [])}
        for gen in data.get("generators", []):
            self.puzzle_manager.generators.append(
                Generator(gen["link_id"], gen["x"], gen["y"], gen.get("duration", 0.0))
            )
        for v in data.get("valves", []):
            self.puzzle_manager.valves.append(
                Valve(v["link_id"], v["x"], v["y"])
            )
        for cb in data.get("cables", []):
            self.puzzle_manager.cables.append(
                PowerCable(cb["points"], cb["link_id"])
            )
        for mr in data.get("mirrors", []):
            self.puzzle_manager.mirrors.append(
                RotatableMirror(mr["id"], mr["x"], mr["y"], mr.get("orientation", 0))
            )
        for conv in data.get("conveyors", []):
            self.puzzle_manager.conveyors.append(
                ConveyorBelt(
                    conv["id"],
                    conv["x"],
                    conv["y"],
                    conv["w"],
                    conv["h"],
                    conv["speed"],
                    conv.get("reversed_by"),
                    conv.get("powered_by"),
                )
            )
        for wz in data.get("wind_zones", []):
            self.puzzle_manager.wind_zones.append(
                WindZone(
                    wz["id"],
                    wz["x"],
                    wz["y"],
                    wz["w"],
                    wz["h"],
                    wz.get("vx", 0.0),
                    wz.get("vy", 0.0),
                    wz.get("controlled_by"),
                    wz.get("active_by_default", True),
                )
            )
        for water in data.get("water_zones", []):
            self.puzzle_manager.water_zones.append(
                WaterZone(
                    water["id"],
                    water["x"],
                    water["y"],
                    water["w"],
                    water["h"],
                    water["drained_y"],
                    water.get("controlled_by"),
                    water.get("toxic", False),
                )
            )
        for cp_plat in data.get("collapsing_platforms", []):
            self.puzzle_manager.collapsing_platforms.append(
                CollapsingPlatform(
                    cp_plat["id"],
                    cp_plat["x"],
                    cp_plat["y"],
                    cp_plat["w"],
                    cp_plat["h"],
                    cp_plat.get("delay", 0.45),
                    cp_plat.get("respawn", 2.5),
                )
            )
        for d in data.get("doors", []):
            self.puzzle_manager.add_door(
                Door(
                    d["id"],
                    d["x"],
                    d["y"],
                    d["w"],
                    d["h"],
                    d.get("required_links", []),
                    d.get("logic", "ALL"),
                    d.get("inverted", False),
                )
            )
        # The final exit gate is authoritative, even if the player discovers a
        # geometry shortcut around it. Auxiliary doors keep their own state.
        explicit_gate = data.get("exit_gate_id")
        exit_gates = [d for d in self.puzzle_manager.doors
                      if d.door_id == explicit_gate] if explicit_gate else []
        if not exit_gates:
            exit_gates = [d for d in self.puzzle_manager.doors
                          if ("exit" in d.door_id or "surface_lock" in d.door_id
                              or "moon_gate" in d.door_id)]
        self.exit_gate = (exit_gates[-1] if exit_gates else
                          self.puzzle_manager.doors[-1] if self.puzzle_manager.doors else None)
        for ob in data.get("optical_beams", []):
            self.puzzle_manager.add_optical_beam(
                OpticalBeam(
                    ob["link_id"],
                    ob["x"],
                    ob["y"],
                    tuple(ob["dir"]),
                    ob["max_length"],
                    pygame.Rect(*ob["receiver"]),
                    ob.get("enabled_by"),
                )
            )
        self.puzzle_manager.order_optical_beams()
        for seq in data.get("sequences", []):
            self.puzzle_manager.timer_mech.register_sequence(
                seq["group_id"], seq["order"]
            )

        self.checkpoint_manager = CheckpointManager(
            (float(spawn[0]), float(spawn[1])), self.audio
        )
        for cp in data.get("checkpoints", []):
            self.checkpoint_manager.add_checkpoint(
                Checkpoint(cp["id"], cp["x"], cp["y"])
            )
        self.checkpoint_manager.save_snapshot(
            self.crates, self.moving_platforms, self.puzzle_manager,
            self.puzzle_manager.collapsing_platforms,
        )

        self.hazard_manager = HazardManager(self.height)
        for sp in data.get("spikes", []):
            self.hazard_manager.spikes.append(
                SpikeHazard(
                    sp["x"],
                    sp["y"],
                    sp["w"],
                    sp["h"],
                    sp.get("orientation", "up"),
                )
            )
        for ac in data.get("acids", []):
            self.hazard_manager.acids.append(
                AcidHazard(ac["x"], ac["y"], ac["w"], ac["h"])
            )
        for ls in data.get("lasers", []):
            self.hazard_manager.lasers.append(
                LaserHazard(
                    ls["x"],
                    ls["y"],
                    tuple(ls["dir"]),
                    ls["max_length"],
                    ls.get("disabled_by", []),
                    ls.get("logic", "ANY"),
                    ls.get("period", 0.0),
                    ls.get("duty_cycle", 0.55),
                )
            )
        for cr in data.get("crushers", []):
            self.hazard_manager.crushers.append(
                CrusherHazard(
                    cr["id"],
                    cr["x"],
                    cr["y"],
                    cr["w"],
                    cr["h"],
                    cr["travel"],
                    cr.get("period", 2.2),
                    cr.get("disabled_by", []),
                )
            )
        for sv in data.get("steam_vents", []):
            self.hazard_manager.steam_vents.append(
                SteamVentHazard(
                    sv["id"],
                    sv["x"],
                    sv["y"],
                    sv["w"],
                    sv["h"],
                    sv.get("period", 2.4),
                    sv.get("duty_cycle", 0.5),
                    sv.get("disabled_by", []),
                )
            )

        self.cycling_hazards = (self.hazard_manager.lasers + self.hazard_manager.crushers
                               + self.hazard_manager.steam_vents)
        self.hazards_at_checkpoint = [(h, h.timer) for h in self.cycling_hazards]

        already_collected = set(self.save_manager.data.get("collected_logs", []))
        self.collectibles = []
        for col in data.get("collectibles", []):
            self.collectibles.append(
                {
                    "id": col["id"],
                    "rect": pygame.Rect(col["x"], col["y"], 24, 28),
                    "title": col.get("title", "Research Log"),
                    "text": col.get("text", ""),
                    "collected": col["id"] in already_collected,
                    "required_links": tuple(col.get("required_links", [])),
                    "optional_investigation": bool(col.get("optional_investigation", False)),
                }
            )
        self.decorations = list(data.get("decorations", []))
        self.npcs = [FacilityNPC(**npc) for npc in data.get("npcs", [])]
        self.dialogue_text = ""
        self.dialogue_timer = 0.0
        self.dialogue_active = False
        self.dialogue_page = 0
        self.dialogue_pages = []
        self.npc_stages = {}
        self.log_banner_elapsed = 0.0

        # World-space scenery is seeded by level identity, never by player spawn.
        self.scenery.set_level_context(level_num)
        self.scenery.set_level_focus(int(spawn[0]), int(spawn[1]))
        self.camera.resize_bounds(self.width, self.height)
        self.camera.snap_to(self.player.rect.centerx, self.player.rect.centery)
        self.death_timer = 0.0
        self.log_banner_timer = 0.0
        self.death_particles.clear()

        self.ambient_particles = [
            [
                random.uniform(0, self.width),
                random.uniform(0, self.height),
                random.uniform(-12, 12),
                random.uniform(-22, -8),
                random.uniform(1.5, 3.2),
            ]
            for _ in range(45)
        ]

    def exit_is_ready(self) -> bool:
        """A level cannot finish while its final puzzle bulkhead is sealed."""
        gate = getattr(self, "exit_gate", None)
        if gate is None:
            return True
        return bool(gate.is_open and not gate.is_solid)

    def trigger_manual_restart(self) -> None:
        if self.death_timer <= 0.0:
            self._kill_player()

    def _kill_player(self) -> None:
        if not self.player.alive:
            return
        self.player.alive = False
        self.player.death_anim_clock = 0.0
        self.death_timer = 0.27  # Short retries; solved checkpoint states are preserved.
        if self.save_manager.data["settings"].get("camera_shake", True):
            self.camera.add_shake(0.22, 6.0)
        if self.audio:
            self.audio.play("death")
        cx, cy = self.player.rect.center
        self.death_particles = [
            [
                float(cx),
                float(cy),
                math.cos(i * 0.4) * random.uniform(60, 190),
                math.sin(i * 0.4) * random.uniform(60, 190),
                random.uniform(3.0, 6.0),
            ]
            for i in range(18)
        ]

    def _talk_to_nearby_npc(self) -> bool:
        flags = set(self.save_manager.data.get("story_flags", []))
        for npc in self.npcs:
            if not npc.interact_rect.colliderect(self.player.rect):
                continue
            if npc.npc_id == "kip":
                key = f"kip_room_{self.current_level_num}"
                stage = self.npc_stages.get(npc.npc_id, 1 if key in flags else 0)
                if not self.save_manager.data["settings"].get("hints", True):
                    # KIP never escalates to solution clues with hints disabled.
                    # On revisits, do not repeat his initial introduction.
                    if key in flags:
                        self.dialogue_text = ("KIP: Spoiler-free maintenance mode. "
                                              "My hints are switched off, but my sarcasm is fully powered.")
                        flag = None
                    else:
                        self.dialogue_text, flag = npc.speak(flags, self.current_level_num, 0)
                else:
                    self.npc_stages[npc.npc_id] = min(stage + 1, 2)
                    self.dialogue_text, flag = npc.speak(flags, self.current_level_num, stage)
            else:
                self.dialogue_text, flag = npc.speak(flags)
            if flag and flag not in flags:
                self.save_manager.data.setdefault("story_flags", []).append(flag)
                self.save_manager.save()
            # Dialogue pauses platforming and hazards; pressing E/Space advances
            # pages rather than interacting with any nearby machinery.
            self.dialogue_pages = paginate(wrap_text(
                    self.dialogue_text.partition(":")[2].strip() or self.dialogue_text,
                    self.font_dialogue, 930), 3)
            self.dialogue_page = 0
            self.dialogue_active = True
            self.dialogue_timer = 0.0
            self.player.interact_flash = 0.20
            return True
        return False

    def _close_dialogue(self) -> None:
        self.dialogue_active = False
        self.dialogue_page = 0
        self.dialogue_pages = []

    def _update_story_events(self):
        flags = self.save_manager.data.setdefault("story_flags", [])
        if self.current_level_num == 3 and (
            "relay_3_staged" in self.puzzle_manager.active_signals
            and "plate_assembly" in self.puzzle_manager.active_signals
            and any(plate.link_id == "plate_assembly" and
                    any(plate.sensor_rect.colliderect(crate.rect) for crate in self.crates)
                    for plate in self.puzzle_manager.plates)
            and "freight_twice" not in flags
        ):
            flags.append("freight_twice")
            self.save_manager.save()

    def update(self, dt: float, events: list[pygame.event.Event]) -> str:
        self.pending_events.extend(e for e in events if e.type in (pygame.KEYDOWN, pygame.KEYUP))
        self.physics_time += min(dt, 0.1)
        step = 1 / 120
        while self.physics_time + 1e-10 >= step:
            self.physics_time -= step
            edges, self.pending_events = self.pending_events, []
            status = self._tick(step, edges)
            if status != "PLAYING":
                return status
        return "PLAYING"

    def _tick(self, dt, events):
        # Camera shake is independent of look-ahead, smoothing and focus panning.
        self.camera.shake_enabled = self.save_manager.data["settings"].get("camera_shake", True)
        self.camera.focus_enabled = not self.save_manager.data["settings"].get("reduced_motion", False)
        self.camera.look_ahead_enabled = True
        self.portal_timer += dt * 3.5
        if self.log_banner_timer > 0.0:
            self.log_banner_timer = max(0.0, self.log_banner_timer - dt)
        self.dialogue_timer = max(0.0, self.dialogue_timer - dt)
        if self.log_banner_timer > 0.0:
            self.log_banner_elapsed += dt

        for p in self.ambient_particles:
            p[0] = (p[0] + p[2] * dt) % self.width
            p[1] = (p[1] + p[3] * dt) % self.height

        if not self.player.alive:
            self.player.death_anim_clock += dt
            self.death_timer -= dt
            for dp in self.death_particles:
                dp[0] += dp[2] * dt
                dp[1] += dp[3] * dt
                dp[4] = max(0.0, dp[4] - dt * 6.0)
            self.camera.update(self.player.rect, 0.0, dt)
            if self.death_timer <= 0.0:
                self.player.alive = True
                self.player.respawn_visual_timer = 0.32
                self.checkpoint_manager.restore_snapshot(
                    self.player,
                    self.crates,
                    self.moving_platforms,
                    self.puzzle_manager,
                    self.puzzle_manager.collapsing_platforms,
                )
                self.precision.restore(self.precision_at_checkpoint)
                for hazard, saved_time in self.hazards_at_checkpoint:
                    hazard.timer = saved_time
                self.respawn_grace = 0.45
                self.camera.snap_to(*self.player.rect.center)
            return "PLAYING"

        self.respawn_grace = max(0, self.respawn_grace - dt)
        keybinds = self.save_manager.get_keybinds()
        if self.dialogue_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,):
                        self._close_dialogue()
                    elif event.key in (*keybinds["interact"], pygame.K_SPACE,
                                       pygame.K_RETURN):
                        if self.dialogue_page + 1 < len(self.dialogue_pages):
                            self.dialogue_page += 1
                        else:
                            self._close_dialogue()
            # Pausing world updates also prevents an NPC chat from allowing
            # a timed gate or a hazard to complete its cycle off-screen.
            return "PLAYING"
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h and self.save_manager.data["settings"].get("hints", True):
                    self.hint_link, self.hint_depth, self.log_banner_text = next_hint(
                        self.puzzle_manager, self.hint_route, self.player.rect,
                        self.hint_link, self.hint_depth, self.hint_notes)
                    self.log_banner_timer = 7.0
                    self.log_banner_elapsed = 0.0
                elif event.key in keybinds.get('dash', [pygame.K_x]):
                    keys = pygame.key.get_pressed()
                    horizontal = (int(any(keys[k] for k in keybinds['right'])) -
                                  int(any(keys[k] for k in keybinds['left'])))
                    vertical = (int(any(keys[k] for k in keybinds.get('down', []))) -
                                int(any(keys[k] for k in keybinds.get('up', []))))
                    if self.player.begin_dash(horizontal, vertical) and self.audio:
                        self.audio.play('dash')
                elif event.key in keybinds["jump"]:
                    keys = pygame.key.get_pressed()
                    dropping = any(keys[k] for k in keybinds.get('down', []))
                    if not (dropping and self.player.try_drop_through(self.precision.one_ways)):
                        self.player.queue_jump()
                elif event.key in keybinds["interact"]:
                    # Machinery wins priority; NPCs never steal a nearby switch press.
                    if self.puzzle_manager.nearby_interactable is not None:
                        if self.puzzle_manager.try_interact(self.player.rect):
                            self.player.interact_flash = 0.24
                    elif not self._talk_to_nearby_npc():
                        if self.puzzle_manager.try_interact(self.player.rect):
                            self.player.interact_flash = 0.24
            elif event.type == pygame.KEYUP:
                if event.key in keybinds["jump"]:
                    self.player.release_jump()


        was_receiving = any(b.receiving for b in self.puzzle_manager.optical_beams)
        # Update puzzles & environmental zones first so conveyors/wind/water apply to player
        self.puzzle_manager.update(
            dt,
            self.player.rect,
            self.crates,
            self.tiles,
            self.moving_platforms,
            player=self.player,
        )

        if not was_receiving:
            for beam in self.puzzle_manager.optical_beams:
                if beam.receiving and abs(beam.receiver_rect.centerx - self.player.rect.centerx) < VIRTUAL_WIDTH * 0.4:
                    self.camera.trigger_focus(*beam.receiver_rect.center, duration=0.28)
                    break
        for mp in self.moving_platforms:
            mp.update(dt)

        static_and_door_solids = (
            self.tiles + self.puzzle_manager.get_solid_door_rects()
            + self.precision.solid_barriers()
        )
        all_world_solids = static_and_door_solids + [
            mp.rect for mp in self.moving_platforms
        ]

        # 3. Carry player and crates on moving platforms
        CollisionSystem.apply_platform_carry(
            [self.player] + self.crates,
            self.moving_platforms,
            static_and_door_solids,
        )

        # 4. Update player velocity & resolve player/crate collisions
        keys = pygame.key.get_pressed()
        jumped = self.player.update_timers_and_input(
            dt, keys, keybinds, ladders=self.ladders, solids=all_world_solids + [c.rect for c in self.crates]
        )
        if jumped and self.audio:
            self.audio.play("jump")

        # Dash impacts can fracture authored panels, never terrain or locked doors.
        if self.precision.break_with_dash(self.player, dt,
                self.tiles + self.puzzle_manager.get_solid_door_rects()):
            if self.audio:
                self.audio.play('dash_break')
            static_and_door_solids = (self.tiles + self.puzzle_manager.get_solid_door_rects()
                                      + self.precision.solid_barriers())
            all_world_solids = static_and_door_solids + [mp.rect for mp in self.moving_platforms]

        landed, impact_vy = CollisionSystem.move_and_collide_player(
            self.player, dt, all_world_solids, self.crates,
            [] if self.player.drop_through_timer > 0 else self.precision.one_ways
        )
        self.player.after_collision(self.player.wall_surfaces)
        for cue in self.precision.tick(dt, self.player, landed, impact_vy):
            if self.audio:
                self.audio.play(cue)
        if landed and impact_vy > 200.0 and self.audio:
            self.audio.play("land")

        # 5. Update crates gravity & collisions
        for crate in self.crates:
            crate.apply_gravity_and_friction(dt)
            CollisionSystem.move_and_collide_crate(
                crate, dt, all_world_solids + [self.player.rect], self.crates
            )

        # 6. Check collectible research logs
        for col in self.collectibles:
            if (not col["collected"] and col["rect"].colliderect(self.player.rect)
                    and all(link in self.puzzle_manager.active_signals
                            for link in col.get("required_links", ()))):
                col["collected"] = True
                self.save_manager.mark_log_collected(col["id"])
                self.log_banner_text = f"{col['title']}: {col['text']}"
                self.log_banner_timer = 10.5
                self.log_banner_elapsed = 0.0
                if self.audio:
                    self.audio.play("collect")

        # 7. Update hazards & check death conditions
        solids_and_crates = all_world_solids + [c.rect for c in self.crates]
        self.hazard_manager.update(
            dt, solids_and_crates, self.puzzle_manager.active_signals
        )

        if self.respawn_grace == 0 and (
            self.hazard_manager.is_player_killed(self.player.rect)
            or CollisionSystem.is_crushed(self.player.rect, all_world_solids)
        ):
            self._kill_player()
            return "PLAYING"

        self._update_story_events()
        if self.audio:
            finale_stage = 0
            if self.current_level_num == 80:
                finale_stage = sum(
                    signal in self.puzzle_manager.active_signals
                    for signal in ("west_record", "reserve_B", "evac_proof", "countdown")
                )
            self.audio.update_music_state(
                dt,
                any(g.active for g in self.puzzle_manager.generators)
                or any(r.latched for r in self.puzzle_manager.latching_relays),
                finale_stage=finale_stage,
            )

        # 8. Update checkpoints
        activated = self.checkpoint_manager.update(
            dt,
            self.player.rect,
            self.crates,
            self.moving_platforms,
            self.puzzle_manager,
            self.puzzle_manager.collapsing_platforms,
            unsafe_spawn=lambda box: box.collidelist(solids_and_crates) >= 0
                or self.hazard_manager.is_player_killed(box),
        )
        if activated:
            self.hazards_at_checkpoint = [(h, h.timer) for h in self.cycling_hazards]
            self.precision_at_checkpoint = self.precision.snapshot()

        # 9. Check level exit portal
        if self.exit_rect.colliderect(self.player.rect) and self.exit_is_ready():
            if self.audio:
                self.audio.play("level_clear")
            if self.current_level_num in AUXILIARY_ROOMS:
                self.save_manager.mark_auxiliary_completed(self.current_level_num)
                return "AUXILIARY_COMPLETED"
            self.save_manager.mark_level_completed(self.current_level_num)
            if self.current_level_num < self.save_manager.TOTAL_LEVELS:
                self.load_level(self.current_level_num + 1)
                return "NEXT_LEVEL"
            return "GAME_COMPLETED"

        self.camera.update(self.player.rect, self.player.vx, dt)
        return "PLAYING"

    def draw(self, surface: pygame.Surface) -> None:
        theme = CHAPTER_THEMES.get(self.theme_name, CHAPTER_THEMES["awakening"])
        surface.fill(theme["bg_deep"])
        ox, oy = self.camera.get_offset()
        self.scenery._reduced_motion = bool(self.save_manager.data["settings"].get("reduced_motion", False))
        circuit_powered = any(g.active for g in self.puzzle_manager.generators) or any(
            relay.latched for relay in self.puzzle_manager.latching_relays)
        self.scenery.pixel_environment.set_active_signals(self.puzzle_manager.active_signals)
        self.scenery.draw_background(surface, self.theme_name, ox, oy, self.portal_timer,
                                     self.width, self.height, powered=circuit_powered,
                                     signals=self.puzzle_manager.active_signals)
        self.scenery.draw_room_scenery(surface, self.camera, self)
        self._draw_decorations(surface)

        # Ambient dust particles
        for p in self.ambient_particles:
            px, py = self.camera.apply_point((p[0], p[1]))
            if 0 <= px <= VIRTUAL_WIDTH and 0 <= py <= VIRTUAL_HEIGHT:
                pygame.draw.circle(surface, theme["tile_border"], (px, py), int(p[4]))

        for tile in self.tiles:
            tr = self.camera.apply(tile)
            if tr.colliderect(surface.get_rect()):
                self.scenery.draw_platform(surface, tr, self.theme_name, (ox, oy), world_rect=tile)

        # Ladders
        for lad in self.ladders:
            lr = self.camera.apply(lad)
            pygame.draw.line(surface, theme["tile_border"], (lr.left + 4, lr.top), (lr.left + 4, lr.bottom), 3)
            pygame.draw.line(surface, theme["tile_border"], (lr.right - 4, lr.top), (lr.right - 4, lr.bottom), 3)
            for ry in range(lr.top + 8, lr.bottom, 16):
                pygame.draw.line(surface, COLORS["ui_muted"], (lr.left + 4, ry), (lr.right - 4, ry), 2)

        # Exit Portal
        er = self.camera.apply(self.exit_rect)
        self.scenery.draw_exit(surface, er, self.theme_name, self.portal_timer,
                               locked=not self.exit_is_ready())

        # Collectibles
        for col in self.collectibles:
            if not col["collected"]:
                cr = self.camera.apply(col["rect"])
                required = col.get("required_links", ())
                unlocked = all(link in self.puzzle_manager.active_signals for link in required)
                if col.get("optional_investigation"):
                    pygame.draw.rect(surface, (18, 30, 45), cr, border_radius=4)
                    rim = (241, 175, 91) if unlocked else (93, 118, 140)
                    pygame.draw.rect(surface, rim, cr, width=2, border_radius=4)
                    pygame.draw.line(surface, rim, (cr.left+6,cr.centery), (cr.right-6,cr.centery), 2)
                    if not unlocked:
                        pygame.draw.circle(surface,rim,cr.center,4,1)
                else:
                    pygame.draw.rect(surface, COLORS["ui_panel"], cr, border_radius=4)
                    pygame.draw.rect(surface, COLORS["ui_accent"], cr, width=2, border_radius=4)

        # Checkpoints, Puzzles, Platforms, Hazards, Crates, Tiles, Player
        self.checkpoint_manager.draw(surface, self.camera)
        self.puzzle_manager.draw(surface, self.camera, self.font_sub)

        for mp in self.moving_platforms:
            mp.draw(surface, self.camera)

        self.hazard_manager.draw(surface, self.camera)
        self.precision.draw(surface, self.camera, self.portal_timer)

        for crate in self.crates:
            crate.draw(surface, self.camera)

        self.player.draw(surface, self.camera)
        for npc in self.npcs:
            npc.draw(surface, self.camera, self.font_sub,
                     npc.interact_rect.colliderect(self.player.rect)
                     and self.puzzle_manager.nearby_interactable is None,
                     self.portal_timer)

        for dp in self.death_particles:
            if dp[4] > 0:
                px, py = self.camera.apply_point((dp[0], dp[1]))
                pygame.draw.circle(
                    surface, COLORS["player_visor"], (px, py), int(dp[4])
                )

        # HUD: measured text fitting on a higher-contrast panel. Subtitle may
        # occupy two lines; the hint prompt has a dedicated right-hand space.
        # Smaller HUD keeps upper traversal lanes readable; full hints remain
        # available via [H] and the game's existing terminal/story interface.
        hud_panel = pygame.Rect(16, 14, 738, 67)
        ui.panel(surface, hud_panel)
        ch_num = (self.current_level_num - 1) // 10 + 1
        draw_fitted(surface, f"SECTOR {ch_num:02d}  //  {self.level_name}",
                    pygame.Rect(29, 20, 615, 27), COLORS["ui_accent"],
                    size=19, min_size=13, bold=True, align="left")
        draw_fitted(surface, self.level_subtitle,
                    pygame.Rect(29, 50, 615, 21), COLORS["ui_text"],
                    size=13, min_size=11, align="left")
        if self.hint_route and self.save_manager.data["settings"].get("hints", True):
            draw_fitted(surface, "[H] HINT", pygame.Rect(647, 28, 94, 26),
                        COLORS["ui_accent"], size=14, min_size=12, bold=True)

        if self.puzzle_manager.doors and not self.puzzle_manager.timer_mech.timers:
            gate = self.puzzle_manager.doors[-1]
            needed = list(getattr(gate, "required_links", []))
            if needed:
                live = sum(link in self.puzzle_manager.active_signals for link in needed)
                info = pygame.Rect(953,14,307,54)
                ui.panel(surface,info)
                draw_fitted(surface,f"EXIT CIRCUIT     {live} / {len(needed)} READY",
                            info.inflate(-12,-10),ui.CYAN if live == len(needed) else ui.MUTED,
                            size=16,min_size=12,bold=True)

        if self.player.can_wall_jump or self.player.can_dash:
            abilities_label = ('WALL: CONTACT + SPACE' if self.player.can_wall_jump else '')
            if self.player.can_dash:
                state = 'READY' if self.player.dash_charges else 'EMPTY'
                abilities_label = f"[X] DASH {state}" + ('  //  ' + abilities_label if abilities_label else '')
            panel = pygame.Rect(953, 83, 307, 39)
            ui.panel(surface, panel)
            draw_fitted(surface, abilities_label, panel.inflate(-12, -9),
                        COLORS['ui_text'], size=15, min_size=11)

        timers = self.puzzle_manager.timer_mech.timers
        if timers:
            link, (remaining, total) = min(timers.items(), key=lambda item: item[1][0])
            is_reserve = any(g.link_id == link for g in self.puzzle_manager.generators)
            caption = "Reserve" if is_reserve else "Relay"
            panel = pygame.Rect(VIRTUAL_WIDTH - 232, 14, 214, 56)
            ui.panel(surface, panel)
            draw_fitted(surface, f"{caption}  {remaining:.1f} s",
                        panel.inflate(-24, -24), COLORS["ui_text"], size=18)
            bar = pygame.Rect(panel.x + 12, panel.bottom - 14, panel.w - 24, 4)
            pygame.draw.rect(surface, COLORS["tile_border"], bar)
            bar.width = round(bar.width * max(0, remaining) / max(0.001, total))
            pygame.draw.rect(surface, COLORS["ui_warning"], bar)

        if self.dialogue_active and self.dialogue_pages:
            panel = pygame.Rect(130, 510, VIRTUAL_WIDTH - 260, 184)
            ui.panel(surface, panel, accented=True)
            speaker = self.dialogue_text.partition(":")[0].strip() or "FACILITY"
            draw_fitted(surface, f"{speaker} // FACILITY GUIDE" if speaker == "KIP" else speaker,
                        pygame.Rect(panel.x + 23, panel.y + 13, 760, 27),
                        COLORS["ui_accent"], size=20, min_size=16,
                        bold=True, align="left")
            draw_lines(surface, self.font_dialogue,
                       self.dialogue_pages[self.dialogue_page],
                       pygame.Rect(panel.x + 23, panel.y + 47, panel.w - 46, 107),
                       COLORS["ui_text"], line_gap=4)
            instructions = f"[E/SPACE] {'NEXT' if self.dialogue_page + 1 < len(self.dialogue_pages) else 'CLOSE'}   [ESC] SKIP"
            if len(self.dialogue_pages) > 1:
                instructions += f"   {self.dialogue_page + 1}/{len(self.dialogue_pages)}"
            draw_fitted(surface, instructions,
                        pygame.Rect(panel.x + 560, panel.bottom - 30, 430, 22),
                        COLORS["ui_muted"], size=15, min_size=12, align="right")

        # Contextual hints and research logs: paginate rather than draw a long
        # single-line bitmap outside its bounds. Hide while dialogue is open.
        if self.log_banner_timer > 0.0 and not self.dialogue_active:
            log_panel = pygame.Rect(135, 600, VIRTUAL_WIDTH - 270, 105)
            ui.panel(surface, log_panel, accented=True)
            pages = paginate(wrap_text(self.log_banner_text, self.font_sub,
                                       log_panel.width - 44), 3)
            page_index = min(len(pages) - 1, int(self.log_banner_elapsed // 3.0))
            draw_lines(surface, self.font_sub, pages[page_index],
                       pygame.Rect(log_panel.x + 22, log_panel.y + 12,
                                   log_panel.w - 44, 70), COLORS["ui_text"])
            if len(pages) > 1:
                draw_fitted(surface, f"MESSAGE {page_index + 1}/{len(pages)}",
                            pygame.Rect(log_panel.right - 172, log_panel.bottom - 25, 150, 18),
                            COLORS["ui_accent"], size=14, min_size=11, align="right")

    def label(self, text, title=False):
        key = (text, title)
        if key not in self.labels:
            font = self.font_hud if title else self.font_sub
            color = COLORS["ui_accent"] if title else COLORS["ui_text"]
            self.labels[key] = font.render(text, True, color)
        return self.labels[key]

    def _draw_parallax(self, surface: pygame.Surface, theme: dict) -> None:
        ox, _ = self.camera.get_offset()
        pillar_spacing = 320
        start_i = int((ox * 0.25) // pillar_spacing)
        for i in range(start_i, start_i + 6):
            px = int(i * pillar_spacing - (ox * 0.25))
            pygame.draw.rect(
                surface, theme["bg_mid"], (px, 0, 68, VIRTUAL_HEIGHT)
            )
        # Ceiling service rail and lamps switch from standby to power with the room.
        powered = any(gen.active for gen in self.puzzle_manager.generators)
        lamp = COLORS["switch_on"] if powered else theme["tile_border"]
        pygame.draw.line(surface, theme["bg_near"], (0, 108), (VIRTUAL_WIDTH, 108), 5)
        for x in range(-int(ox * 0.45) % 220 - 220, VIRTUAL_WIDTH, 220):
            pygame.draw.rect(surface, theme["bg_near"], (x + 45, 108, 46, 9))
            pygame.draw.line(surface, lamp, (x + 51, 117), (x + 84, 117), 2)
        girder_spacing = 220
        start_j = int((ox * 0.45) // girder_spacing)
        for j in range(start_j, start_j + 8):
            gx = int(j * girder_spacing - (ox * 0.45))
            pygame.draw.rect(
                surface, theme["bg_near"], (gx, 80, 26, VIRTUAL_HEIGHT - 80)
            )
            for y in (164, 366):
                pygame.draw.line(surface, theme["bg_mid"], (gx + 26, y + 64), (gx + 142, y), 5)
                pygame.draw.rect(surface, theme["bg_near"], (gx - 4, y + 56, 34, 12))
            # Recessed pipe run with couplings and alternating ventilation grilles.
            pygame.draw.line(surface, theme["bg_mid"], (gx, 286), (gx + 220, 286), 9)
            for offset in (42, 164):
                pygame.draw.rect(surface, theme["bg_near"], (gx + offset, 279, 7, 14))
            if j % 2 == 0:
                grill = pygame.Rect(gx + 58, 207, 78, 34)
                pygame.draw.rect(surface, theme["bg_mid"], grill, border_radius=3)
                for slot_y in range(grill.top + 6, grill.bottom - 3, 6):
                    pygame.draw.line(surface, theme["bg_deep"], (grill.left + 5, slot_y),
                                     (grill.right - 5, slot_y), 2)

    def _draw_decorations(self, surface: pygame.Surface) -> None:
        """Keep signage readable without concealing real puzzles or solid terrain."""
        placed_boxes: list[pygame.Rect] = []
        pm = self.puzzle_manager
        busy_world_rects = [
            *self.tiles,
            *(g.rect for g in pm.generators),
            *(v.rect for v in pm.valves),
            *(r.rect for r in pm.latching_relays),
            *(rc.rect for rc in pm.routing_consoles),
            *(sw.rect for sw in pm.switches),
            *(d.rect for d in pm.doors),
        ]
        for dec in self.decorations:
            dtype = dec.get("type")
            wx, wy = int(dec.get("x", 0)), int(dec.get("y", 0))
            dx, dy = self.camera.apply_point((wx, wy))
            if dtype in ("monitor", "sign_arrow"):
                initial = pygame.Rect(wx, wy, 108, 28)
                free = None
                for shift_y in (0, -32, 32, -56):
                    candidate = initial.move(0, shift_y)
                    if not any(candidate.colliderect(r) for r in busy_world_rects):
                        free = candidate
                        break
                if free is None:
                    continue  # don't draw sign through the terrain or a device
                box = self.camera.apply(free)
                if any(box.colliderect(prev.inflate(6, 6)) for prev in placed_boxes):
                    continue
                placed_boxes.append(box)
                pygame.draw.rect(surface, (6, 15, 30), box.inflate(2, 2), border_radius=3)
                pygame.draw.rect(surface, COLORS["ui_bg"], box, border_radius=3)
                pygame.draw.rect(surface, COLORS["ui_accent"] if dtype == "monitor" else COLORS["tile_border"],
                                 box, width=1, border_radius=3)
                pygame.draw.circle(surface, COLORS["plate_active"], (box.left + 5, box.top + 5), 2)
                draw_fitted(surface, dec.get("text", ""), box.inflate(-10, -4),
                            COLORS["ui_text"], size=15, min_size=10)
            elif dtype == "warning_stripe":
                w = int(dec.get("w", 100))
                pygame.draw.rect(surface, (16, 20, 28), (dx, dy, w, 7))
                for x in range(dx + 2, dx + w - 8, 16):
                    pygame.draw.line(surface, COLORS["ui_warning"], (x, dy + 5), (x + 6, dy + 1), 3)
            elif dtype == "pipe_h":
                w = int(dec.get("w", 200))
                pygame.draw.rect(surface, (6, 15, 30), (dx, dy - 1, w, 16))
                pygame.draw.rect(surface, COLORS["tile_dark"], (dx, dy, w, 14))
                pygame.draw.line(surface, COLORS["tile_border"], (dx, dy + 3), (dx + w, dy + 3), 2)
                for fx in range(dx + 60, dx + w - 20, 120):
                    pygame.draw.rect(surface, COLORS["tile_border"], (fx, dy - 2, 8, 18))
