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

    def test_routes_uncommitted_end_to_end_requests_to_orchestrator(self):
        self.assertIn("変更がすべてcommit済みのGitHub PR作成", self.skill)
        self.assertIn(
            "未コミットの対象変更からcommitとPR作成まで一連で求められた場合",
            self.skill,
        )
        self.assertIn("`github-pr-orchestrate`へルーティング", self.skill)

    def test_leaf_never_stages_or_commits(self):
        self.assertIn("ファイル修正、`git add`、`git commit`", self.skill)
        self.assertIn("`BASE..HEAD`にcommitがなければ停止", self.skill)

    def test_trigger_description_excludes_end_to_end_pr_wording(self):
        frontmatter = self.skill.split("---", 2)[1]
        self.assertIn("変更がすべてcommit済み", frontmatter)
        self.assertNotIn("PRまで", frontmatter)
        self.assertNotIn("レビュー依頼", frontmatter)


if __name__ == "__main__":
    unittest.main()
