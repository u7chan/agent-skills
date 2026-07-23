import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_stages_only_explicit_task_paths(self):
        self.assertIn("`git add -- <path>...`", self.skill)
        self.assertIn("staged pathが対象集合と完全一致", self.skill)
        self.assertIn("対象外のstage済み変更があれば", self.skill)
        self.assertNotIn("`git add .`を使う", self.skill)
        self.assertNotIn("`git add -A`を使う", self.skill)

    def test_unknown_untracked_files_are_excluded(self):
        self.assertIn("今回の成果物だと確認できるものだけ", self.skill)
        self.assertIn("出自や必要性を判断できないファイルはstageしない", self.skill)

    def test_does_not_push_or_create_a_pr(self):
        self.assertIn("pushやPR作成は行わない", self.skill)
        self.assertNotIn("`git push`", self.skill)
        self.assertNotIn("`gh pr create", self.skill)


if __name__ == "__main__":
    unittest.main()
