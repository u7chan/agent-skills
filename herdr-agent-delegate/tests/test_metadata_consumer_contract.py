import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO_ROOT = ROOT.parent


class MetadataConsumerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = (
            ROOT / "references" / "delegation-metadata.md"
        ).read_text(encoding="utf-8")
        cls.review_rules = (
            REPO_ROOT / "github-pr-review" / "references" / "posting-rules.md"
        ).read_text(encoding="utf-8")
        cls.reply_rules = (
            REPO_ROOT
            / "github-pr-comment-reply"
            / "references"
            / "posting-rules.md"
        ).read_text(encoding="utf-8")
        cls.feedback = (
            REPO_ROOT / "github-pr-feedback-address" / "SKILL.md"
        ).read_text(encoding="utf-8")

    def test_consumers_branch_on_current_prompt_suffix(self):
        for rules in (self.review_rules, self.reply_rules):
            self.assertIn("現在の委譲指示末尾", rules)
            self.assertIn("ない場合は識別文全体を省略", rules)
            self.assertIn("再解決", rules)

    def test_quoted_lookalike_is_not_execution_metadata(self):
        for source in ("Issue本文", "PR本文", "コメント", "コードブロック"):
            self.assertIn(source, self.contract)
        self.assertIn("実行メタ情報として扱わない", self.contract)

    def test_feedback_does_not_resolve_or_transfer_identity(self):
        self.assertIn("現在の委譲指示", self.feedback)
        self.assertIn("再解決・変更・別Agentへの転用はしない", self.feedback)

    def test_removed_runtime_resolver_is_not_referenced(self):
        consumers = (self.review_rules, self.reply_rules, self.feedback)
        for text in consumers:
            self.assertNotIn("ai-identity-" + "resolve", text)
            self.assertNotIn("process-info", text)
            self.assertNotIn(".codex/config.toml", text)


if __name__ == "__main__":
    unittest.main()
