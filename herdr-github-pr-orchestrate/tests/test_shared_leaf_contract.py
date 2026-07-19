import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SharedLeafContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.delegation = (
            ROOT / "references" / "implementation-delegation.md"
        ).read_text(encoding="utf-8")

    def test_herdr_flow_keeps_its_specific_contracts(self):
        for term in (
            "herdr-agent-delegate",
            "cagent-agent-command-resolve",
            "AI Work Metadata",
            "最大 3 回",
            "同一指摘が 2 回連続",
        ):
            self.assertIn(term, self.skill)

    def test_trigger_description_remains_herdr_specific(self):
        frontmatter = self.skill.split("---", 2)[1]
        self.assertIn("Herdr Agentへの実装委譲", frontmatter)
        self.assertIn("pane配置", frontmatter)

    def test_commit_and_pr_creation_use_shared_leaf_skills(self):
        for text in (self.skill, self.delegation):
            self.assertIn("git-changes-commit/SKILL.md", text)
            self.assertIn("github-pr-create/SKILL.md", text)
        self.assertIn("共通手順を再定義しない", self.skill)

    def test_herdr_contract_does_not_embed_leaf_commands(self):
        for text in (self.skill, self.delegation):
            self.assertNotIn("`git add --", text)
            self.assertNotIn("`git commit ", text)
            self.assertNotIn("`git push", text)
            self.assertNotIn("`gh pr create", text)


if __name__ == "__main__":
    unittest.main()
