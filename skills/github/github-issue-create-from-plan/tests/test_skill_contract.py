import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.openai_yaml = (ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

    def test_short_description_matches_current_issue_creation_scope(self):
        match = re.search(r'short_description: "(?P<value>.*)"', self.openai_yaml)
        self.assertIsNotNone(match)
        description = match.group("value")

        self.assertEqual(
            "確定済みプランからGitHub Issueを作成・確認する", description
        )
        self.assertNotIn("HTML", description)


if __name__ == "__main__":
    unittest.main()
