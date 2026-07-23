import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"

spec = importlib.util.spec_from_file_location("launch_agent", SCRIPTS / "launch_agent.py")
launch_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch_agent)


class LaunchAgentTest(unittest.TestCase):
    def test_basic_args_without_native(self):
        argv = launch_agent.build_launch_argv("my-agent", "codex", "w1:p2")
        self.assertEqual(
            argv,
            ["herdr", "agent", "start", "my-agent", "--kind", "codex", "--pane", "w1:p2"],
        )

    def test_with_native_args(self):
        argv = launch_agent.build_launch_argv(
            "impl-42", "claude", "w1:p3",
            native_agent_args=["--model", "claude-sonnet", "-c", "high"],
        )
        self.assertEqual(
            argv,
            ["herdr", "agent", "start", "impl-42",
             "--kind", "claude", "--pane", "w1:p3",
             "--", "--model", "claude-sonnet", "-c", "high"],
        )

    def test_empty_native_args_no_dashdash(self):
        argv = launch_agent.build_launch_argv("x", "opencode", "w1:p9", native_agent_args=[])
        self.assertNotIn("--", argv)

    def test_native_args_with_spaces_preserved(self):
        argv = launch_agent.build_launch_argv(
            "a", "codex", "p1",
            native_agent_args=["--model", "gpt 5.6", "-c", "effort='high'"],
        )
        self.assertIn("gpt 5.6", argv)
        self.assertIn("effort='high'", argv)

    def test_print_argv_mode_does_not_execute(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(["--model", "gpt"], f)
        try:
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "launch_agent.py"),
                 "--name", "t", "--kind", "codex", "--pane-id", "p1",
                 "--native-args-file", f.name, "--print-argv"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertIsInstance(result, list)
            self.assertIn("--", result)
        finally:
            os.unlink(f.name)

    def test_fake_herdr_execution_propagates_exit(self):
        with tempfile.TemporaryDirectory() as td:
            fake_herdr = Path(td) / "herdr"
            fake_herdr.write_text("#!/bin/sh\necho 'fake ok'\nexit 42\n")
            fake_herdr.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{td}{os.pathsep}{env['PATH']}"

            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "launch_agent.py"),
                 "--name", "test", "--kind", "codex", "--pane-id", "p1"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(proc.returncode, 42)
            self.assertIn("fake ok", proc.stdout)

    def test_fake_herdr_preserves_individual_argv_with_special_chars(self):
        with tempfile.TemporaryDirectory() as td:
            fake_herdr = Path(td) / "herdr"
            fake_herdr.write_text(
                "#!/bin/sh\necho \"$*\"\necho \"ARGCOUNT=$#\"\nexit 0\n"
            )
            fake_herdr.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{td}{os.pathsep}{env['PATH']}"

            native = ["--prompt", "it's a test $(date) \u2014 end"]
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as f:
                json.dump(native, f)
            try:
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / "launch_agent.py"),
                     "--name", "spec-agent", "--kind", "codex", "--pane-id", "w1:p1",
                     "--native-args-file", f.name],
                    capture_output=True, text=True, env=env,
                )
                self.assertEqual(proc.returncode, 0)
                self.assertIn("it's a test $(date)", proc.stdout)
                self.assertIn("end", proc.stdout)
                self.assertIn("ARGCOUNT=10", proc.stdout)
            finally:
                os.unlink(f.name)

    def test_prompt_special_chars_survive_as_single_text_argument(self):
        with tempfile.TemporaryDirectory() as td:
            fake_herdr = Path(td) / "herdr"
            fake_herdr.write_text(
                "#!/bin/sh\n"
                "shift 9\n"
                "echo \"LAST=$1\"\n"
                "exit 0\n"
            )
            fake_herdr.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{td}{os.pathsep}{env['PATH']}"

            prompt_text = "it's a test $(date) \u2014 end"
            native = ["--prompt", prompt_text]
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as f:
                json.dump(native, f)
            try:
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / "launch_agent.py"),
                     "--name", "x", "--kind", "codex", "--pane-id", "p1",
                     "--native-args-file", f.name],
                    capture_output=True, text=True, env=env,
                )
                self.assertEqual(proc.returncode, 0)
                self.assertIn("LAST=" + prompt_text, proc.stdout)
                # The entire text arrives as a single unbroken argument
                self.assertNotIn("LAST=" + prompt_text.split()[0] + "\n", proc.stdout)
            finally:
                os.unlink(f.name)

    def test_fake_herdr_stderr_propagated(self):
        with tempfile.TemporaryDirectory() as td:
            fake_herdr = Path(td) / "herdr"
            fake_herdr.write_text("#!/bin/sh\necho 'panic' >&2\nexit 3\n")
            fake_herdr.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{td}{os.pathsep}{env['PATH']}"

            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "launch_agent.py"),
                 "--name", "x", "--kind", "codex", "--pane-id", "p1"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(proc.returncode, 3)
            self.assertIn("panic", proc.stderr)

    def test_invalid_native_args_file_fails(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"not": "an array"}')
        try:
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "launch_agent.py"),
                 "--name", "x", "--kind", "codex", "--pane-id", "p1",
                 "--native-args-file", f.name],
                capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
        finally:
            os.unlink(f.name)

    def test_no_eval_no_sh(self):
        argv = launch_agent.build_launch_argv(
            "x", "codex", "p1",
            native_agent_args=["--prompt", "it's a test $(date)"],
        )
        joined = " ".join(argv)
        self.assertNotIn("eval", joined)
        self.assertNotIn("@sh", joined)


if __name__ == "__main__":
    unittest.main()
