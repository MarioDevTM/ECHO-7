"""Small manually-triggered recurring characters. No automatic dialogue on retries."""
import math
import pygame
from src.core.settings import COLORS
from src.entities.kip_dialogue import dialogue_for_room


class FacilityNPC:
    def __init__(self, id, x, y, dialogue=None, **_):
        self.room_lines = dialogue or []
        self.npc_id = id
        self.rect = pygame.Rect(int(x), int(y) - 42, 32, 42)
        self.interact_rect = self.rect.inflate(36, 22)

    def speak(self, flags, level_num=None, stage=0):
        if self.npc_id == "kip" and level_num is not None:
            flag = f"kip_room_{level_num}" if stage == 0 else None
            line = (self.room_lines[min(stage, len(self.room_lines) - 1)]
                    if level_num >= 25 and self.room_lines else dialogue_for_room(level_num, stage, flags))
            return f"KIP: {line}", flag
        if self.npc_id == "kip":
            if "freight_twice" in flags and "kip_met" in flags:
                return "KIP: Two deliveries. The crate gets a promotion before I do.", None
            if "freight_twice" in flags:
                return "KIP: Your crate completed two jobs. Management loves efficiency.", "kip_met"
            return "KIP: A crate should do two jobs. I should do zero. Negotiations continue.", "kip_met"
        if self.npc_id == "ada":
            return ("ADA: The facility has an exit plan. The paperwork is less confident.", "ada_met")
        if self.npc_id == "kip_final":
            if "kip_met" in flags and "freight_twice" in flags:
                return "KIP: I reserved you a seat. Dispatch says it's a pallet.", None
            return "KIP: Evacuation seating is first come, first crate.", None
        if self.npc_id == "ada_final":
            if "ada_met" in flags:
                return "ADA: You were right about the power. I filed it under 'unusual'.", None
            return "ADA: I would wish you luck, but the speakers are under warranty.", None
        return "KIP: Repair complete. Please do not inspect it.", None

    def draw(self, surface, camera, font, prompted, phase):
        r = camera.apply(self.rect)
        bob = int(math.sin(phase * 0.7) * 2)
        r.y += bob
        is_robot = self.npc_id.startswith('kip')
        suit = (197, 144, 66) if is_robot else (105, 156, 183)
        eye = (255, 215, 123) if is_robot else (140, 239, 255)
        if is_robot:
            pygame.draw.rect(surface, suit, r, border_radius=6)
            pygame.draw.rect(surface, COLORS['tile_border'], r, 2, border_radius=6)
            pygame.draw.rect(surface, COLORS['tile_dark'], r.inflate(-9, -15), border_radius=2)
            pygame.draw.circle(surface, eye, (r.centerx + 4, r.top + 14), 4)
            pygame.draw.line(surface, suit, (r.centerx, r.top), (r.centerx, r.top - 8), 2)
            pygame.draw.circle(surface, eye, (r.centerx, r.top - 9), 3)
        else:
            # ADA is a wall-mounted intercom, visually distinct from equipment buttons.
            pygame.draw.rect(surface, suit, r, 2, border_radius=4)
            pygame.draw.ellipse(surface, eye, r.inflate(-16, -21), 2)
            for offset in (-6, 0, 6):
                pygame.draw.line(surface, eye,
                                 (r.centerx + offset, r.bottom - 11),
                                 (r.centerx + offset, r.bottom - 7), 2)
        if prompted:
            label = font.render('[E] TALK', True, COLORS['ui_text'])
            surface.blit(label, label.get_rect(center=(r.centerx, r.top - 20)))
