import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class AiWorkMetadataContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.delegation = (
            ROOT / "references" / "implementation-delegation.md"
        ).read_text(encoding="utf-8")
        cls.review_loop = (ROOT / "references" / "review-loop.md").read_text(
            encoding="utf-8"
        )
        cls.pr_template = (ROOT / "references" / "pr-template.md").read_text(
            encoding="utf-8"
        )
        template = re.search(r"```markdown\n(.*?)\n```", cls.pr_template, re.DOTALL)
        assert template is not None
        cls.pr_body_template = template.group(1)

    def test_template_uses_only_metadata_backed_rows(self):
        sections = re.split(r"^## ", self.pr_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))
        metadata = sections[-1]
        self.assertIn("| Role | Agent | Model | Effort |", metadata)
        self.assertIn("<metadata-backed role>", metadata)
        self.assertNotIn("| オーケストレーター |", metadata)

    def test_root_without_delegation_metadata_has_no_row(self):
        for text in (self.skill, self.delegation):
            self.assertIn("標準suffix", text)
            self.assertIn("root", text)
            self.assertRegex(text, r"行[をは].*作らない")

    def test_partial_and_inferred_values_are_forbidden(self):
        for text in (self.skill, self.delegation):
            self.assertIn("—", text)
            self.assertIn("補完", text)
        self.assertIn("1値でも欠ける役割には行を作らない", self.delegation)
        self.assertIn("Codex Config", self.delegation)

    def test_recheck_reuses_original_snapshot_only(self):
        self.assertIn("cagent-agent-command-resolve", self.skill)
        self.assertIn("固定済み`agent-kind`・`native-agent-args`", self.delegation)
        self.assertIn("初回起動時の同じsnapshotを再送", self.review_loop)
        self.assertIn("出自不明の再利用paneならメタ情報を送らない", self.review_loop)
        self.assertIn("親の値を転用しない", self.review_loop)

    def test_repeated_feedback_uses_fresh_codex_high_session_by_default(self):
        self.assertIn("前回のFB Agent・pane・sessionを再利用せず", self.review_loop)
        self.assertIn("`agent=codex`、task level=`high`", self.review_loop)
        self.assertIn("fb-pr-<number>-r<round>", self.review_loop)
        self.assertIn("ユーザーが次FB担当のAgentまたはtask levelを明示", self.review_loop)


if __name__ == "__main__":
    unittest.main()
