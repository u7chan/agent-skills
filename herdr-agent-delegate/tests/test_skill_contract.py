import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.reference = (ROOT / "references" / "agent-cli.md").read_text(
            encoding="utf-8"
        )

    def test_foreground_idle_and_background_done_are_both_complete(self):
        for text in (self.skill, self.reference):
            self.assertIn("foreground", text)
            self.assertIn("idle", text)
            self.assertIn("done", text)
            self.assertIn("双方を完了扱い", text)

    def test_official_primitives_are_used_directly(self):
        self.assertIn("herdr pane run", self.skill)
        self.assertIn("herdr wait agent-status", self.skill)
        self.assertIn("herdr pane read", self.skill)
        removed_scripts = ["wait_for_" + "completion.py", "task_" + "exchange.py"]
        for name in removed_scripts:
            self.assertNotIn(name, self.skill)
            self.assertFalse((ROOT / "scripts" / name).exists())

    def test_removed_environment_variables_are_not_documented(self):
        prefix = "HERDR" + "_DELEGATE_"
        suffixes = (
            "GRID_COLUMNS",
            "MIN_PANE_WIDTH",
            "MIN_PANE_HEIGHT",
            "AUTO_DEDICATED_TAB",
            "MAX_PANES_PER_TAB",
        )
        for name in (prefix + suffix for suffix in suffixes):
            self.assertNotIn(name, self.skill)
