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
        ):
            self.assertIn(requirement, self.skill)

    def test_doctor_retry_only_communication_errors(self):
        self.assertIn("モデル一覧取得や通信の一過性", self.skill)
        self.assertIn("設定・認証・非互換エラーは即停止", self.skill)
        self.assertIn("最大2回", self.skill)
        self.assertIn("dry-runや直接CLI fallbackは禁止", self.skill)

    def test_handoff_returns_kind_and_native_args(self):
        for name in (
            "agent-kind",
            "native-agent-args",
            "agent-command",
            "delegation-metadata",
        ):
            self.assertIn(name, self.skill)
        self.assertIn("herdr agent start", self.skill)
        self.assertIn("--kind", self.skill)
        self.assertIn("JSON配列", self.skill)
        self.assertIn("1値でも欠ける", self.skill)
        self.assertIn("全体を`null`", self.skill)

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
