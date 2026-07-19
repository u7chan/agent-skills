#!/usr/bin/env python3
"""Tests for herdr-agent-delegate/scripts/send_request.py."""

from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import send_request  # noqa: E402


class SendRequestTest(unittest.TestCase):
    @staticmethod
    def _args(**overrides):
        defaults = {
            "target": "w1Z:pX",
            "agent": "claude",
            "prompt": "long " * 500,
            "metadata": None,
            "timeout": 30_000,
            "activation_timeout": 10_000,
            "activation_text": "実行して",
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _run(self, responses, **overrides):
        """Run send_request with a fake run_herdr that yields each response.

        ``responses`` is an iterable of CompletedProcess instances returned in
        the order ``send_request`` invokes ``run_herdr``.
        """
        response_iter = iter(responses)
        calls = []

        def fake_run_herdr(arguments, timeout=None):
            calls.append(list(arguments))
            return next(response_iter)

        stderr = io.StringIO()
        with patch.object(send_request, "run_herdr", side_effect=fake_run_herdr):
            with patch.object(sys, "stderr", stderr):
                rc = send_request.send_request(self._args(**overrides))
        return rc, stderr.getvalue(), calls

    def test_codex_starts_immediately_without_activation(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="codex",
            prompt="self introduction",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls[0], ["pane", "run", "w1Z:pX", "self introduction"])
        self.assertEqual(calls[1][:2], ["wait", "agent-status"])
        self.assertIn("--timeout", calls[1])
        self.assertNotIn(["pane", "run", "w1Z:pX", "実行して"], calls)

    def test_complete_metadata_is_appended_once_at_prompt_end(self):
        metadata = {
            "agent": "Codex",
            "model": "gpt-5.6-sol",
            "effort": "high",
        }
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="codex",
            prompt="review this",
            metadata=metadata,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        sent = calls[0][3]
        self.assertTrue(sent.startswith("review this\n\n"))
        self.assertEqual(sent.count("<herdr-delegation-metadata>"), 1)
        self.assertIn(
            '{"agent":"Codex","model":"gpt-5.6-sol","effort":"high"}',
            sent,
        )
        self.assertTrue(sent.endswith(send_request.METADATA_INSTRUCTION))

    def test_metadata_is_omitted_when_snapshot_is_absent(self):
        self.assertEqual(send_request.build_prompt("task", None), "task")

    def test_herdr_environment_alone_does_not_create_metadata(self):
        with patch.dict("os.environ", {"HERDR_ENV": "1"}):
            self.assertEqual(send_request.build_prompt("task", None), "task")

    def test_metadata_parser_rejects_partial_or_unknown_values(self):
        invalid = (
            '{"agent":"Codex","model":"gpt-5.6-sol"}',
            '{"agent":"Codex","model":"gpt-5.6-sol","effort":""}',
            '{"agent":"Codex","model":"gpt-5.6-sol","effort":"high","x":1}',
            "not-json",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    send_request.parse_metadata(value)

    def test_metadata_parser_rejects_em_dash_value(self):
        for key in send_request.METADATA_KEYS:
            metadata = {
                "agent": "Codex",
                "model": "gpt-5.6-sol",
                "effort": "high",
            }
            metadata[key] = "—"
            with self.subTest(key=key):
                with self.assertRaises(argparse.ArgumentTypeError):
                    send_request.parse_metadata(json.dumps(metadata))

    def test_claude_short_prompt_starts_without_activation(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="claude",
            prompt="自己紹介して",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls[0], ["pane", "run", "w1Z:pX", "自己紹介して"])
        self.assertEqual(calls[1][:2], ["wait", "agent-status"])
        self.assertNotIn(["pane", "run", "w1Z:pX", "実行して"], calls)

    def test_claude_long_paste_activates_and_succeeds(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(
                    ["pane", "read"], 0, "before\n[Pasted text #1]\nafter", ""
                ),
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="claude",
            prompt="x" * 4000,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls[0], ["pane", "run", "w1Z:pX", "x" * 4000])
        self.assertEqual(calls[1][:2], ["wait", "agent-status"])
        self.assertEqual(calls[2][:2], ["pane", "read"])
        self.assertEqual(calls[3], ["pane", "run", "w1Z:pX", "実行して"])
        self.assertEqual(calls[4][:2], ["wait", "agent-status"])

    def test_claude_no_placeholder_waits_remaining_timeout_and_succeeds(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(["pane", "read"], 0, "no placeholder here", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="claude",
            prompt="x" * 4000,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            len([c for c in calls if c[:2] == ["wait", "agent-status"]]), 2
        )
        self.assertNotIn(["pane", "run", "w1Z:pX", "実行して"], calls)

    def test_claude_long_paste_without_placeholder_diagnoses_after_full_timeout(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(["pane", "read"], 0, "no placeholder here", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(["pane", "get"], 0, "{}", ""),
                CompletedProcess(["pane", "read"], 0, "still idle", ""),
            ],
            agent="claude",
            prompt="x" * 4000,
        )
        self.assertEqual(rc, 1)
        diagnostics = stderr
        self.assertIn("request_delivery_failed", diagnostics)
        self.assertIn("still idle", diagnostics)
        self.assertEqual(calls[-2][:2], ["pane", "get"])
        self.assertEqual(calls[-1][:2], ["pane", "read"])

    def test_codex_slow_start_waits_full_timeout_then_diagnoses(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(["pane", "get"], 0, "{}", ""),
                CompletedProcess(["pane", "read"], 0, "still idle", ""),
            ],
            agent="codex",
            prompt="x" * 4000,
        )
        self.assertEqual(rc, 1)
        self.assertIn("request_delivery_failed", stderr)
        self.assertIn("still idle", stderr)
        self.assertEqual(
            len([c for c in calls if c[:2] == ["wait", "agent-status"]]), 1
        )

    def test_claude_activation_fails_then_diagnoses(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(
                    ["pane", "read"], 0, "[Pasted text #1]", ""
                ),
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 1, "", ""),
                CompletedProcess(["pane", "get"], 0, "{}", ""),
                CompletedProcess(["pane", "read"], 0, "stuck idle", ""),
            ],
            agent="claude",
            prompt="x" * 4000,
        )
        self.assertEqual(rc, 1)
        self.assertIn("request_delivery_failed", stderr)
        self.assertIn("stuck idle", stderr)
        self.assertEqual(calls[3], ["pane", "run", "w1Z:pX", "実行して"])

    def test_delivery_failure_diagnoses_immediately(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 1, "", "pane not found"),
                CompletedProcess(["pane", "get"], 0, "{}", ""),
                CompletedProcess(["pane", "read"], 0, "error", ""),
            ],
            agent="codex",
            prompt="hello",
        )
        self.assertEqual(rc, 1)
        self.assertIn("request_delivery_failed", stderr)
        self.assertIn("pane not found", stderr)
        self.assertEqual(calls[0], ["pane", "run", "w1Z:pX", "hello"])
        self.assertEqual(calls[1][:2], ["pane", "get"])
        self.assertEqual(calls[2][:2], ["pane", "read"])

    def test_argument_validation(self):
        with patch.object(
            sys,
            "argv",
            [
                "send_request.py",
                "--target",
                "w1:p2",
                "--agent",
                "claude",
                "--prompt",
                "x",
                "--activation-timeout",
                "40000",
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                send_request.main()
        self.assertNotEqual(ctx.exception.code, 0)

    def test_opencode_starts_immediately_without_activation(self):
        rc, stderr, calls = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="opencode",
            prompt="self introduction",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(calls[0], ["pane", "run", "w1Z:pX", "self introduction"])
        self.assertEqual(calls[1][:2], ["wait", "agent-status"])


if __name__ == "__main__":
    unittest.main()
