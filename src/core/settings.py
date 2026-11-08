from pathlib import Path
import pygame

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LEVELS_DIR = DATA_DIR / "levels"
SAVE_FILE = DATA_DIR / "save_data.json"

# Former auxiliary rooms 21-24 are now mandatory chapters in the main campaign.
AUXILIARY_ROOMS = {}

# Display & Timing
GAME_TITLE = "ECHO-7 // Abandoned Facility Puzzle Platformer"
VIRTUAL_WIDTH = 1280
VIRTUAL_HEIGHT = 720
FPS = 60
MAX_DT = 1.0 / 30.0
SUBSTEP_MAX_DISP = 12.0

TILE_SIZE = 40

# Player Physics Constants (Pixels / Second)
GRAVITY = 1550.0
MAX_FALL_SPEED = 820.0

WALK_SPEED = 240.0
RUN_SPEED = 365.0
CROUCH_SPEED = 135.0
LADDER_SPEED = 210.0

GROUND_ACCEL = 2200.0
GROUND_DECEL = 2600.0
AIR_ACCEL = 1500.0
AIR_DECEL = 600.0

JUMP_VELOCITY = -575.0
JUMP_CUT_MULTIPLIER = 0.45
COYOTE_TIME = 0.11
JUMP_BUFFER_TIME = 0.12

# Precision movement is opt-in per room to protect earlier machinery puzzles.
WALL_SLIDE_SPEED = 125.0
WALL_JUMP_HORIZONTAL = 360.0
WALL_JUMP_VERTICAL = -555.0
WALL_JUMP_CONTROL_LOCK = 0.14
DASH_SPEED = 670.0
DASH_DURATION = 0.145
DASH_EXIT_SPEED = 290.0
DASH_RECOVERY = 0.10
SPRING_IMPULSE = -885.0

PLAYER_WIDTH = 26
PLAYER_HEIGHT = 46
PLAYER_CROUCH_HEIGHT = 28
CRATE_SIZE = 36

# Base Color Palette
COLORS = {
    "bg_deep": (10, 14, 22),
    "bg_mid": (18, 25, 38),
    "bg_near": (26, 36, 52),
    "tile_main": (45, 58, 78),
    "tile_border": (72, 92, 120),
    "tile_dark": (28, 36, 48),
    "player_suit": (230, 238, 248),
    "player_visor": (0, 230, 255),
    "player_run_visor": (255, 195, 50),
    "crate_light": (145, 186, 183),
    "wind_stream": (150, 235, 219),
    "crate_body": (115, 130, 150),
    "crate_accent": (50, 210, 245),
    "platform": (85, 105, 135),
    "platform_glow": (0, 210, 255),
    "plate_idle": (180, 70, 70),
    "plate_active": (60, 235, 130),
    "switch_off": (220, 80, 65),
    "switch_on": (65, 235, 140),
    "door_closed": (90, 45, 55),
    "door_accent": (240, 85, 85),
    "door_open": (50, 180, 120),
    "spike": (210, 60, 75),
    "acid": (55, 230, 95),
    "acid_glow": (120, 255, 150),
    "water": (35, 125, 210),
    "water_surface": (110, 200, 255),
    "laser": (255, 45, 70),
    "laser_core": (255, 210, 220),
    "optical_beam": (70, 220, 255),
    "checkpoint_idle": (95, 110, 130),
    "checkpoint_active": (50, 235, 200),
    "exit_portal": (135, 85, 255),
    "exit_core": (220, 195, 255),
    "ui_bg": (14, 20, 30),
    "ui_panel": (26, 36, 54),
    "ui_accent": (0, 215, 255),
    "ui_text": (235, 242, 250),
    "ui_muted": (140, 155, 175),
    "ui_warning": (255, 180, 55),
}

# Chapter-Specific Atmospheric Palettes
CHAPTER_THEMES = {
    "awakening": {
        "bg_deep": (10, 14, 22),
        "bg_mid": (18, 25, 38),
        "bg_near": (26, 36, 52),
        "tile_main": (45, 58, 78),
        "tile_border": (72, 92, 120),
    },
    "mechanical": {
        "bg_deep": (18, 14, 12),
        "bg_mid": (32, 24, 20),
        "bg_near": (46, 34, 28),
        "tile_main": (68, 54, 46),
        "tile_border": (110, 86, 70),
    },
    "power": {
        "bg_deep": (10, 18, 24),
        "bg_mid": (16, 30, 40),
        "bg_near": (24, 44, 58),
        "tile_main": (40, 68, 86),
        "tile_border": (65, 135, 165),
    },
    "environmental": {
        "bg_deep": (10, 20, 18),
        "bg_mid": (16, 34, 30),
        "bg_near": (24, 48, 42),
        "tile_main": (42, 72, 64),
        "tile_border": (70, 120, 108),
    },
    "core": {
        "bg_deep": (16, 10, 24),
        "bg_mid": (28, 18, 42),
        "bg_near": (42, 26, 62),
        "tile_main": (62, 44, 88),
        "tile_border": (115, 82, 160),
    },
    "optical": {"bg_deep": (18, 13, 31), "bg_mid": (26, 24, 48), "bg_near": (42, 38, 68),
               "tile_main": (62, 52, 93), "tile_border": (129, 103, 181)},
    "furnace": {"bg_deep": (29, 13, 14), "bg_mid": (46, 23, 22), "bg_near": (66, 37, 29),
               "tile_main": (92, 53, 41), "tile_border": (175, 98, 64)},
    "spire": {"bg_deep": (11, 20, 30), "bg_mid": (23, 37, 51), "bg_near": (38, 57, 71),
               "tile_main": (55, 75, 93), "tile_border": (107, 153, 175)},
    "surface": {"bg_deep": (15, 21, 32), "bg_mid": (28, 39, 54), "bg_near": (47, 64, 81),
               "tile_main": (70, 87, 106), "tile_border": (133, 170, 187)},
}

DEFAULT_KEYBINDS = {
    "left": [pygame.K_a, pygame.K_LEFT],
    "right": [pygame.K_d, pygame.K_RIGHT],
    "up": [pygame.K_w, pygame.K_UP],
    "down": [pygame.K_s, pygame.K_DOWN],
    "jump": [pygame.K_SPACE, pygame.K_w, pygame.K_UP],
    "interact": [pygame.K_e],
    "dash": [pygame.K_x],
    "run": [pygame.K_LSHIFT, pygame.K_RSHIFT],
    "restart": [pygame.K_r],
    "pause": [pygame.K_ESCAPE],
}