import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_format_check_never_uses_a_writing_command(self):
        self.assertIn("`format:check`や`prettier --check`", self.skill)
        self.assertIn("非書き込みコマンドだけを実行", self.skill)
        self.assertIn("書き込み型しか見つからない場合は実行せず", self.skill)
        self.assertIn("未実施として本文に理由を記録", self.skill)
        self.assertNotIn("formatを実行して差分が発生", self.skill)


if __name__ == "__main__":
    unittest.main()
