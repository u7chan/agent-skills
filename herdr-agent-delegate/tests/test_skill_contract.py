import unittest
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
PARENT_SKILL_ROOT = ROOT.parent / "herdr-github-implement-pr"


class SkillContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.reference = (ROOT / "references" / "agent-cli.md").read_text(
            encoding="utf-8"
        )

    def test_foreground_idle_and_background_done_are_both_complete(self):
        for text in (self.skill, self.reference):
            self.assertIn("foreground", text)
            self.assertIn("idle", text)
            self.assertIn("done", text)
            self.assertIn("双方を完了扱い", text)

    def run_completion_contract(self, *, focused, final_status, wait_rc=0):
        match = re.search(
            r"<!-- completion-wait-contract:start -->\s*```bash\n(.*?)\n```\s*"
            r"<!-- completion-wait-contract:end -->",
            self.skill,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        script = match.group(1).replace('"<pane-id>"', '"w1:p2"')

        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            fake_herdr = temporary_path / "herdr"
            log_path = temporary_path / "wait.log"
            fake_herdr.write_text(
                """#!/bin/sh
if [ "$1 $2" = "pane get" ]; then
  printf '{"result":{"pane":{"tab_id":"w1:t1","agent_status":"%s"}}}\\n' "$FINAL_STATUS"
elif [ "$1 $2" = "tab list" ]; then
  printf '{"result":{"tabs":[{"tab_id":"w1:t1","focused":%s}]}}\\n' "$TAB_FOCUSED"
elif [ "$1 $2" = "wait agent-status" ]; then
  printf '%s\\n' "$*" > "$WAIT_LOG"
  exit "$WAIT_RC"
else
  exit 2
fi
""",
                encoding="utf-8",
            )
            fake_herdr.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{temporary}{os.pathsep}{env['PATH']}",
                    "FINAL_STATUS": final_status,
                    "TAB_FOCUSED": str(focused).lower(),
                    "WAIT_LOG": str(log_path),
                    "WAIT_RC": str(wait_rc),
                }
            )
            result = subprocess.run(["bash", "-c", script], env=env, check=False)
            wait_command = log_path.read_text(encoding="utf-8")
            return result.returncode, wait_command

    def test_foreground_completion_waits_for_idle(self):
        returncode, wait_command = self.run_completion_contract(
            focused=True, final_status="idle"
        )
        self.assertEqual(returncode, 0)
        self.assertIn("--status idle", wait_command)

    def test_background_completion_waits_for_done(self):
        returncode, wait_command = self.run_completion_contract(
            focused=False, final_status="done"
        )
        self.assertEqual(returncode, 0)
        self.assertIn("--status done", wait_command)

    def test_final_idle_is_accepted_after_wait_timeout(self):
        returncode, _ = self.run_completion_contract(
            focused=False, final_status="idle", wait_rc=124
        )
        self.assertEqual(returncode, 0)

    def test_final_working_is_not_complete(self):
        returncode, _ = self.run_completion_contract(
            focused=False, final_status="working"
        )
        self.assertNotEqual(returncode, 0)

    def test_official_primitives_are_used_directly(self):
        self.assertIn("herdr pane run", self.skill)
        self.assertIn("herdr wait agent-status", self.skill)
        self.assertIn("herdr pane read", self.skill)
        removed_scripts = ["wait_for_" + "completion.py", "task_" + "exchange.py"]
        for name in removed_scripts:
            self.assertNotIn(name, self.skill)
            self.assertFalse((ROOT / "scripts" / name).exists())

    def test_removed_environment_variables_are_not_documented(self):
        prefix = "HERDR" + "_DELEGATE_"
        suffixes = (
            "GRID_COLUMNS",
            "MIN_PANE_WIDTH",
            "MIN_PANE_HEIGHT",
            "AUTO_DEDICATED_TAB",
            "MAX_PANES_PER_TAB",
        )
        for name in (prefix + suffix for suffix in suffixes):
            self.assertNotIn(name, self.skill)

    def test_parent_skill_does_not_restore_file_exchange_contract(self):
        parent_documents = (
            PARENT_SKILL_ROOT / "SKILL.md",
            PARENT_SKILL_ROOT / "references" / "implementation-delegation.md",
            PARENT_SKILL_ROOT / "references" / "review-loop.md",
        )
        removed_terms = ("reply_" + "missing", "task directory", "collect")
        for document in parent_documents:
            text = document.read_text(encoding="utf-8")
            self.assertIn("pane", text)
            for term in removed_terms:
                self.assertNotIn(term, text)
