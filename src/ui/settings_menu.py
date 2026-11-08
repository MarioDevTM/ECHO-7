import pygame
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLORS
from src.ui.text_layout import draw_fitted
from src.ui import components as ui


class SettingsMenu:
    """Two-column settings menu for audio, display, camera shake, and full key remapping."""

    def __init__(self, game) -> None:
        self.game = game
        self.selected_index = 0
        self.awaiting_remap_action: str | None = None
        self.font_title = pygame.font.SysFont("consolas", 36, bold=True)
        self.font_item = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_hint = pygame.font.SysFont("consolas", 16)
        self.item_rects: list[tuple[pygame.Rect, str]] = []
        self._overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((5, 11, 22, 239))

    def _get_rows(self) -> list[tuple[str, str]]:
        s = self.game.save_manager.data["settings"]
        kb = self.game.save_manager.get_keybinds()

        def kname(action: str) -> str:
            if self.awaiting_remap_action == action:
                return "[PRESS KEY...]"
            return pygame.key.name(kb[action][0]).upper()

        return [
            (f"Master Volume:   {int(round(s['master_volume'] * 100))}%", "MASTER_VOL"),
            (f"SFX Volume:      {int(round(s['sfx_volume'] * 100))}%", "SFX_VOL"),
            (f"Music Volume:    {int(round(s['music_volume'] * 100))}%", "MUSIC_VOL"),
            (f"Fullscreen:      {'ON' if s.get('fullscreen', False) else 'OFF'}", "FULLSCREEN"),
            (f"Camera Shake:    {'ON' if s.get('camera_shake', True) else 'OFF'}", "CAMERA_SHAKE"),
            (f"Reduced Motion:  {'ON' if s.get('reduced_motion', False) else 'OFF'}", "REDUCED_MOTION"),
            (f"Puzzle Hints:    {'ON' if s.get('hints', True) else 'OFF'}", "HINTS"),
            (f"Move Left:       {kname('left')}", "REMAP_left"),
            (f"Move Right:      {kname('right')}", "REMAP_right"),
            (f"Climb Up:        {kname('up')}", "REMAP_up"),
            (f"Crouch / Down:   {kname('down')}", "REMAP_down"),
            (f"Jump:            {kname('jump')}", "REMAP_jump"),
            (f"Interact:        {kname('interact')}", "REMAP_interact"),
            (f"Air Dash:        {kname('dash')}", "REMAP_dash"),
            (f"Sprint / Run:    {kname('run')}", "REMAP_run"),
            ("Save & Return", "BACK"),
        ]

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        rows = self._get_rows()
        self.selected_index %= len(rows)

        for event in events:
            if self.awaiting_remap_action is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key != pygame.K_ESCAPE:
                        self.game.save_manager.set_keybind(
                            self.awaiting_remap_action, event.key
                        )
                    self.awaiting_remap_action = None
                    self.game.audio.play("ui_select")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.audio.play("ui_select")
                    self.game.close_settings()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.selected_index = (self.selected_index - 1) % len(rows)
                    self.game.audio.play("ui_move")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_index = (self.selected_index + 1) % len(rows)
                    self.game.audio.play("ui_move")
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_value(rows[self.selected_index][1], -0.1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_value(rows[self.selected_index][1], 0.1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._activate(rows[self.selected_index][1])

            elif event.type == pygame.MOUSEMOTION:
                vpos = self.game.window_to_virtual(event.pos)
                for idx, (rect, _) in enumerate(self.item_rects):
                    if rect.collidepoint(vpos):
                        self.selected_index = idx

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                vpos = self.game.window_to_virtual(event.pos)
                for idx, (rect, code) in enumerate(self.item_rects):
                    if rect.collidepoint(vpos):
                        self.selected_index = idx
                        self._activate(code)
                        break

    def _adjust_value(self, code: str, delta: float) -> None:
        s = self.game.save_manager.data["settings"]
        key_map = {
            "MASTER_VOL": "master_volume",
            "SFX_VOL": "sfx_volume",
            "MUSIC_VOL": "music_volume",
        }
        if code in key_map:
            k = key_map[code]
            s[k] = round(max(0.0, min(1.0, s[k] + delta)), 2)
            self.game.save_manager.save()
            self.game.audio.update_volumes()
            self.game.audio.play("ui_move")

    def _activate(self, code: str) -> None:
        s = self.game.save_manager.data["settings"]
        if code in ("MASTER_VOL", "SFX_VOL", "MUSIC_VOL"):
            self._adjust_value(code, 0.1)
        elif code == "FULLSCREEN":
            s["fullscreen"] = not s.get("fullscreen", False)
            self.game.save_manager.save()
            self.game.apply_display_settings()
            self.game.audio.play("ui_select")
        elif code == "HINTS":
            s["hints"] = not s.get("hints", True)
            self.game.save_manager.save()
        elif code == "REDUCED_MOTION":
            s["reduced_motion"] = not s.get("reduced_motion", False)
            self.game.save_manager.save()
            self.game.audio.play("ui_select")
        elif code == "CAMERA_SHAKE":
            s["camera_shake"] = not s.get("camera_shake", True)
            self.game.save_manager.save()
            self.game.audio.play("ui_select")
        elif code.startswith("REMAP_"):
            self.awaiting_remap_action = code.replace("REMAP_", "")
            self.game.audio.play("ui_select")
        elif code == "BACK":
            self.game.audio.play("ui_select")
            self.game.close_settings()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._overlay, (0, 0))

        ui.panel(surface, pygame.Rect(78,34,1124,627),accented=True)
        draw_fitted(surface, "SYSTEM SETTINGS & CONTROLS",
                    pygame.Rect(110, 42, 1060, 54), COLORS["ui_accent"],
                    size=36, min_size=22, bold=True)
        draw_fitted(surface,
                    "Use [Up/Down] to select, [Left/Right] to adjust volume, [Enter/Click] to toggle or remap.",
                    pygame.Rect(110, 93, 1060, 35), COLORS["ui_text"],
                    size=16, min_size=12)

        rows = self._get_rows()
        self.item_rects.clear()

        # Two-column settings layout, with a separate final confirmation button.
        col_w = 460
        row_h = 42
        gap_y = 50
        left_x = VIRTUAL_WIDTH // 2 - col_w - 20
        right_x = VIRTUAL_WIDTH // 2 + 20
        start_y = 165
        draw_fitted(surface,"AUDIO & DISPLAY",pygame.Rect(left_x,start_y-30,col_w,20),
                    ui.CYAN,size=14,min_size=12,bold=True,align='left')
        draw_fitted(surface,"KEY BINDINGS",pygame.Rect(right_x,start_y-30,col_w,20),
                    ui.CYAN,size=14,min_size=12,bold=True,align='left')
        for idx, (label, code) in enumerate(rows):
            if code == "BACK":
                rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 220, 579, 440, 48)
            elif idx < 7:
                rect = pygame.Rect(left_x, start_y + idx * gap_y, col_w, row_h)
            else:
                rect = pygame.Rect(right_x, start_y + (idx - 7) * gap_y, col_w, row_h)

            self.item_rects.append((rect, code))
            selected = idx == self.selected_index
            ui.button(surface,rect,label,selected=idx==self.selected_index,
                      primary=code=="BACK",size=16)
            if code in ("MASTER_VOL","SFX_VOL","MUSIC_VOL"):
                val=self.game.save_manager.data["settings"][{"MASTER_VOL":"master_volume","SFX_VOL":"sfx_volume","MUSIC_VOL":"music_volume"}[code]]
                ui.progress(surface,pygame.Rect(rect.left+14,rect.bottom-6,rect.width-28,3),val,1.0)
