import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_normal_flow_uses_shared_leaf_skills_in_order(self):
        commit_step = self.skill.index("### 3. 今回の変更だけをcommitする")
        create_step = self.skill.index("### 4. pushしてPRを作成・確認する")
        review_step = self.skill.index("### 5. 指定されたレビュー工程を行う")
        self.assertLess(commit_step, create_step)
        self.assertLess(create_step, review_step)
        self.assertIn("`git-changes-commit`", self.skill)
        self.assertIn("`github-pr-create`", self.skill)
        self.assertNotIn("../git-changes-commit/", self.skill)
        self.assertNotIn("../github-pr-create/", self.skill)

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

    def test_committed_changes_skip_commit_and_continue_to_requested_review(self):
        self.assertIn("PR対象がすべてcommit済みならcommit工程をスキップ", self.skill)
        self.assertIn("レビュー工程も明示されていればStep 4の後にStep 5まで進む", self.skill)
        self.assertIn("PR対象に未コミット変更がある場合だけ", self.skill)

    def test_writing_formatter_never_touches_unrelated_paths(self):
        self.assertIn("非書き込みのformat checkを優先", self.skill)
        self.assertIn("今回の対象pathだけに限定できる場合のみ実行", self.skill)
        self.assertIn("repo全体や対象外pathを変更し得る場合は実行せず停止", self.skill)

    def test_existing_pr_does_not_bypass_a_missing_push(self):
        self.assertIn("PR headとlocal `HEAD`が一致する場合だけ", self.skill)
        self.assertIn("`github-pr-create`が既存PRで停止する現行契約", self.skill)
        self.assertIn("push未完了として後続レビューへ進まず停止", self.skill)

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
