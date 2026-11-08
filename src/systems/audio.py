"""ECHO-7 original music playback and procedural SFX. Silent without an audio device."""
from array import array
import math
from pathlib import Path
import pygame


MUSIC_DIR = Path(__file__).resolve().parents[2] / "data" / "music"


class AudioManager:
    SAMPLE_RATE = 44100

    def __init__(self, save_manager) -> None:
        self.save_manager = save_manager
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ambient_channel = None
        self.rhythm_channel = None
        self.current_chapter_track = 1
        self.power_mix = 0.0
        self.target_powered = False
        self.in_finale = False
        self.gallery_active = False
        self.gallery_paused = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(max(10, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(2)  # protect synchronized loops from SFX stealing
            self.ambient_channel = pygame.mixer.Channel(0)
            self.rhythm_channel = pygame.mixer.Channel(1)
            self.enabled = True
            self._build_sounds()
        except (pygame.error, OSError):
            self.enabled = False

    def _synth_tone(self, f0, f1, duration, volume=0.35, wave="sine"):
        settings = pygame.mixer.get_init() or (self.SAMPLE_RATE, -16, 2)
        rate, _format, channels = settings
        count = max(1, int(rate * duration))
        buf = array("h")
        phase = 0.0
        for i in range(count):
            t = i / count
            freq = f0 + (f1 - f0) * t
            phase += 2.0 * math.pi * freq / rate
            env = (1.0 - t) ** 1.4
            if wave == "square":
                raw = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wave == "triangle":
                raw = (2.0 / math.pi) * math.asin(math.sin(phase))
            else:
                raw = math.sin(phase)
            sample = int(max(-32767, min(32767, raw * env * volume * 32767)))
            for _ in range(channels):
                buf.append(sample)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build_sounds(self):
        effects = {
            "jump": (210, 460, .13, .28, "triangle"),
            "dash": (410, 1080, .15, .29, "triangle"),
            "spring": (270, 940, .19, .27, "sine"),
            "dash_recharge": (780, 1210, .12, .25, "sine"),
            "dash_break": (330, 70, .18, .26, "square"),
            "land": (120, 65, .07, .22, "sine"),
            "step": (95, 75, .04, .14, "sine"),
            "switch": (520, 780, .10, .28, "square"),
            "plate": (340, 480, .09, .25, "triangle"),
            "door": (160, 260, .18, .26, "triangle"),
            "collect": (580, 1160, .22, .30, "sine"),
            "checkpoint": (440, 880, .25, .30, "sine"),
            "death": (300, 85, .32, .35, "square"),
            "level_clear": (400, 960, .40, .35, "triangle"),
            "ui_move": (480, 520, .05, .20, "sine"),
            "ui_select": (600, 900, .11, .26, "triangle"),
        }
        for name, args in effects.items():
            self.sounds[name] = self._synth_tone(*args)
        for chapter in range(1, 9):
            for layer in ("quiet", "rhythm"):
                # High-quality original stereo OGG preferred; existing WAV is a safe fallback.
                filename = MUSIC_DIR / f"chapter_{chapter}_{layer}.ogg"
                if not filename.exists():
                    filename = MUSIC_DIR / f"chapter_{chapter}_{layer}.wav"
                if filename.exists():
                    try:
                        self.sounds[f"music_{chapter}_{layer}"] = pygame.mixer.Sound(str(filename))
                    except (pygame.error, OSError):
                        fallback = MUSIC_DIR / f"chapter_{chapter}_{layer}.wav"
                        if fallback.exists():
                            self.sounds[f"music_{chapter}_{layer}"] = pygame.mixer.Sound(str(fallback))
        # Dedicated Level 80 music uses the same synchronized playback architecture.
        for layer in ("quiet", "rhythm"):
            for extension in (".ogg", ".wav"):
                candidate = MUSIC_DIR / f"finale_ascent_{layer}{extension}"
                if candidate.exists():
                    try:
                        self.sounds[f"finale_ascent_{layer}"] = pygame.mixer.Sound(str(candidate))
                        break
                    except (pygame.error, OSError):
                        continue
        if (MUSIC_DIR / "surface_resolution.wav").exists():
            self.sounds["surface_resolution"] = pygame.mixer.Sound(str(MUSIC_DIR / "surface_resolution.wav"))

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return
        settings = self.save_manager.data["settings"]
        vol = settings.get("master_volume", .8) * settings.get("sfx_volume", .8)
        snd = self.sounds[name]
        snd.set_volume(max(0.0, min(1.0, vol)))
        if not snd.get_num_channels():
            snd.play()

    def start_ambient(self, chapter=1):
        if not self.enabled:
            return
        chapter = max(1, min(8, chapter))
        if (self.current_chapter_track == chapter and not self.in_finale
                and self.ambient_channel.get_busy()):
            return  # retry/death/checkpoint never restarts a musical phrase
        self.current_chapter_track = chapter
        self.gallery_active = False
        self.gallery_paused = False
        self.in_finale = False
        self.power_mix = 0.0
        self.target_powered = False
        quiet = self.sounds.get(f"music_{chapter}_quiet")
        rhythm = self.sounds.get(f"music_{chapter}_rhythm")
        if quiet:
            self.ambient_channel.play(quiet, loops=-1, fade_ms=180)
        if rhythm:
            # Both same sample count; muted secondary starts on the same mixer tick.
            self.rhythm_channel.play(rhythm, loops=-1, fade_ms=180)
        self.update_volumes()

    def start_level_80_finale_ascent(self) -> None:
        """Start the Level 80 cue without restarting it on death/checkpoint reloads."""
        if not self.enabled:
            return
        if (self.current_chapter_track == 80 and not self.in_finale
                and self.ambient_channel.get_busy()):
            return
        self.current_chapter_track = 80
        self.gallery_active = False
        self.gallery_paused = False
        self.in_finale = False
        self.power_mix = 0.20
        self.target_powered = False
        quiet = self.sounds.get("finale_ascent_quiet") or self.sounds.get("music_8_quiet")
        rhythm = self.sounds.get("finale_ascent_rhythm") or self.sounds.get("music_8_rhythm")
        if quiet:
            self.ambient_channel.play(quiet, loops=-1, fade_ms=180)
        if rhythm:
            self.rhythm_channel.play(rhythm, loops=-1, fade_ms=180)
        self.update_volumes()

    def update_music_state(self, dt, powered, finale_stage: int = 0):
        if not self.enabled or self.in_finale:
            return
        self.target_powered = bool(powered)
        if self.current_chapter_track == 80:
            # Actual milestone signals gradually raise musical urgency.
            target = min(1.0, 0.20 + 0.20 * max(0, min(4, int(finale_stage))))
        else:
            target = 1.0 if powered else 0.0
        delta = min(1.0, max(0.0, dt) / .9)
        self.power_mix += (target - self.power_mix) * delta
        self.update_volumes()

    def preview_chapter(self, chapter: int) -> None:
        """Start the *same* synchronized pair of tracks used during gameplay."""
        if not self.enabled:
            return
        self.start_ambient(chapter)
        self.gallery_active = True
        self.gallery_paused = False
        self.power_mix = 0.85
        self.update_volumes()

    def toggle_gallery_pause(self) -> bool:
        """Pause/resume both music layers without losing their synchronization."""
        if not self.enabled or not self.gallery_active:
            return False
        self.gallery_paused = not self.gallery_paused
        for channel in (self.ambient_channel, self.rhythm_channel):
            if channel:
                if self.gallery_paused:
                    channel.pause()
                else:
                    channel.unpause()
        return self.gallery_paused

    def leave_gallery(self) -> None:
        if not self.enabled:
            return
        self.gallery_active = False
        self.gallery_paused = False
        self.current_chapter_track = 0
        self.ambient_channel.stop()
        self.rhythm_channel.stop()
        self.start_ambient(1)

    def play_finale(self):
        if not self.enabled:
            return
        self.in_finale = True
        self.ambient_channel.stop()
        self.rhythm_channel.stop()
        final = self.sounds.get("surface_resolution")
        if final:
            self.ambient_channel.play(final, loops=-1)
        self.update_volumes()

    def update_volumes(self):
        if not self.enabled:
            return
        settings = self.save_manager.data["settings"]
        vol = max(0.0, min(1.0,
                          settings.get("master_volume", .8) * settings.get("music_volume", .5)))
        if self.ambient_channel:
            self.ambient_channel.set_volume(vol * .67)
        if self.rhythm_channel:
            self.rhythm_channel.set_volume(0 if self.in_finale else vol * .65 * self.power_mix)
