import sys
import pygame
from src.core.settings import (
    AUXILIARY_ROOMS,
    GAME_TITLE,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    FPS,
    MAX_DT,
    COLORS,
)
from src.core.save_manager import SaveManager
from src.systems.audio import AudioManager
from src.levels.level_loader import LevelLoader, CHAPTER_METADATA
from src.levels.level_manager import LevelManager
from src.ui.main_menu import MainMenu
from src.ui.pause_menu import PauseMenu
from src.ui.settings_menu import SettingsMenu
from src.ui.text_layout import draw_fitted
from src.ui import components as ui
from src.entities.kip_dialogue import KIP_CHAPTER_MILESTONES


class Game:
    """Top-level application state machine, display scaler, and 80-level main loop."""

    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        # The player-head artwork belongs to the OS window / packaged app,
        # not any in-game menu panel or gameplay sprite.
        self._app_icon = None

        self.save_manager = SaveManager()
        self.audio = AudioManager(self.save_manager)
        self.level_loader = LevelLoader()

        self.window_size = (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.screen = self._create_display()
        self.canvas = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # States: MAIN_MENU, PLAYING, PAUSED, SETTINGS, CHAPTER_COMPLETE, VICTORY
        self.state = "MAIN_MENU"
        self.previous_state = "MAIN_MENU"
        self.completed_chapter_num = 1
        self.next_level_num = 1

        self.level_manager = LevelManager(
            self.level_loader, self.save_manager, self.audio
        )
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)

        self.font_large = pygame.font.SysFont("consolas", 42, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)

    def _create_display(self) -> pygame.Surface:
        fullscreen = self.save_manager.data["settings"].get("fullscreen", False)
        flags = pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
        display = pygame.display.set_mode(self.window_size, flags)
        # Set after opening the window so Windows/Linux window managers get
        # the real RGBA icon; reapply if the display is recreated in Settings.
        try:
            if self._app_icon is None:
                from pathlib import Path
                icon_path = Path(__file__).resolve().parents[2] / "data" / "art" / "ui" / "echo7_icon.png"
                self._app_icon = pygame.image.load(str(icon_path)).convert_alpha()
            pygame.display.set_icon(self._app_icon)
        except (pygame.error, OSError):
            pass
        return display

    def apply_display_settings(self) -> None:
        self.screen = self._create_display()
        self.window_size = self.screen.get_size()

    def window_to_virtual(self, pos: tuple[int, int]) -> tuple[int, int]:
        win_w, win_h = self.screen.get_size()
        if win_w <= 0 or win_h <= 0:
            return pos
        scale = min(win_w / VIRTUAL_WIDTH, win_h / VIRTUAL_HEIGHT)
        rendered_w = int(VIRTUAL_WIDTH * scale)
        rendered_h = int(VIRTUAL_HEIGHT * scale)
        offset_x = (win_w - rendered_w) // 2
        offset_y = (win_h - rendered_h) // 2
        # Letterbox areas are outside the actual game canvas. Returning a
        # sentinel prevents black-bar clicks from selecting edge-aligned UI.
        if not (offset_x <= pos[0] < offset_x + rendered_w and
                offset_y <= pos[1] < offset_y + rendered_h):
            return -1, -1
        vx = int((pos[0] - offset_x) / scale)
        vy = int((pos[1] - offset_y) / scale)
        return min(VIRTUAL_WIDTH - 1, vx), min(VIRTUAL_HEIGHT - 1, vy)

    def start_level(self, level_num: int) -> None:
        level_num = max(1, min(self.level_loader.TOTAL_LEVELS, int(level_num)))
        self.level_manager.load_level(level_num)
        self.save_manager.data["current_level"] = level_num
        self.save_manager.save()
        self.state = "PLAYING"

    def open_settings(self, from_state: str) -> None:
        self.previous_state = from_state
        self.state = "SETTINGS"

    def close_settings(self) -> None:
        self.state = self.previous_state

    def run(self) -> None:
        self.audio.start_ambient()
        while self.running:
            raw_dt = self.clock.tick(FPS) / 1000.0
            dt = min(raw_dt, MAX_DT)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = (event.w, event.h)

            if self.state == "MAIN_MENU":
                self.main_menu.handle_events(events)
                self.main_menu.update(dt)
                self.main_menu.draw(self.canvas)

            elif self.state == "PLAYING":
                prev_lvl = self.level_manager.current_level_num
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        keybinds = self.save_manager.get_keybinds()
                        # Escape closes KIP's dialogue instead of opening the pause menu.
                        if self.level_manager.dialogue_active:
                            continue
                        if event.key in keybinds["pause"]:
                            self.audio.play("ui_select")
                            self.state = "PAUSED"
                        elif event.key in keybinds["restart"]:
                            self.level_manager.trigger_manual_restart()
                        elif event.key in (pygame.K_PAGEDOWN, pygame.K_RIGHTBRACKET):
                            nxt = min(self.level_loader.TOTAL_LEVELS, self.level_manager.current_level_num + 1)
                            self.start_level(nxt)
                        elif event.key in (pygame.K_PAGEUP, pygame.K_LEFTBRACKET):
                            prv = max(1, self.level_manager.current_level_num - 1)
                            self.start_level(prv)

                status = self.level_manager.update(min(raw_dt, 0.1), events) if self.state == "PLAYING" else "PAUSED"
                self.level_manager.draw(self.canvas)

                if status == "NEXT_LEVEL":
                    # Show Chapter Completion screen at the end of each 10-level chapter
                    if prev_lvl % 10 == 0 and prev_lvl < self.level_loader.TOTAL_LEVELS:
                        self.completed_chapter_num = prev_lvl // 10
                        self.next_level_num = prev_lvl + 1
                        self.state = "CHAPTER_COMPLETE"
                elif status == "AUXILIARY_COMPLETED":
                    self.main_menu.mode = "AUXILIARY"
                    self.main_menu.selected_index = list(AUXILIARY_ROOMS).index(prev_lvl)
                    self.state = "MAIN_MENU"
                elif status == "GAME_COMPLETED":
                    self.audio.play_finale()
                    self.state = "VICTORY"

            elif self.state == "PAUSED":
                self.level_manager.draw(self.canvas)
                self.pause_menu.handle_events(events)
                self.pause_menu.draw(self.canvas)

            elif self.state == "SETTINGS":
                if self.previous_state == "PAUSED":
                    self.level_manager.draw(self.canvas)
                else:
                    self.main_menu.draw(self.canvas)
                self.settings_menu.handle_events(events)
                self.settings_menu.draw(self.canvas)

            elif self.state == "CHAPTER_COMPLETE":
                self._handle_chapter_complete_events(events)
                self._draw_chapter_complete(self.canvas)

            elif self.state == "VICTORY":
                self._handle_victory_events(events)
                self._draw_victory(self.canvas)

            self._present_canvas()

        pygame.quit()
        sys.exit()

    def _handle_chapter_complete_events(
        self, events: list[pygame.event.Event]
    ) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_e,
            ):
                self.audio.play("ui_select")
                self.state = "PLAYING"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.audio.play("ui_select")
                self.state = "PLAYING"

    def _draw_chapter_complete(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["bg_deep"])
        panel = pygame.Rect(VIRTUAL_WIDTH // 2 - 440, 160, 880, 400)
        ui.panel(surface,panel,accented=True)

        cur_meta = CHAPTER_METADATA.get(self.completed_chapter_num, {})
        next_meta = CHAPTER_METADATA.get(self.completed_chapter_num + 1, {})

        draw_fitted(surface, f"CHAPTER {self.completed_chapter_num} COMPLETE",
                    pygame.Rect(250, 206, 780, 48), COLORS["plate_active"],
                    size=36, min_size=22, bold=True)
        draw_fitted(surface, cur_meta.get("title", ""),
                    pygame.Rect(260, 265, 760, 40), COLORS["ui_text"], size=24)
        draw_fitted(surface, f"Next Sector: {next_meta.get('title', '')}",
                    pygame.Rect(255, 344, 770, 39), COLORS["ui_accent"],
                    size=23, min_size=16)
        draw_fitted(surface, next_meta.get("description", ""),
                    pygame.Rect(245, 389, 790, 39), COLORS["ui_text"],
                    size=18, min_size=13)
        draw_fitted(surface, KIP_CHAPTER_MILESTONES.get(self.completed_chapter_num, ""),
                    pygame.Rect(250, 435, 780, 39), COLORS["ui_text"], size=17, min_size=13)
        draw_fitted(surface, "Press [Enter / Space] or Click to Enter Next Chapter",
                    pygame.Rect(250, 488, 780, 36), COLORS["ui_warning"],
                    size=20, min_size=15)

    def _handle_victory_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.audio.play("ui_select")
                self.state = "MAIN_MENU"

    def _draw_victory(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["bg_deep"])
        logs_count = len(self.save_manager.data.get("collected_logs", []))
        ui.panel(surface,pygame.Rect(95,210,1090,423),accented=True)

        draw_fitted(surface, "FACILITY ESCAPED // PROTOCOL COMPLETE",
                    pygame.Rect(105, 254, 1070, 55), COLORS["plate_active"],
                    size=38, min_size=23, bold=True)
        draw_fitted(surface, f"Final chamber cleared. Total completed: {len(self.save_manager.data.get('completed_levels', []))}/80.",
                    pygame.Rect(140, 332, 1000, 46), COLORS["ui_text"], size=23)
        draw_fitted(surface, f"Research Logs Recovered: {logs_count} / {self.main_menu.total_logs}",
                    pygame.Rect(140, 388, 1000, 40), COLORS["ui_accent"], size=23)
        draw_fitted(surface, "KIP: Officially, you are now more reliable than the elevator.",
                    pygame.Rect(130, 452, 1020, 60), COLORS["ui_text"], size=20)
        draw_fitted(surface, "Press any key or click to return to Main Menu.",
                    pygame.Rect(200, 565, 880, 34), COLORS["ui_muted"], size=19)

    def _present_canvas(self) -> None:
        win_w, win_h = self.screen.get_size()
        if (win_w, win_h) == (VIRTUAL_WIDTH, VIRTUAL_HEIGHT):
            self.screen.blit(self.canvas, (0, 0))
        else:
            scale = min(win_w / VIRTUAL_WIDTH, win_h / VIRTUAL_HEIGHT)
            scaled_w = max(1, int(VIRTUAL_WIDTH * scale))
            scaled_h = max(1, int(VIRTUAL_HEIGHT * scale))
            scaled = pygame.transform.scale(
                self.canvas, (scaled_w, scaled_h)
            )
            self.screen.fill((0, 0, 0))
            self.screen.blit(
                scaled, ((win_w - scaled_w) // 2, (win_h - scaled_h) // 2)
            )
        pygame.display.flip()