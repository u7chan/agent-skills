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

    def test_agent_resolution_matches_cagent_priority(self):
        self.assertIn("`--agent` を省略", self.skill)
        priority = "`ユーザー明示の --agent > CAGENT_AGENT > config.default_agent`"
        self.assertIn(priority, self.skill)
        self.assertIn("この優先順位で選んだ同じagent ID", self.skill)

    def test_defaults_are_selected_by_omission(self):
        self.assertIn("`default_agent`", self.skill)
        self.assertIn("levelを省略して `default_level`", self.skill)

    def test_preflight_failures_do_not_fallback(self):
        for requirement in (
            "HERDR_ENV=1",
            "HERDR_PANE_ID",
            "command -v cagent",
            "cagent --help",
            "cagent doctor",
            "直接起動して回避しない",
        ):
            self.assertIn(requirement, self.skill)

    def test_preflight_rejects_incompatible_or_unresolvable_cagent(self):
        for capability in (
            "rootの対話起動",
            "`--dry-run`",
            "`--agent`",
            "`--model`",
            "`--effort`",
            "任意のlevel位置引数",
        ):
            self.assertIn(capability, self.skill)

        self.assertIn("cagent --agent <agent> doctor", self.skill)
        self.assertIn("同じagent / model / effort / level", self.skill)
        self.assertIn("選択対象Agentのbin不在", self.skill)
        self.assertIn("Agent CLIやpaneを起動せず", self.skill)

    def test_normal_flow_uses_only_interactive_cagent_command(self):
        self.assertIn("cagent [--agent <agent>]", self.skill)
        for forbidden in ("cagent " + "run", "cagent " + "mux"):
            occurrences = [
                line
                for line in self.skill.splitlines()
                if forbidden in line and "使わない" not in line
            ]
            self.assertEqual([], occurrences)

    def test_handoff_separates_agent_type_from_command(self):
        self.assertIn("base-agent-type", self.skill)
        self.assertIn("agent-command", self.skill)
        self.assertIn("ラッパー名 `cagent`", self.skill)
        self.assertIn("Agent表示名が必要な後続処理", self.skill)
        self.assertIn("cagent agent IDやpane・役割識別子を渡さない", self.skill)

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
        self.assertIn("呼び出し側が持つ", self.skill)


if __name__ == "__main__":
    unittest.main()
