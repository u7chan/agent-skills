import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "wait_for_input_ready.py"
SPEC = importlib.util.spec_from_file_location("wait_for_input_ready", MODULE_PATH)
readiness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(readiness)


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class WaitForInputReadyTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.task_dir = Path(self.temporary.name) / "task"
        self.task_dir.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def args(self, agent="codex"):
        return Namespace(target="w1:p2", agent=agent, task_dir=str(self.task_dir),
                         timeout=1_000, lines=80)

    def test_semantic_idle_does_not_trigger_notice_or_enter(self):
        results = [Result(returncode=1), Result(stdout="agent_status: idle\n")]
        with patch.object(readiness, "run_herdr", side_effect=results) as run:
            self.assertEqual(readiness.wait_for_input_ready(self.args()), 2)
        self.assertEqual(run.call_count, 2)
        self.assertNotIn("agent-status", str(run.call_args_list))
        self.assertNotIn("send", str(run.call_args_list))
        self.assertTrue((self.task_dir / "input_readiness.diagnostics.json").is_file())

    def test_delayed_codex_tui_requires_wait_and_read_confirmation(self):
        results = [Result(stdout="matched"), Result(stdout="Codex\n\n› Ask for changes\n")]
        with patch.object(readiness, "run_herdr", side_effect=results) as run:
            self.assertEqual(readiness.wait_for_input_ready(self.args()), 0)
        self.assertEqual(run.call_args_list[0].args[0][:2], ["wait", "output"])
        self.assertEqual(run.call_args_list[1].args[0][:2], ["pane", "read"])

    def test_wait_match_without_prompt_in_readback_fails(self):
        results = [Result(stdout="matched"), Result(stdout="Codex is still starting\n")]
        with patch.object(readiness, "run_herdr", side_effect=results):
            self.assertEqual(readiness.wait_for_input_ready(self.args()), 2)

    def test_agent_specific_ready_signatures(self):
        outputs = {"claude": "❯ ", "opencode": "Build · Model  ctrl+p commands"}
        for agent, output in outputs.items():
            with self.subTest(agent=agent), patch.object(
                readiness, "run_herdr", side_effect=[Result(), Result(stdout=output)]
            ):
                self.assertEqual(readiness.wait_for_input_ready(self.args(agent)), 0)


if __name__ == "__main__":
    unittest.main()
