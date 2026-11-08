import pygame
import json
from src.core.settings import LEVELS_DIR
from src.core.settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, COLORS, AUXILIARY_ROOMS
from src.levels.level_loader import CHAPTER_METADATA, DEFAULT_LEVELS
from src.ui.text_layout import draw_fitted
from src.ui import components as ui
from src.visuals.scene_renderer import SceneRenderer


class MainMenu:
    """Cohesive industrial main menu with chapter background previews, 80-level selector, and telemetry."""

    def __init__(self, game) -> None:
        self.game = game
        self.mode = "ROOT"  # "ROOT", "CHAPTER_SELECT", "LEVEL_SELECT", "MUSIC_GALLERY", "CREDITS"
        self.selected_index = 0
        self.selected_chapter = 1
        self.gallery_chapter = 1
        self.scenery = SceneRenderer()
        self.level_catalog = {}
        for number in range(1, self.game.level_loader.TOTAL_LEVELS + 1):
            path = LEVELS_DIR / f"level_{number:02d}.json"
            if path.exists():
                self.level_catalog[number] = json.loads(path.read_text(encoding="utf-8"))
        self.total_logs = sum(len(data.get("collectibles", []))
                              for data in self.level_catalog.values())

        self.font_title = pygame.font.SysFont("consolas", 50, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 18)
        self.font_btn = pygame.font.SysFont("consolas", 21, bold=True)
        self.font_meta = pygame.font.SysFont("consolas", 16)

        self.button_rects: list[tuple[pygame.Rect, str]] = []
        self._hero_sprite = None

    def _get_items(self) -> list[tuple[str, str]]:
        unlocked_lvl = self.game.save_manager.data.get("unlocked_level", 1)
        current_lvl = self.game.save_manager.data.get("current_level", 1)
        completed_lvls = set(self.game.save_manager.data.get("completed_levels", []))
        collected_logs = set(self.game.save_manager.data.get("collected_logs", []))

        if self.mode == "CHAPTER_SELECT":
            items: list[tuple[str, str]] = []
            for ch_num in range(1, self.game.level_loader.TOTAL_CHAPTERS + 1):
                meta = CHAPTER_METADATA.get(ch_num, {})
                ch_levels = meta.get("levels", [])
                first_lvl = ch_levels[0] if ch_levels else 1
                is_unlocked = True
                cleared_count = sum(1 for lvl in ch_levels if lvl in completed_lvls)
                chapter_logs = {entry["id"] for lvl in ch_levels for entry in self.level_catalog.get(lvl, {}).get("collectibles", [])}
                logs_count = len(collected_logs & chapter_logs)

                if is_unlocked:
                    status = f"[{cleared_count}/{len(ch_levels)} Cleared | {logs_count}/{len(chapter_logs)} Logs]"
                else:
                    status = "[AVAILABLE]"

                title = meta.get("title", f"Chapter {ch_num}")
                items.append((f"{title}  {status}", f"OPEN_CHAPTER_{ch_num}"))
            items.append(("Back to Main Menu", "BACK_ROOT"))
            return items

        if self.mode == "LEVEL_SELECT":
            meta = CHAPTER_METADATA.get(self.selected_chapter, CHAPTER_METADATA[1])
            ch_levels = meta.get("levels", list(range(1, 11)))
            items = []
            for lvl in ch_levels:
                lvl_data = self.level_catalog.get(lvl, {})
                lvl_name = lvl_data.get("name", f"Chamber {lvl:02d}")
                log_id = f"log_{lvl:02d}"
                has_log = log_id in collected_logs

                if lvl == current_lvl and lvl in completed_lvls:
                    badge = "[CLEARED*]"
                elif lvl == current_lvl:
                    badge = "[CURRENT]"
                elif lvl in completed_lvls:
                    badge = "[CLEARED]"
                elif lvl == unlocked_lvl:
                    badge = "[NEXT]"
                elif lvl > unlocked_lvl:
                    badge = "[AVAILABLE]"
                else:
                    badge = "[OPEN]"

                log_badge = " [LOG: YES]" if has_log else " [LOG: --]"
                items.append((f"{lvl_name}  {badge}{log_badge}", f"LEVEL_{lvl}"))

            items.append(
                (
                    f"Previous Chapter [A / PgUp]     |     Next Chapter [D / PgDn]",
                    "CYCLE_CHAPTER",
                )
            )
            items.append(("Back to Chapters", "BACK_CHAPTERS"))
            return items

        if self.mode == "AUXILIARY":
            cleared = self.game.save_manager.data["completed_auxiliary"]
            rooms = [(f"{name}  [CLEARED]" if n in cleared else name, f"AUX_{n}")
                     for n, name in AUXILIARY_ROOMS.items()]
            return rooms + [("Return to Main Menu", "BACK_ROOT")]

        if self.mode == "MUSIC_GALLERY":
            tracks = []
            for num in range(1, 9):
                chapter = CHAPTER_METADATA.get(num, {})
                name = chapter.get("title", f"Chapter {num}").split("—")[-1].strip()
                current = "  [PLAYING]" if self.game.audio.gallery_active and num == self.gallery_chapter else ""
                if current and self.game.audio.gallery_paused:
                    current = "  [PAUSED]"
                tracks.append((f"{num:02d}  //  {name}{current}", f"GALLERY_{num}"))
            tracks.append(("Pause / Resume", "GALLERY_TOGGLE"))
            tracks.append(("Return to Main Menu", "GALLERY_BACK"))
            return tracks

        if self.mode == "CREDITS":
            return [("Return to Main Menu", "BACK_ROOT")]

        if self.mode == "CONFIRM_NEW_GAME":
            return [("Create new save / clear campaign progress", "CONFIRM_RESET"),
                    ("Cancel / Keep existing progress", "CANCEL_RESET")]

        return [
            ("New Game", "NEW_GAME"),
            ("Continue", "CONTINUE"),
            ("Chapter Selection", "CHAPTER_SELECT"),
            ("Level Selection", "LEVEL_SELECT"),
            ("Soundtrack Gallery", "MUSIC_GALLERY"),
            ("Settings", "SETTINGS"),
            ("Credits", "CREDITS"),
            ("Quit", "QUIT"),
        ]

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        items = self._get_items()
        if items:
            self.selected_index %= len(items)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    step = 2 if self.mode in ("CHAPTER_SELECT", "LEVEL_SELECT") else 1
                    self.selected_index = (self.selected_index - step) % len(items)
                    self.game.audio.play("ui_move")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    step = 2 if self.mode in ("CHAPTER_SELECT", "LEVEL_SELECT") else 1
                    self.selected_index = (self.selected_index + step) % len(items)
                    self.game.audio.play("ui_move")
                elif self.mode in ("CHAPTER_SELECT", "LEVEL_SELECT") and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    total_cards = 8 if self.mode == "CHAPTER_SELECT" else 10
                    if self.selected_index < total_cards:
                        if event.key == pygame.K_LEFT and self.selected_index % 2 == 1:
                            self.selected_index -= 1
                        elif event.key == pygame.K_RIGHT and self.selected_index % 2 == 0:
                            self.selected_index += 1
                        self.game.audio.play("ui_move")
                elif self.mode == "LEVEL_SELECT" and event.key in (pygame.K_a, pygame.K_d, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                    delta = -1 if event.key in (pygame.K_a, pygame.K_PAGEUP) else 1
                    self.selected_chapter = (self.selected_chapter - 1 + delta) % self.game.level_loader.TOTAL_CHAPTERS + 1
                    self.selected_index = 0
                    self.game.audio.play("ui_move")
                elif self.mode in ("LEVEL_SELECT", "CHAPTER_SELECT") and pygame.K_1 <= event.key <= pygame.K_8:
                    ch_jump = event.key - pygame.K_1 + 1
                    self.selected_chapter = ch_jump
                    self.mode = "LEVEL_SELECT"
                    self.selected_index = 0
                    self.game.audio.play("ui_select")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._trigger_action(items[self.selected_index][1])
                elif event.key == pygame.K_ESCAPE:
                    if self.mode == "LEVEL_SELECT":
                        self.mode = "CHAPTER_SELECT"
                        self.selected_index = self.selected_chapter - 1
                        self.game.audio.play("ui_select")
                    elif self.mode == "MUSIC_GALLERY":
                        self.game.audio.leave_gallery()
                        self.mode = "ROOT"
                        self.selected_index = 0
                    elif self.mode in ("CHAPTER_SELECT", "CREDITS", "AUXILIARY", "CONFIRM_NEW_GAME"):
                        self.mode = "ROOT"
                        self.selected_index = 0
                        self.game.audio.play("ui_select")

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
                        self._trigger_action(action)
                        break

    def _action_locked(self, action: str) -> bool:
        """All chapters and levels are playable from a fresh save.

        Completing a level still has separate, persistent meaning; selecting it
        does NOT auto-complete it or advance the story progression marker.
        """
        return False

    def _trigger_action(self, action: str) -> None:
        if self._action_locked(action):
            self.game.audio.play("ui_move")
            return
        if action == "NEW_GAME":
            has_progress = (self.game.save_manager.data.get("unlocked_level", 1) > 1
                            or self.game.save_manager.data.get("current_level", 1) > 1
                            or bool(self.game.save_manager.data.get("completed_levels"))
                            or bool(self.game.save_manager.data.get("collected_logs")))
            if has_progress:
                self.mode = "CONFIRM_NEW_GAME"
                self.selected_index = 1   # Safe default: do not clear saves
                self.game.audio.play("ui_select")
            else:
                self.game.start_level(1)
        elif action == "CONFIRM_RESET":
            self.game.save_manager.reset_new_game()
            self.game.start_level(1)
        elif action == "CANCEL_RESET":
            self.mode = "ROOT"
            self.selected_index = 0
            self.game.audio.play("ui_select")
        elif action == "CONTINUE":
            self.game.audio.play("ui_select")
            lvl = self.game.save_manager.data.get("current_level", 1)
            self.game.start_level(lvl)
        elif action == "CHAPTER_SELECT":
            self.game.audio.play("ui_select")
            self.mode = "CHAPTER_SELECT"
            self.selected_index = 0
        elif action == "LEVEL_SELECT":
            self.game.audio.play("ui_select")
            cur_lvl = self.game.save_manager.data.get("current_level", 1)
            self.selected_chapter = self.game.level_loader.get_chapter_for_level(cur_lvl)
            self.mode = "LEVEL_SELECT"
            self.selected_index = (cur_lvl - 1) % 10
        elif action == "AUXILIARY":
            self.mode = "AUXILIARY"
            self.selected_index = 0
            self.game.audio.play("ui_select")
        elif action.startswith("AUX_"):
            self.game.audio.play("ui_select")
            self.game.start_level(int(action[4:]))
        elif action == "MUSIC_GALLERY":
            self.mode = "MUSIC_GALLERY"
            self.selected_index = 0
            self.gallery_chapter = 1
            self.game.audio.preview_chapter(1)
            self.game.audio.play("ui_select")
        elif action.startswith("GALLERY_") and action.split("_")[-1].isdigit():
            self.gallery_chapter = int(action.split("_")[-1])
            self.game.audio.preview_chapter(self.gallery_chapter)
            self.game.audio.play("ui_select")
        elif action == "GALLERY_TOGGLE":
            self.game.audio.toggle_gallery_pause()
        elif action == "GALLERY_BACK":
            self.game.audio.leave_gallery()
            self.mode = "ROOT"
            self.selected_index = 0
            self.game.audio.play("ui_select")
        elif action == "SETTINGS":
            self.game.audio.play("ui_select")
            self.game.open_settings("MAIN_MENU")
        elif action == "CREDITS":
            self.game.audio.play("ui_select")
            self.mode = "CREDITS"
            self.selected_index = 0
        elif action == "QUIT":
            self.game.audio.play("ui_select")
            self.game.running = False
        elif action == "BACK_ROOT":
            self.game.audio.play("ui_select")
            self.mode = "ROOT"
            self.selected_index = 0
        elif action == "BACK_CHAPTERS":
            self.game.audio.play("ui_select")
            self.mode = "CHAPTER_SELECT"
            self.selected_index = self.selected_chapter - 1
        elif action == "CYCLE_CHAPTER":
            self.game.audio.play("ui_move")
            self.selected_chapter = self.selected_chapter % self.game.level_loader.TOTAL_CHAPTERS + 1
        elif action.startswith("OPEN_CHAPTER_"):
            ch_num = int(action.split("_")[-1])
            self.game.audio.play("ui_select")
            self.selected_chapter = ch_num
            self.mode = "LEVEL_SELECT"
            self.selected_index = 0
        elif action.startswith("LEVEL_"):
            lvl = int(action.split("_")[1])
            self.game.audio.play("ui_select")
            self.mode = "ROOT"
            self.game.start_level(lvl)

    def update(self, dt: float) -> None:
        pass

    def _draw_button(self, surface, rect, label, selected, muted=False):
        ui.button(surface, rect, label, selected=selected and not muted,
                  enabled=not muted, primary=self.mode == "ROOT" and label.startswith(("Continue","New Game")),
                  size=18 if self.mode == "ROOT" else 16)

    def _draw_root_hero(self, surface):
        """Save-aware facility console with a prominent, original character portrait."""
        hero = pygame.Rect(134, 156, 1012, 212)
        ui.panel(surface, hero, accented=True)
        data = self.game.save_manager.data
        total = max(1, self.game.level_loader.TOTAL_LEVELS)
        cleared = len(set(data.get("completed_levels", [])))
        cleared = max(0, min(total, cleared))
        cur_lvl = max(1, min(total, int(data.get("current_level", 1))))
        cur_ch = (cur_lvl - 1) // 10 + 1
        logs = len(set(data.get("collected_logs", [])))
        fresh = cleared == 0 and cur_lvl == 1
        pygame.draw.rect(surface, (12, 31, 46), (148, 169, 690, 186))
        pygame.draw.line(surface, (65, 121, 149), (845, 175), (845, 347), 1)
        draw_fitted(surface, "ECHO-7  //  OPERATIVE STATUS", pygame.Rect(167, 175, 600, 26),
                    (90, 216, 237), size=18, min_size=13, bold=True, align="left")
        draw_fitted(surface, "READY FOR DEPLOYMENT" if fresh else "CAMPAIGN RECORD RESTORED",
                    pygame.Rect(167, 211, 620, 32), (225, 239, 248),
                    size=23, min_size=16, bold=True, align="left")
        draw_fitted(surface, f"SECTOR {cur_ch:02d}   /   CHAMBER {cur_lvl:02d}   /   {logs:02d} LOGS RECOVERED",
                    pygame.Rect(168, 255, 623, 25), (155, 185, 205), size=16, min_size=12, align="left")
        progress = pygame.Rect(168, 303, 615, 13)
        ui.progress(surface, progress, cleared, total)
        pygame.draw.rect(surface, (87, 125, 146), progress, 1)
        draw_fitted(surface, f"{cleared:02d} OF {total} CHAMBERS CLEARED   //   {cleared / total * 100:05.1f}%",
                    pygame.Rect(168, 324, 608, 22), (119, 199, 214), size=14, min_size=11, align="left")
        portrait = pygame.Rect(864, 169, 261, 187)
        pygame.draw.rect(surface, (7, 16, 28), portrait)
        pygame.draw.rect(surface, (59, 118, 151), portrait, 1)
        for y in range(portrait.top + 15, portrait.bottom - 4, 20):
            pygame.draw.line(surface, (22, 43, 60), (portrait.left + 11, y), (portrait.right - 12, y))
        from pathlib import Path
        art_root = Path(__file__).resolve().parents[2] / 'data/art'
        if self._hero_sprite is None:
            try:
                player = pygame.image.load(str(art_root / 'player/idle_0.png')).convert_alpha()
                self._hero_sprite = pygame.transform.scale(player, (108, 168))
            except (pygame.error, OSError):
                self._hero_sprite = False
        if self._hero_sprite is not False:
            surface.blit(self._hero_sprite, (portrait.x + 35, portrait.y + 3))
        # The player's head is used for the APPLICATION icon only.
        # Keep this progress panel dedicated to the full in-game character
        # and genuine campaign telemetry; do not display the .ico artwork here.
        draw_fitted(surface, 'EXPLORATION UNIT', pygame.Rect(1010, 206, 101, 34),
                    (91, 183, 202), size=12, min_size=10, bold=True, align='center')
        pygame.draw.line(surface, (46, 99, 129), (1011, 250), (1110, 250), 1)
        draw_fitted(surface, 'ACTIVE', pygame.Rect(1010, 258, 101, 26),
                    (166, 225, 229), size=14, min_size=10, bold=True, align='center')
        draw_fitted(surface, f'CH. {cur_ch:02}', pygame.Rect(1010, 289, 101, 24),
                    (124, 176, 195), size=12, min_size=10, align='center')
        draw_fitted(surface, 'UNIT 07  /  ONLINE', pygame.Rect(877, 331, 236, 18),
                    (118, 205, 220), size=13, min_size=10)

    def _draw_gallery_detail(self, surface):
        """Visual metadata pane; actual audio state stays in AudioManager."""
        chapter = max(1, min(8, self.gallery_chapter))
        descriptions = (
            ('Awakening', 'Diagnostic ambience', 'Glassy pads / soft pulses'),
            ('Mechanical Depths', 'Industrial ambience', 'Machinery / metallic percussion'),
            ('Power Grid', 'Electrical ambience', 'Shimmer / synchronized energy'),
            ('Surveillance Grid', 'Minimal suspense', 'Measured tones / distant echoes'),
            ('Flood Control', 'Hydraulic ambience', 'Flowing resonance / low currents'),
            ('Core Collapse', 'Containment pressure', 'Deep rhythmic urgency'),
            ('Broken Spire', 'Fractured echoes', 'Fragile harmony / broken structures'),
            ('Surface Breach', 'Nocturnal release', 'Moonlit pads / open atmosphere'),
        )
        name, mood, texture = descriptions[chapter - 1]
        pane = pygame.Rect(807, 202, 354, 407)
        ui.panel(surface, pane, accented=True)
        thumb = self.scenery.get_chapter_preview(chapter, (320, 165))
        surface.blit(thumb, (pane.x + 17, pane.y + 15))
        pygame.draw.rect(surface, (70, 130, 156), (pane.x + 17, pane.y + 15, 320, 165), 1)
        draw_fitted(surface, f'0{chapter}  /  {name.upper()}',
                    pygame.Rect(pane.x + 18, pane.y + 198, 322, 30),
                    ui.CYAN, size=18, min_size=13, bold=True, align='left')
        draw_fitted(surface, mood, pygame.Rect(pane.x + 18, pane.y + 240, 319, 27),
                    ui.TEXT, size=17, min_size=12, align='left')
        draw_fitted(surface, texture, pygame.Rect(pane.x + 18, pane.y + 276, 319, 28),
                    ui.MUTED, size=14, min_size=11, align='left')
        state = ('PAUSED' if self.game.audio.gallery_paused else 'PLAYING') if self.game.audio.gallery_active else 'AUDIO UNAVAILABLE'
        draw_fitted(surface, f'STATUS   /   {state}', pygame.Rect(pane.x + 18, pane.y + 325, 318, 25),
                    ui.AMBER if state == 'PAUSED' else ui.CYAN, size=15, min_size=11, align='left')
        draw_fitted(surface, 'Adaptive layers  //  Synced loops',
                    pygame.Rect(pane.x + 18, pane.y + 362, 318, 18),
                    ui.MUTED, size=12, min_size=10, align='left')

    def _draw_chapter_preview_card(self, surface):
        """Draws a visual preview panel of the focused chapter using the new chapter art."""
        focused_ch = min(8, max(1, self.selected_index + 1)) if self.selected_index < 8 else self.selected_chapter
        meta = CHAPTER_METADATA.get(focused_ch, CHAPTER_METADATA[1])
        card = pygame.Rect(825, 195, 365, 425)
        pygame.draw.rect(surface, (9, 19, 34), card, border_radius=8)
        pygame.draw.rect(surface, COLORS['ui_accent'], card, 2, border_radius=8)

        thumb = self.scenery.get_chapter_preview(focused_ch, (333, 187))
        surface.blit(thumb, (card.left + 16, card.top + 16))
        pygame.draw.rect(surface, (72, 118, 155), (card.left + 16, card.top + 16, 333, 187), 2)

        draw_fitted(surface, meta.get('title', f'Chapter {focused_ch}'),
                    pygame.Rect(card.left + 18, card.top + 216, 329, 34),
                    COLORS['plate_active'], size=19, min_size=13, bold=True, align='left')
        draw_fitted(surface, meta.get('description', ''),
                    pygame.Rect(card.left + 18, card.top + 256, 329, 76),
                    COLORS['ui_text'], size=15, min_size=12, align='left')
        loc_tag = 'EXTERIOR // NOCTURNAL ESCAPE' if focused_ch == 8 else f'INTERIOR // FACILITY SECTOR 0{focused_ch}'
        draw_fitted(surface, loc_tag,
                    pygame.Rect(card.left + 18, card.top + 344, 329, 26),
                    COLORS['ui_warning'], size=14, min_size=11, bold=True, align='left')
        allowed=True
        draw_fitted(surface, 'Press [1-8] or Click to Open Sector' if allowed else 'LOCKED / COMPLETE PRIOR CHAPTERS',
                    pygame.Rect(card.left + 18, card.top + 380, 329, 26),
                    COLORS['ui_muted'], size=14, min_size=11, align='left')

    def draw(self, surface: pygame.Surface) -> None:
        """Shared 1280x720 layout with exact matching clickable bounds."""
        bg_ch = (self.gallery_chapter if self.mode == "MUSIC_GALLERY"
                 else self.selected_chapter if self.mode == "LEVEL_SELECT"
                 else min(8,self.selected_index+1) if self.mode == "CHAPTER_SELECT" and self.selected_index < 8
                 else 1)
        self.scenery.draw_menu_background(surface, bg_ch)
        self.button_rects.clear()
        draw_fitted(surface, "ECHO-7  /  FACILITY OPERATIONS",
                    pygame.Rect(92,28,1096,66),ui.TEXT,size=43,min_size=28,bold=True)
        completed = len(self.game.save_manager.data.get('completed_levels', []))
        logs = len(self.game.save_manager.data.get('collected_logs', []))
        draw_fitted(surface, f"{completed:02d} / 80 CHAMBERS CLEARED     |     {logs:02d} / {self.total_logs} LOGS RECOVERED",
                    pygame.Rect(120,96,1040,30),ui.MUTED,size=16,min_size=12)
        if self.mode == 'CREDITS':
            self._draw_credits(surface)
            return
        if self.mode == 'ROOT':
            self._draw_root_hero(surface)
            ui.section(surface,"COMMAND CENTER",pygame.Rect(158,374,860,30))
            for idx,(label, action) in enumerate(self._get_items()):
                rect = pygame.Rect(168+(idx%2)*497,414+(idx//2)*62,449,49)
                self.button_rects.append((rect,action))
                self._draw_button(surface,rect,label,idx==self.selected_index)
        elif self.mode == 'CHAPTER_SELECT':
            ui.section(surface,"SELECT A FACILITY SECTOR",pygame.Rect(90,147,695,32))
            self._draw_chapter_preview_card(surface)
            for idx,(label,action) in enumerate(self._get_items()):
                if idx < 8:
                    rect=pygame.Rect(90+(idx%2)*365,200+(idx//2)*96,344,78)
                    chapter=idx+1
                    clearance=sum(n in self.game.save_manager.data.get('completed_levels', [])
                                  for n in range(1+(chapter-1)*10,chapter*10+1))
                    header=f"{chapter:02d}   {CHAPTER_METADATA[chapter]['title'].split('—')[-1].strip()}"
                    status=f"{clearance}/10 COMPLETE" if not self._action_locked(action) else "LOCKED"
                    ui.button(surface,rect,header,selected=idx==self.selected_index,
                              enabled=not self._action_locked(action),size=18)
                    draw_fitted(surface,status,pygame.Rect(rect.x+20,rect.bottom-24,rect.w-40,18),
                                ui.MUTED,size=12,min_size=11,align='left')
                else:
                    rect=pygame.Rect(90,610,709,45)
                    ui.button(surface,rect,label,selected=idx==self.selected_index,size=17)
                self.button_rects.append((rect,action))
        elif self.mode == 'LEVEL_SELECT':
            meta=CHAPTER_METADATA.get(self.selected_chapter,CHAPTER_METADATA[1])
            ui.section(surface,meta.get('title',''),pygame.Rect(105,150,1040,30),
                       subtitle=meta.get('description',''))
            for idx,(label,action) in enumerate(self._get_items()):
                if idx < 10:
                    rect=pygame.Rect(105+(idx%2)*540,235+(idx//2)*69,508,57)
                    lvl=(self.selected_chapter-1)*10+idx+1
                    if lvl in self.level_catalog:
                        name=self.level_catalog[lvl].get('name',f'Chamber {lvl:02d}').split('//')[-1].strip()
                    else:
                        name=f'Chamber {lvl:02d}'
                    completed_levels=self.game.save_manager.data.get('completed_levels',[])
                    status='CLEARED' if lvl in completed_levels else ('CURRENT' if lvl == self.game.save_manager.data.get('current_level') else 'AVAILABLE')
                    display=f"{lvl:02d}   {name}   /   {status}"
                    ui.button(surface,rect,display,selected=idx==self.selected_index,
                              enabled=not self._action_locked(action),size=17)
                else:
                    rect=pygame.Rect(290,579+(idx-10)*49,700,41)
                    ui.button(surface,rect,label,selected=idx==self.selected_index,size=16)
                self.button_rects.append((rect,action))
        elif self.mode == 'CONFIRM_NEW_GAME':
            rect=pygame.Rect(266,207,748,392)
            ui.panel(surface,rect,accented=True)
            draw_fitted(surface,"RESET CAMPAIGN PROGRESS?",
                        pygame.Rect(310,253,660,56),ui.AMBER,size=30,min_size=23,bold=True)
            draw_fitted(surface,"This clears cleared levels, unlocked chapters and collected logs."
                        " Controls and audio preferences remain saved.",
                        pygame.Rect(317,325,646,83),ui.TEXT,size=19,min_size=14)
            for idx,(label,action) in enumerate(self._get_items()):
                btn=pygame.Rect(343,444+idx*65,594,50)
                ui.button(surface,btn,label,selected=idx==self.selected_index,size=17)
                self.button_rects.append((btn,action))
        elif self.mode == 'MUSIC_GALLERY':
            ui.section(surface,"SOUNDTRACK ARCHIVE",pygame.Rect(127,157,940,32))
            self._draw_gallery_detail(surface)
            for idx,(label,action) in enumerate(self._get_items()):
                if idx < 8:
                    rect=pygame.Rect(130,204+idx*47,626,42)
                else:
                    rect=pygame.Rect(130+(idx-8)*323,606,307,45)
                ui.button(surface,rect,label,selected=idx==self.selected_index,size=15)
                self.button_rects.append((rect,action))
        else:
            for idx,(label,action) in enumerate(self._get_items()):
                rect=pygame.Rect(400,192+idx*59,480,48)
                ui.button(surface,rect,label,selected=idx==self.selected_index,size=17)
                self.button_rects.append((rect,action))
        footer = ("ALL 80 OPEN  //  ARROWS FOCUS  //  A/D OR PGUP/PGDN CHAPTER  //  ENTER SELECT"
                  if self.mode == "LEVEL_SELECT" else
                  "ALL 80 OPEN  //  ARROWS NAVIGATE  //  ENTER SELECT  //  ESC BACK")
        draw_fitted(surface,footer,
                    pygame.Rect(125,684,1030,24),ui.MUTED,size=14,min_size=11)

    def _draw_credits(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(VIRTUAL_WIDTH // 2 - 420, 175, 840, 380)
        pygame.draw.rect(surface, COLORS["ui_panel"], panel, border_radius=8)
        pygame.draw.rect(surface, COLORS["tile_border"], panel, width=2, border_radius=8)

        lines = [
            ("ECHO-7 // ABANDONED FACILITY PUZZLE PLATFORMER", COLORS["ui_accent"]),
            ("", COLORS["ui_text"]),
            ("Architecture & Gameplay Systems:  Python 3.12+ & pygame-ce", COLORS["ui_text"]),
            ("Physics & Sub-Stepped Solver:     Custom AABB & Platform Carry Engine", COLORS["ui_text"]),
            ("Environmental Puzzle Framework:   80 Multi-Stage Chambers across 8 Chapters", COLORS["ui_text"]),
            ("Visuals & Audio: Full-Level Chapter Art, Robot Sprites & Adaptive Score", COLORS["ui_text"]),
            ("", COLORS["ui_text"]),
            ("Thank you for exploring the facility.", COLORS["plate_active"]),
        ]
        for i, (text, color) in enumerate(lines):
            draw_fitted(surface, text, pygame.Rect(235, 204 + i * 36, 810, 31),
                        color, size=18, min_size=12)

        self.button_rects.clear()
        btn_rect = pygame.Rect(VIRTUAL_WIDTH // 2 - 220, 585, 440, 50)
        self.button_rects.append((btn_rect, "BACK_ROOT"))
        pygame.draw.rect(surface, (38, 58, 86), btn_rect, border_radius=6)
        pygame.draw.rect(surface, COLORS["ui_accent"], btn_rect, width=2, border_radius=6)
        txt = self.font_btn.render("Return to Main Menu", True, COLORS["ui_text"])
        surface.blit(txt, txt.get_rect(center=btn_rect.center))
