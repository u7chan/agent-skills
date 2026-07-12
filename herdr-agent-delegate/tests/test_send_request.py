#!/usr/bin/env python3
"""Tests for herdr-agent-delegate/scripts/send_request.py."""

from __future__ import annotations

import argparse
import io
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

        def fake_run_herdr(arguments, timeout=None):
            return next(response_iter)

        stderr = io.StringIO()
        with patch.object(send_request, "run_herdr", side_effect=fake_run_herdr):
            with patch.object(sys, "stderr", stderr):
                rc = send_request.send_request(self._args(**overrides))
        return rc, stderr.getvalue()

    def test_codex_starts_immediately_without_activation(self):
        rc, stderr = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="codex",
            prompt="self introduction",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")

    def test_claude_short_prompt_starts_without_activation(self):
        rc, stderr = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="claude",
            prompt="自己紹介して",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")

    def test_claude_long_paste_activates_and_succeeds(self):
        rc, stderr = self._run(
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

    def test_claude_no_placeholder_waits_remaining_timeout_and_succeeds(self):
        rc, stderr = self._run(
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

    def test_claude_long_paste_without_placeholder_diagnoses_after_full_timeout(self):
        rc, stderr = self._run(
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

    def test_codex_slow_start_waits_full_timeout_then_diagnoses(self):
        rc, stderr = self._run(
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

    def test_claude_activation_fails_then_diagnoses(self):
        rc, stderr = self._run(
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

    def test_delivery_failure_diagnoses_immediately(self):
        rc, stderr = self._run(
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
        rc, stderr = self._run(
            [
                CompletedProcess(["pane", "run"], 0, "", ""),
                CompletedProcess(["wait", "agent-status"], 0, "", ""),
            ],
            agent="opencode",
            prompt="self introduction",
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
