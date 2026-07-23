import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PARENT_SKILL_ROOT = ROOT.parent / "herdr-github-pr-orchestrate"


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.reference = (ROOT / "references" / "agent-cli.md").read_text(
            encoding="utf-8"
        )

    def _texts(self):
        return (self.skill, self.reference)

    def test_agent_start_via_launcher_subprocess(self):
        self.assertIn("launch_agent.py", self.skill)
        self.assertIn("subprocess.run", self.skill)
        self.assertIn("exit/stdout/stderr", self.skill)
        self.assertIn("--print-argv", self.skill)
        self.assertTrue((ROOT / "scripts" / "launch_agent.py").exists())

    def test_agent_name_constraint(self):
        self.assertIn("[a-z][a-z0-9_-]", self.skill)
        self.assertIn("{0,31}", self.skill)

    def test_agent_prompt_arg_order(self):
        self.assertIn("--wait --until working --timeout 30000", self.skill)

    def test_prompt_double_quote_not_single(self):
        self.assertIn("BUILT=", self.skill)
        self.assertIn('"$BUILT"', self.skill)
        self.assertIn("単一引用符直接禁止", self.skill)

    def test_prompt_uses_temp_file(self):
        for text in self._texts():
            self.assertIn("--prompt-file", text)

    def test_agent_wait_timeout_only(self):
        self.assertIn("--timeout 1800000", self.skill)
        self.assertIn("本フローでは", self.skill)

    def test_agent_get_for_final_status(self):
        self.assertIn("herdr agent get", self.skill)
        self.assertNotIn("herdr pane get <target>", self.skill)

    def test_layout_planner_stdin_envelope(self):
        self.assertIn("layout_planner.py", self.skill)
        self.assertIn("herdr pane layout --pane", self.skill)
        self.assertIn("envelope", self.skill.lower())
        self.assertIn("--pane <root-pane-id>", self.skill)

    def test_layout_new_tab_transition_flow(self):
        self.assertIn("tab create", self.skill)
        self.assertIn("root_pane.pane_id", self.skill)
        self.assertIn("child_ids", self.skill)
        self.assertIn("リセット", self.skill)

    def test_layout_split_directions(self):
        self.assertIn("子1=右", self.skill)
        self.assertIn("子2=下", self.skill)
        self.assertIn("子3=右", self.skill)

    def test_agent_kind_native_args(self):
        for text in self._texts():
            self.assertIn("agent-kind", text)
            self.assertIn("native-agent-args", text)

    def test_metadata_validation(self):
        for text in self._texts():
            self.assertIn("3キー", text)
            self.assertIn("—", text)

    def test_old_apis_prohibited(self):
        self.assertIn("herdr pane run` でAgent", self.skill)
        self.assertIn("herdr wait agent-status`(旧API)", self.skill)
        self.assertNotIn("send_request.py", self.skill)

    def test_scripts_exist(self):
        for name in ("build_prompt.py", "layout_planner.py", "launch_agent.py"):
            p = ROOT / "scripts" / name
            self.assertTrue(p.exists(), f"{name} missing")
            self.assertTrue(p.stat().st_mode & 0o111, f"{name} not executable")

    def test_removed_scripts_not_referenced(self):
        removed = ("send_request.py", "wait_for_input_ready.py",
                   "split_scoped_pane.py", "choose_layout.py")
        for name in removed:
            for text in self._texts():
                self.assertNotIn(name, text)
            self.assertFalse((ROOT / "scripts" / name).exists())

    def test_parallel_and_nesting(self):
        self.assertIn("ネスト・並列委譲", self.skill)
        self.assertIn("直下子", self.skill)

    def test_one_pane_one_agent(self):
        self.assertIn("1 pane=1 agent", self.skill)

    def test_ids_not_cached(self):
        self.assertIn("キャッシュ", self.skill)

    def test_large_output_saved(self):
        self.assertIn("ファイル保存", self.skill)

    def test_max_four_includes_parent(self):
        self.assertIn("root込み", self.skill)

    def test_no_focus_pane_only(self):
        self.assertIn("--no-focus", self.skill)
        self.assertIn("配置", self.reference)
        self.assertIn("`agent start` に追加不可", self.reference)


if __name__ == "__main__":
    unittest.main()
