import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IssueCreationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        template = re.search(
            r"```markdown\n(.*?)\n```", cls.skill, flags=re.DOTALL
        )
        assert template is not None
        cls.issue_body_template = template.group(1)

    def test_issue_body_ends_with_english_metadata_heading(self):
        sections = re.split(r"^## ", self.issue_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))
        self.assertIn("| Role | Agent | Model | Effort |", sections[-1])
        self.assertNotIn("AI作業メタ情報", self.skill)

    def test_parent_compares_pre_and_post_delegation_snapshots(self):
        for command in (
            "git status --short",
            "git rev-parse HEAD",
            "git ls-remote --heads",
            "gh issue list --author @me --state all",
            "gh pr list --author @me --state all",
            "--limit 1000 --json number,url",
        ):
            self.assertIn(command, self.skill)

        self.assertIn("送信前スナップショットと完全一致", self.skill)
        self.assertIn("今回のIssue 1件だけ", self.skill)
        self.assertIn("PR作成を検出していない", self.skill)

    def test_forbidden_operations_fail_closed_and_keep_pane(self):
        self.assertIn("herdr pane read --source recent-unwrapped", self.skill)
        self.assertIn("出力が欠ける、判定できない", self.skill)
        self.assertIn("禁止操作の検出、スナップショット不一致、確認不能", self.skill)
        self.assertIn("paneを診断用に保持して停止", self.skill)
        for operation in (
            "HTML生成",
            "再委譲",
            "commit",
            "push",
            "PR作成",
        ):
            self.assertIn(operation, self.skill)


if __name__ == "__main__":
    unittest.main()
