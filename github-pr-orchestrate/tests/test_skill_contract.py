import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_normal_flow_uses_shared_leaf_skills_in_order(self):
        commit_step = self.skill.index("### 3. 今回の変更だけをcommitする")
        create_step = self.skill.index("### 4. pushしてPRを作成する")
        review_step = self.skill.index("### 5. 指定されたレビュー工程を行う")
        self.assertLess(commit_step, create_step)
        self.assertLess(create_step, review_step)
        self.assertIn("../git-changes-commit/SKILL.md", self.skill)
        self.assertIn("../github-pr-create/SKILL.md", self.skill)

    def test_unrelated_changes_are_not_committed(self):
        self.assertIn("対象path、除外path", self.skill)
        self.assertIn("対象外の変更がcommitまたはstageされた場合", self.skill)
        self.assertIn("対象外の変更と未追跡ファイルが保持", self.skill)

    def test_routes_committed_pr_creation_to_leaf(self):
        self.assertIn(
            "PR対象がすべてcommit済みでpush・PR作成だけを求められた場合",
            self.skill,
        )
        self.assertIn("`github-pr-create`を単体で使い", self.skill)

    def test_non_herdr_flow_forbids_delegation_features(self):
        self.assertIn(
            "Herdr、pane、Agent委譲、委譲メタ情報を使用しない", self.skill
        )
        self.assertNotIn("herdr-agent-delegate", self.skill)
        self.assertNotIn("cagent-agent-command-resolve", self.skill)

    def test_review_runs_only_when_requested(self):
        self.assertIn("レビューが明示されていなければPR作成成功で完了", self.skill)
        self.assertIn("「レビューして」「レビュー依頼出して」", self.skill)
        self.assertIn("reviewerの割り当てが明示された場合", self.skill)

    def test_trigger_description_covers_regression_phrase(self):
        frontmatter = self.skill.split("---", 2)[1]
        self.assertIn("未コミットの対象変更", frontmatter)
        self.assertIn("PR作ってレビュー依頼出して", frontmatter)


if __name__ == "__main__":
    unittest.main()
