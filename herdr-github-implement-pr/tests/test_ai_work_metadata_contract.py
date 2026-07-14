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
        template = re.search(
            r"```markdown\n(.*?)\n```", cls.skill, flags=re.DOTALL
        )
        assert template is not None
        cls.pr_body_template = template.group(1)

    def test_pr_body_ends_with_required_metadata_section(self):
        sections = re.split(r"^## ", self.pr_body_template, flags=re.MULTILINE)
        self.assertTrue(sections[-1].startswith("AI Work Metadata\n"))

        metadata_section = sections[-1]
        self.assertIn("| 役割 | Agent | Model | Effort |", metadata_section)
        self.assertIn(
            "| オーケストレーター | `<agent>` | `<model>` | `<effort>` |",
            metadata_section,
        )
        self.assertIn(
            "| 実装 | `<agent>` | `<model>` | `<effort>` |", metadata_section
        )

    def test_optional_roles_and_unknown_values_are_not_inferred(self):
        for text in (self.skill, self.delegation):
            self.assertIn("レビュー", text)
            self.assertIn("レビューFB", text)
            self.assertIn("推測", text)
            self.assertIn("—", text)

        self.assertIn("担当 Agent が会話または解決結果で確定", self.skill)
        self.assertIn("Agent 担当自体が未確定なら行を作らない", self.delegation)

    def test_existing_comment_metadata_is_out_of_scope(self):
        self.assertIn("既存のレビューコメント・FB 対応コメントの AI 識別メタ情報は変更しない", self.skill)
        self.assertIn("既存のレビューコメント・FB 対応コメントの記録方法も変更しない", self.delegation)


if __name__ == "__main__":
    unittest.main()
