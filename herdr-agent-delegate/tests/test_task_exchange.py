import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "task_exchange.py"


class TaskExchangeTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "exchange"
        self.env = {**os.environ, "HERDR_AGENT_DELEGATE_ROOT": str(self.root)}
        self.input = Path(self.temporary.name) / "input.md"
        self.input.write_text("調査して結果を返す。\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def run_script(self, *arguments, check=True):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            env=self.env,
            check=check,
            capture_output=True,
            text=True,
        )

    def create(self):
        result = self.run_script("create", "--task-file", str(self.input))
        return json.loads(result.stdout)

    def test_create_complete_collect_and_cleanup(self):
        exchange = self.create()
        task_dir = Path(exchange["task_dir"])
        task_text = Path(exchange["task_path"]).read_text(encoding="utf-8")
        self.assertIn("調査して結果を返す。", task_text)
        self.assertNotIn(exchange["marker"], task_text)
        self.assertEqual(task_dir.stat().st_mode & 0o777, 0o700)

        result_file = Path(self.temporary.name) / "result.md"
        result_file.write_text("# Result\n\n完了\n", encoding="utf-8")
        completed = self.run_script(
            "complete", "--task-dir", str(task_dir), "--reply-file", str(result_file)
        )
        self.assertEqual(completed.stdout.strip(), exchange["marker"])

        collected = self.run_script("collect", "--task-dir", str(task_dir))
        self.assertEqual(collected.stdout, "# Result\n\n完了\n")
        self.assertFalse(task_dir.exists())

    def test_missing_reply_is_retained(self):
        exchange = self.create()
        failed = self.run_script("collect", "--task-dir", exchange["task_dir"], check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(Path(exchange["task_dir"]).exists())

    def test_symlink_reply_is_rejected_and_retained(self):
        exchange = self.create()
        task_dir = Path(exchange["task_dir"])
        (task_dir / "reply.md").symlink_to(self.input)
        failed = self.run_script("collect", "--task-dir", str(task_dir), check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(task_dir.exists())


if __name__ == "__main__":
    unittest.main()
