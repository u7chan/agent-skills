#!/usr/bin/env python3
"""Tests for herdr-agent-delegate/scripts/build_prompt.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

import build_prompt


class BuildPromptTest(unittest.TestCase):
    def test_no_metadata_returns_prompt_unchanged(self):
        result = build_prompt.build_prompt("hello world", None)
        self.assertEqual(result, "hello world")

    def test_complete_metadata_appends_suffix_once(self):
        metadata = {"agent": "Codex", "model": "gpt-5.6-sol", "effort": "high"}
        result = build_prompt.build_prompt("do task", metadata)
        self.assertTrue(result.startswith("do task\n\n"))
        self.assertEqual(result.count("<herdr-delegation-metadata>"), 1)
        self.assertEqual(result.count("</herdr-delegation-metadata>"), 1)
        payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
        self.assertIn(payload, result)

    def test_validate_rejects_missing_key(self):
        for invalid in (
            '{"agent":"Codex","model":"gpt"}',
            '{"agent":"Codex","effort":"high"}',
            '{"model":"gpt","effort":"high"}',
        ):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    build_prompt.validate_metadata(invalid)

    def test_validate_rejects_extra_key(self):
        with self.assertRaises(ValueError):
            build_prompt.validate_metadata(
                '{"agent":"C","model":"M","effort":"E","extra":1}'
            )

    def test_validate_rejects_empty_value(self):
        with self.assertRaises(ValueError):
            build_prompt.validate_metadata(
                '{"agent":"C","model":"M","effort":""}'
            )

    def test_validate_rejects_em_dash(self):
        for key in build_prompt.METADATA_KEYS:
            md = {"agent": "C", "model": "M", "effort": "E"}
            md[key] = "\u2014"
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    build_prompt.validate_metadata(json.dumps(md))

    def test_validate_rejects_non_json(self):
        with self.assertRaises(json.JSONDecodeError):
            build_prompt.validate_metadata("not json")

    def test_metadata_prompt_rstrip_safe(self):
        metadata = {"agent": "Codex", "model": "gpt-5.6-sol", "effort": "high"}
        result = build_prompt.build_prompt("task\n\n", metadata)
        self.assertTrue(result.startswith("task"))
        self.assertEqual(result.count("<herdr-delegation-metadata>"), 1)

    def test_herdr_env_alone_does_not_create_metadata(self):
        result = build_prompt.build_prompt("task", None)
        self.assertEqual(result, "task")

    def test_newlines_preserved_in_prompt(self):
        metadata = {"agent": "C", "model": "M", "effort": "E"}
        prompt = "line1\n\nline2\nline3"
        result = build_prompt.build_prompt(prompt, metadata)
        self.assertTrue(result.startswith("line1\n\nline2\nline3\n\n"))

    def test_single_quotes_preserved_in_prompt(self):
        metadata = {"agent": "C", "model": "M", "effort": "E"}
        prompt = "it's a 'test' with quotes"
        result = build_prompt.build_prompt(prompt, metadata)
        self.assertIn("it's a 'test' with quotes", result)

    def test_unicode_preserved_in_prompt(self):
        metadata = {"agent": "C", "model": "M", "effort": "E"}
        prompt = "日本語テスト \U0001f600"
        result = build_prompt.build_prompt(prompt, metadata)
        self.assertIn("日本語テスト", result)
        self.assertIn("\U0001f600", result)

    def test_prompt_file_reads_correctly(self):
        import importlib.util, io

        metadata = {"agent": "C", "model": "M", "effort": "E"}
        prompt_content = "from file\nline2"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(prompt_content)
        import subprocess, os
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_prompt.py"),
                    "--prompt-file", f.name,
                    "--metadata-json", json.dumps(metadata),
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn(prompt_content, proc.stdout)
            self.assertIn("<herdr-delegation-metadata>", proc.stdout)
        finally:
            os.unlink(f.name)


    def test_prompt_file_takes_priority_over_prompt(self):
        import subprocess, sys, os
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("from file")
        try:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_prompt.py"),
                 "--prompt-file", f.name, "--prompt", "from arg"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("from file", proc.stdout)
            self.assertNotIn("from arg", proc.stdout)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
