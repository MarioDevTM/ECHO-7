import tempfile
import unittest
from pathlib import Path
from src.core.save_manager import SaveManager
from src.levels.level_loader import LevelLoader


class TestProgressionAndLevels(unittest.TestCase):
    def test_save_manager_progression_and_corruption_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            sm = SaveManager(save_path)
            self.assertEqual(sm.data["unlocked_level"], 1)

            sm.mark_level_completed(1)
            self.assertEqual(sm.data["unlocked_level"], 2)
            self.assertIn(1, sm.data["completed_levels"])

            # Corrupt file and verify graceful recovery
            save_path.write_text("{corrupted_json!!!", encoding="utf-8")
            sm_recovered = SaveManager(save_path)
            self.assertEqual(sm_recovered.data["unlocked_level"], 1)

    def test_legacy_default_levels_generate_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = LevelLoader(Path(tmp))
            loader.ensure_default_levels()
            for lvl in range(1, 21):
                data = loader.load_level_data(lvl)
                self.assertEqual(data["level_id"], lvl)
                self.assertIn("spawn", data)
                self.assertIn("exit", data)
                self.assertGreater(len(data["tiles"]), 0)

    def test_all_eighty_shipped_levels_validate(self):
        loader=LevelLoader()
        report=loader.validate_all_levels()
        self.assertEqual(len(report),80)
        self.assertTrue(all(not errors for errors in report.values()),report)

    def test_legacy_save_unlocks_room_21(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"save.json"
            path.write_text(json.dumps({"unlocked_level":20,"current_level":20,
                                        "completed_levels":list(range(1,21))}),encoding="utf-8")
            save=SaveManager(path)
            self.assertEqual(save.data["unlocked_level"],21)
            self.assertEqual(save.data["current_level"],20)

if __name__ == "__main__":
    unittest.main()