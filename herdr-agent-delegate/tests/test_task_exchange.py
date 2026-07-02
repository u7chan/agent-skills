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
        self.assertIn(f"--reply-file {task_dir / 'result.md'}", task_text)
        self.assertNotIn("<result-file>", task_text)
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

    def test_only_one_concurrent_complete_succeeds(self):
        exchange = self.create()
        task_dir = Path(exchange["task_dir"])
        result_files = []
        for index in range(2):
            result_file = Path(self.temporary.name) / f"result-{index}.md"
            result_file.write_text(f"result {index}\n", encoding="utf-8")
            result_files.append(result_file)

        processes = [
            subprocess.Popen(
                [
                    sys.executable,
                    str(SCRIPT),
                    "complete",
                    "--task-dir",
                    str(task_dir),
                    "--reply-file",
                    str(result_file),
                ],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for result_file in result_files
        ]
        results = [process.communicate() for process in processes]

        self.assertEqual(sorted(process.returncode for process in processes), [0, 1])
        self.assertIn((task_dir / "reply.md").read_text(encoding="utf-8"), {"result 0\n", "result 1\n"})
        self.assertEqual(sum(exchange["marker"] in stdout for stdout, _ in results), 1)


if __name__ == "__main__":
    unittest.main()
