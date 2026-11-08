import json
import os
import shutil
import tempfile
import warnings
from pathlib import Path
from typing import Any
from src.core.settings import SAVE_FILE, DEFAULT_KEYBINDS, AUXILIARY_ROOMS


class SaveManager:
    """Manages persistent JSON save data for 80 levels, chapters, collectibles, and settings."""

    TOTAL_LEVELS = 80
    TOTAL_CHAPTERS = 8

    def __init__(self, save_path: Path = SAVE_FILE) -> None:
        self.save_path = Path(save_path)
        self.data: dict[str, Any] = self._default_data()
        self.backup_before_save = False
        self.load()

    def _default_data(self) -> dict[str, Any]:
        return {
            "unlocked_level": 1,
            "current_level": 1,
            "completed_levels": [],
            "completed_auxiliary": [],
            "collected_logs": [],
            "story_flags": [],
            "settings": {
                "master_volume": 0.8,
                "sfx_volume": 0.8,
                "music_volume": 0.5,
                "fullscreen": False,
                "camera_shake": True,
                "reduced_motion": False,
                "hints": True,
                "keybinds": {k: list(v) for k, v in DEFAULT_KEYBINDS.items()},
            },
        }

    def load(self) -> dict[str, Any]:
        if not self.save_path.exists():
            self.data = self._default_data()
            self.save()
            return self.data

        try:
            raw = json.loads(self.save_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Root save object must be a JSON dictionary.")
            self.data = self._validate_and_merge(raw)
            settings = raw.get("settings")
            self.backup_before_save = not isinstance(settings, dict) or "hints" not in settings
        except (json.JSONDecodeError, ValueError, TypeError):
            shutil.copy2(self.save_path, self.save_path.with_suffix(".corrupt.bak"))
            self.data = self._default_data()
            self.save()
        return self.data

    def _validate_and_merge(self, raw: dict[str, Any]) -> dict[str, Any]:
        clean = self._default_data()

        unlocked = raw.get("unlocked_level", 1)
        if isinstance(unlocked, int):
            clean["unlocked_level"] = max(1, min(self.TOTAL_LEVELS, unlocked))

        # In the old 20-level edition, a completed room 20 meant the final
        # screen. Migrate that progress to unlock the newly added room 21.
        if 20 in raw.get("completed_levels", []) and clean["unlocked_level"] == 20:
            clean["unlocked_level"] = 21

        current = raw.get("current_level", 1)
        if isinstance(current, int):
            # Free stage access is independent of the furthest story unlock.
            clean["current_level"] = max(1, min(self.TOTAL_LEVELS, current))

        completed = raw.get("completed_levels", [])
        if isinstance(completed, list):
            clean["completed_levels"] = sorted(
                {
                    lvl
                    for lvl in completed
                    if isinstance(lvl, int) and 1 <= lvl <= self.TOTAL_LEVELS
                }
            )

        auxiliary = raw.get("completed_auxiliary", [])
        if isinstance(auxiliary, list):
            # Keep historical optional-sector achievement records even though these
            # rooms have joined the main campaign as 21-24.
            clean["completed_auxiliary"] = [n for n in (21, 22, 23, 24) if n in auxiliary]

        logs = raw.get("collected_logs", [])
        if isinstance(logs, list):
            clean["collected_logs"] = sorted(
                {str(item) for item in logs if isinstance(item, str)}
            )

        raw_flags = raw.get("story_flags", [])
        if isinstance(raw_flags, list):
            clean["story_flags"] = sorted({str(flag) for flag in raw_flags if isinstance(flag, str)})

        raw_settings = raw.get("settings", {})
        if isinstance(raw_settings, dict):
            for vol_key in ("master_volume", "sfx_volume", "music_volume"):
                val = raw_settings.get(vol_key)
                if isinstance(val, (int, float)):
                    clean["settings"][vol_key] = max(0.0, min(1.0, float(val)))

            for bool_key in ("fullscreen", "camera_shake", "reduced_motion", "hints"):
                bval = raw_settings.get(bool_key)
                if isinstance(bval, bool):
                    clean["settings"][bool_key] = bval

            kb = raw_settings.get("keybinds")
            if isinstance(kb, dict):
                for action, default_keys in DEFAULT_KEYBINDS.items():
                    user_keys = kb.get(action)
                    if (
                        isinstance(user_keys, list)
                        and len(user_keys) > 0
                        and all(isinstance(k, int) for k in user_keys)
                    ):
                        clean["settings"]["keybinds"][action] = user_keys
                    else:
                        clean["settings"]["keybinds"][action] = list(default_keys)

        return clean

    def save(self) -> None:
        temporary = None
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            if self.backup_before_save:
                backup = self.save_path.with_suffix(".pre-update.bak")
                if not backup.exists():
                    shutil.copy2(self.save_path, backup)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.save_path.parent,
                                             prefix=".echo-save-", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.data, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.save_path)
            self.backup_before_save = False
        except OSError as exc:
            warnings.warn(f"Could not write game progress: {exc}")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def mark_level_completed(self, level_num: int) -> None:
        if level_num not in self.data["completed_levels"]:
            self.data["completed_levels"].append(level_num)
            self.data["completed_levels"].sort()
        if level_num < self.TOTAL_LEVELS:
            self.data["unlocked_level"] = max(
                self.data["unlocked_level"], level_num + 1
            )
            self.data["current_level"] = level_num + 1
        self.save()

    def mark_auxiliary_completed(self, number: int) -> None:
        rooms = self.data["completed_auxiliary"]
        if number in AUXILIARY_ROOMS and number not in rooms:
            rooms.append(number)
            self.save()

    def mark_log_collected(self, log_id: str) -> None:
        if log_id not in self.data["collected_logs"]:
            self.data["collected_logs"].append(log_id)
            self.data["collected_logs"].sort()
            self.save()

    def reset_new_game(self) -> None:
        self.data["unlocked_level"] = 1
        self.data["current_level"] = 1
        self.data["completed_levels"] = []
        self.data["completed_auxiliary"] = []
        self.data["collected_logs"] = []
        self.data["story_flags"] = []
        self.save()

    def get_keybinds(self) -> dict[str, list[int]]:
        kb = self.data["settings"]["keybinds"]
        for k, v in DEFAULT_KEYBINDS.items():
            if k not in kb:
                kb[k] = list(v)
        return kb

    def set_keybind(self, action: str, key_code: int) -> None:
        if action in DEFAULT_KEYBINDS:
            defaults = [k for k in DEFAULT_KEYBINDS[action][1:] if k != key_code]
            self.data["settings"]["keybinds"][action] = [key_code] + defaults
            self.save()