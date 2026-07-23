"""Contract tests for every documented ``launch_agent.py`` consumer."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
LAUNCHER = REPO_ROOT / "herdr-agent-delegate" / "scripts" / "launch_agent.py"
CONSUMERS = (
    (
        REPO_ROOT / "herdr-agent-delegate",
        Path("SKILL.md"),
        "<skill-dir>/scripts/launch_agent.py",
    ),
    (
        REPO_ROOT / "herdr-agent-delegate",
        Path("references/agent-cli.md"),
        "<skill-dir>/scripts/launch_agent.py",
    ),
)


class LauncherConsumerContractTest(unittest.TestCase):
    def test_every_documented_consumer_is_covered(self):
        expected_documents = {
            (skill_dir / document).resolve()
            for skill_dir, document, _ in CONSUMERS
        }
        documented_consumers = {
            document.resolve()
            for document in REPO_ROOT.rglob("*.md")
            if "<skill-dir>/" in document.read_text(encoding="utf-8")
            and "launch_agent.py" in document.read_text(encoding="utf-8")
        }
        self.assertEqual(documented_consumers, expected_documents)

    def test_documented_paths_exist_and_print_expected_argv(self):
        expected_argv = [
            "herdr",
            "agent",
            "start",
            "contract-agent",
            "--kind",
            "codex",
            "--pane",
            "w1:p2",
        ]

        for skill_dir, document, documented_path in CONSUMERS:
            with self.subTest(document=str(skill_dir / document)):
                text = (skill_dir / document).read_text(encoding="utf-8")
                self.assertIn(documented_path, text)
                command_start = text.index(documented_path)
                command_excerpt = text[command_start : command_start + 300]
                self.assertIn("--pane-id", command_excerpt)
                self.assertNotRegex(command_excerpt, r"--pane(?:\s|<)")

                relative_path = documented_path.removeprefix("<skill-dir>/")
                consumer_launcher = (skill_dir / relative_path).resolve()
                self.assertEqual(consumer_launcher, LAUNCHER.resolve())
                self.assertTrue(consumer_launcher.is_file())

                proc = subprocess.run(
                    [
                        sys.executable,
                        str(consumer_launcher),
                        "--name",
                        "contract-agent",
                        "--kind",
                        "codex",
                        "--pane-id",
                        "w1:p2",
                        "--print-argv",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(json.loads(proc.stdout), expected_argv)

    def test_logical_skill_references_replace_cross_skill_launcher_paths(self):
        for path in (
            REPO_ROOT / "cagent-agent-command-resolve" / "SKILL.md",
            REPO_ROOT / "herdr-prompt-evaluate" / "references" / "herdr-execution.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn("`herdr-agent-delegate`", text)
            self.assertNotIn("../herdr-agent-delegate/scripts/launch_agent.py", text)


if __name__ == "__main__":
    unittest.main()
