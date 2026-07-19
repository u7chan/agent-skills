import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IssueCreationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        template = re.search(r"```markdown\n(.*?)\n```", cls.skill, re.DOTALL)
        assert template is not None
        cls.issue_body_template = template.group(1)

    def test_metadata_template_has_only_backed_rows(self):
        sections = re.split(r"^## ", self.issue_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))
        self.assertIn("| Role | Agent | Model | Effort |", sections[-1])
        self.assertIn("<metadata-backed role>", sections[-1])
        self.assertNotIn("| 壁打ち |", sections[-1])

    def test_root_without_suffix_has_no_wall_meeting_row(self):
        self.assertIn("Herdr直接起動のrootには作らない", self.skill)
        self.assertIn("行が1件もなければ", self.skill)
        self.assertIn("セクション自体を作らない", self.skill)

    def test_child_metadata_matches_fixed_launch_values(self):
        self.assertIn("同じ3値を明示した`agent-command`", self.skill)
        self.assertIn("同じJSONを`send_request.py --metadata-json`へ渡す", self.skill)
        self.assertIn("標準ブロックは手書きしない", self.skill)

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

    def test_partial_or_fallback_identity_is_forbidden(self):
        for forbidden_contract in (
            "部分行",
            "Codex Config fallback",
            "他役割からの補完",
        ):
            self.assertIn(forbidden_contract, self.skill)

    def test_forbidden_operations_fail_closed_and_keep_pane(self):
        self.assertIn("herdr pane read --source recent-unwrapped", self.skill)
        self.assertIn("paneを診断用に保持して停止", self.skill)
        for operation in ("HTML生成", "再委譲", "commit", "push", "PR作成"):
            self.assertIn(operation, self.skill)


if __name__ == "__main__":
    unittest.main()
