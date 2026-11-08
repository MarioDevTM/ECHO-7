import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLORS
from src.ui.text_layout import draw_fitted
from src.ui import components as ui


class PauseMenu:
    """In-game overlay pause menu with active chamber, quick level-skipping & collectible telemetry."""

    ITEMS = [
        ("Resume", "RESUME"),
        ("Restart from Checkpoint", "RESTART_CP"),
        ("Restart Level", "RESTART_LEVEL"),
        ("Next Chamber  [PgDn / ]]", "NEXT_LEVEL"),
        ("Previous Chamber  [PgUp / []", "PREV_LEVEL"),
        ("Level Selection (All 80)", "LEVEL_SELECT"),
        ("Settings", "SETTINGS"),
        ("Return to Main Menu", "MAIN_MENU"),
    ]

    def __init__(self, game) -> None:
        self.game = game
        self.selected_index = 0
        self.font_title = pygame.font.SysFont("consolas", 36, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 18)
        self.font_btn = pygame.font.SysFont("consolas", 20, bold=True)
        self.button_rects: list[tuple[pygame.Rect, str]] = []
        self._overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((4, 11, 23, 218))

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.audio.play("ui_select")
                    self.game.state = "PLAYING"
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
                    self.game.audio.play("ui_move")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
                    self.game.audio.play("ui_move")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._trigger(self.ITEMS[self.selected_index][1])

            elif event.type == pygame.MOUSEMOTION:
                vpos = self.game.window_to_virtual(event.pos)
                for idx, (rect, _) in enumerate(self.button_rects):
                    if rect.collidepoint(vpos):
                        self.selected_index = idx

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                vpos = self.game.window_to_virtual(event.pos)
                for idx, (rect, action) in enumerate(self.button_rects):
                    if rect.collidepoint(vpos):
                        self.selected_index = idx
                        self._trigger(action)
                        break

    def _trigger(self, action: str) -> None:
        self.game.audio.play("ui_select")
        cur_lvl = getattr(self.game.level_manager, "current_level_num", 1)
        if action == "RESUME":
            self.game.state = "PLAYING"
        elif action == "RESTART_CP":
            self.game.state = "PLAYING"
            self.game.level_manager.trigger_manual_restart()
        elif action == "RESTART_LEVEL":
            self.game.state = "PLAYING"
            self.game.level_manager.load_level(cur_lvl)
        elif action == "NEXT_LEVEL":
            nxt = min(self.game.level_loader.TOTAL_LEVELS, cur_lvl + 1)
            self.game.start_level(nxt)
        elif action == "PREV_LEVEL":
            prv = max(1, cur_lvl - 1)
            self.game.start_level(prv)
        elif action == "LEVEL_SELECT":
            self.game.main_menu.selected_chapter = self.game.level_loader.get_chapter_for_level(cur_lvl)
            self.game.main_menu.mode = "LEVEL_SELECT"
            self.game.main_menu.selected_index = (cur_lvl - 1) % 10
            self.game.state = "MAIN_MENU"
        elif action == "SETTINGS":
            self.game.open_settings("PAUSED")
        elif action == "MAIN_MENU":
            self.game.main_menu.mode = "ROOT"
            self.game.state = "MAIN_MENU"

    def draw(self, surface: pygame.Surface) -> None:
        """Responsive-looking industrial control panel at the fixed 1280x720 canvas."""
        surface.blit(self._overlay, (0, 0))

        panel = pygame.Rect(92, 62, VIRTUAL_WIDTH - 184, VIRTUAL_HEIGHT - 124)
        ui.panel(surface, panel, accented=True)
        draw_fitted(surface, "ECHO-7  //  SYSTEM PAUSED",
                    pygame.Rect(125, 87, 1030, 54), COLORS["ui_accent"],
                    size=34, min_size=23, bold=True, align="left")

        lvl_num = getattr(self.game.level_manager, "current_level_num", 1)
        lvl_name = getattr(self.game.level_manager, "level_name", f"Chamber {lvl_num:02d}")
        log_id = f"log_{lvl_num:02d}"
        collected = log_id in self.game.save_manager.data.get("collected_logs", [])
        status = "LOG RECOVERED" if collected else "LOG NOT FOUND"
        draw_fitted(surface, f"{lvl_name}  //  CHAPTER {(lvl_num - 1) // 10 + 1:02d}  //  {status}",
                    pygame.Rect(124, 154, 1030, 34), (176, 205, 223),
                    size=17, min_size=13, align="left")
        pygame.draw.line(surface, (37, 65, 88), (124, 200), (1156, 200), 2)

        self.button_rects.clear()
        for idx, (label, action) in enumerate(self.ITEMS):
            col, row = idx % 2, idx // 2
            rect = pygame.Rect(130 + col * 517, 225 + row * 83, 478, 62)
            self.button_rects.append((rect, action))
            selected = idx == self.selected_index
            enabled = action != "NEXT_LEVEL" or lvl_num < self.game.level_loader.TOTAL_LEVELS
            ui.button(surface,rect,label,selected=selected and enabled,enabled=enabled,size=19)
        draw_fitted(surface, "UP / DOWN   NAVIGATE    •    ENTER / CLICK   SELECT    •    ESC   RESUME",
                    pygame.Rect(138, 588, 1000, 36), (142, 180, 203),
                    size=14, min_size=12)
