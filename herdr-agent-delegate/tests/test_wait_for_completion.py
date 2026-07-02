import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "wait_for_completion.py"
SPEC = importlib.util.spec_from_file_location("wait_for_completion", MODULE_PATH)
waiter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(waiter)


class Result:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.stdout = ""
        self.stderr = ""


class WaitForCompletionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.reply = Path(self.temporary.name) / "reply.md"

    def tearDown(self):
        self.temporary.cleanup()

    def args(self, **values):
        defaults = {
            "target": "w1:p2",
            "reply_path": str(self.reply),
            "timeout": 1_000,
            "poll_interval": 10,
            "marker": "DONE_123",
        }
        defaults.update(values)
        return Namespace(**defaults)

    def test_semantic_wait_completes_after_working(self):
        self.reply.write_text("done\n", encoding="utf-8")
        with patch.object(waiter, "agent_status", side_effect=["working"]), patch.object(
            waiter, "run_herdr", return_value=Result()
        ):
            self.assertEqual(waiter.wait_semantic(self.args()), 0)

    def test_semantic_wait_reports_blocked(self):
        with patch.object(waiter, "agent_status", return_value="blocked"):
            self.assertEqual(waiter.wait_semantic(self.args()), 2)

    def test_semantic_wait_does_not_accept_reply_while_blocked(self):
        self.reply.write_text("partial\n", encoding="utf-8")
        with patch.object(waiter, "agent_status", return_value="blocked"):
            self.assertEqual(waiter.wait_semantic(self.args()), 2)

    def test_marker_requires_reply_after_match(self):
        with patch.object(waiter, "run_herdr", return_value=Result()):
            self.assertEqual(waiter.wait_marker(self.args()), 4)

    def test_marker_completes_with_reply(self):
        self.reply.write_text("done\n", encoding="utf-8")
        with patch.object(waiter, "run_herdr", return_value=Result()):
            self.assertEqual(waiter.wait_marker(self.args()), 0)


if __name__ == "__main__":
    unittest.main()
