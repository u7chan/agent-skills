"""Verify the documented ``BUILT`` prompt path through a fake Herdr."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD_PROMPT = ROOT / "scripts" / "build_prompt.py"


class AgentPromptIntegrationTest(unittest.TestCase):
    def _run_documented_prompt_flow(
        self,
        prompt_text: str,
        metadata: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        """Build ``BUILT``, invoke fake Herdr, and return its recorded argv."""
        with tempfile.TemporaryDirectory() as temporary:
            temp_dir = Path(temporary)
            fake_herdr = temp_dir / "herdr"
            prompt_file = temp_dir / "prompt.txt"
            built_file = temp_dir / "built.txt"
            argv_log = temp_dir / "argv.json"

            fake_herdr.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "import os\n"
                "import sys\n"
                "with open(os.environ['HERDR_ARGV_LOG'], 'w', encoding='utf-8') as fh:\n"
                "    json.dump(sys.argv[1:], fh, ensure_ascii=False)\n",
                encoding="utf-8",
            )
            fake_herdr.chmod(0o755)
            prompt_file.write_text(prompt_text, encoding="utf-8")

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{temporary}{os.pathsep}{env['PATH']}",
                    "HERDR_ARGV_LOG": str(argv_log),
                    "PROMPT_BUILDER": str(BUILD_PROMPT),
                    "PROMPT_FILE": str(prompt_file),
                    "BUILT_FILE": str(built_file),
                    "PYTHON_BIN": sys.executable,
                }
            )
            metadata_args = ""
            if metadata is not None:
                env["METADATA_JSON"] = json.dumps(metadata, ensure_ascii=False)
                metadata_args = ' --metadata-json "$METADATA_JSON"'

            script = (
                '"$PYTHON_BIN" "$PROMPT_BUILDER" --prompt-file "$PROMPT_FILE"'
                f'{metadata_args} > "$BUILT_FILE"\n'
                'BUILT="$(cat "$BUILT_FILE")"\n'
                'herdr agent prompt "TARGET TEXT" "$BUILT" '
                '--wait --until working --timeout 30000\n'
            )
            proc = subprocess.run(
                ["bash", "-eu", "-c", script],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            recorded_argv = (
                json.loads(argv_log.read_text(encoding="utf-8"))
                if argv_log.exists()
                else []
            )
            return proc, recorded_argv

    def test_simple_prompt_matches_full_argv(self):
        prompt = "fix all bugs"
        proc, recorded_argv = self._run_documented_prompt_flow(prompt)

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            recorded_argv,
            [
                "agent",
                "prompt",
                "TARGET TEXT",
                prompt,
                "--wait",
                "--until",
                "working",
                "--timeout",
                "30000",
            ],
        )

    def test_special_characters_remain_one_built_text_argv(self):
        prompt = (
            "first line\n"
            "it's still one argument\n"
            'literal HOME: "$HOME"\n'
            "literal command substitution: $(printf injected)\n"
            "Unicode: 日本語 — 😀"
        )
        proc, recorded_argv = self._run_documented_prompt_flow(prompt)

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            recorded_argv,
            [
                "agent",
                "prompt",
                "TARGET TEXT",
                prompt,
                "--wait",
                "--until",
                "working",
                "--timeout",
                "30000",
            ],
        )

    def test_metadata_suffix_is_part_of_one_built_text_argv(self):
        prompt = "do task"
        metadata = {
            "agent": "Codex",
            "model": "gpt-5.6-sol",
            "effort": "high",
        }
        proc, recorded_argv = self._run_documented_prompt_flow(prompt, metadata)

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(recorded_argv[:3], ["agent", "prompt", "TARGET TEXT"])
        self.assertEqual(
            recorded_argv[4:],
            ["--wait", "--until", "working", "--timeout", "30000"],
        )
        self.assertIn("<herdr-delegation-metadata>", recorded_argv[3])
        self.assertIn('"agent":"Codex"', recorded_argv[3])


if __name__ == "__main__":
    unittest.main()
