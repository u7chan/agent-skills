import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_user_values_have_highest_priority(self):
        self.assertIn("ユーザーが明示", self.skill)
        self.assertIn("ユーザー指定をコスト最適化や独自判断で変更しない", self.skill)
        for name in ("agent", "level", "model", "effort"):
            self.assertIn(name, self.skill)

    def test_preflight_resolves_then_verifies_fixed_command(self):
        for requirement in (
            "HERDR_ENV=1",
            "cagent doctor",
            "初回`cagent ... --dry-run`",
            "freeze_resolution.py",
            "Agent CLI、Model、Effortが一致した`verified: true`",
            "直接CLIへfallbackせず停止",
        ):
            self.assertIn(requirement, self.skill)

    def test_handoff_separates_runtime_and_metadata_values(self):
        for name in (
            "base-agent-type",
            "resolved",
            "agent-command",
            "delegation-metadata",
        ):
            self.assertIn(name, self.skill)
        self.assertIn("1値でも欠ける", self.skill)
        self.assertIn("全体を`null`", self.skill)
        self.assertIn("Codex Config fallbackを使わない", self.skill)

    def test_agent_execution_is_out_of_scope(self):
        for responsibility in (
            "paneの作成・分割・操作",
            "Agent CLIの起動",
            "readiness確認",
            "依頼送信",
            "完了待機",
            "出力回収",
            "cleanup",
        ):
            self.assertIn(responsibility, self.skill)


if __name__ == "__main__":
    unittest.main()
