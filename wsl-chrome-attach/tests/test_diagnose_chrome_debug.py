from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "diagnose_chrome_debug.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("diagnose_chrome_debug", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["diagnose_chrome_debug"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DiagnoseChromeDebugTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diag = load_module()

    def candidates_for(self, port: int) -> list[tuple[str, str]]:
        with (
            mock.patch.object(self.diag, "read_resolv_nameservers", return_value=[]),
            mock.patch.object(
                self.diag, "read_default_gateways", return_value=["172.25.128.1"]
            ),
        ):
            return [
                (candidate.url, candidate.source)
                for candidate in self.diag.build_candidates(port, [])
            ]

    def test_default_port_includes_default_gateway_portproxy_candidate(self) -> None:
        candidates = self.candidates_for(self.diag.DEFAULT_PORT)

        self.assertIn(
            ("http://172.25.128.1:9334", "default gateway portproxy"),
            candidates,
        )

    def test_portproxy_port_does_not_add_duplicate_candidate(self) -> None:
        candidates = self.candidates_for(self.diag.DEFAULT_PORTPROXY_PORT)
        urls = [url for url, _ in candidates]

        self.assertIn(
            ("http://172.25.128.1:9334", "default gateway"),
            candidates,
        )
        self.assertNotIn(
            ("http://172.25.128.1:9334", "default gateway portproxy"),
            candidates,
        )
        self.assertEqual(urls.count("http://172.25.128.1:9334"), 1)

    def test_explicit_candidate_keeps_priority_before_built_in_candidates(self) -> None:
        with (
            mock.patch.object(self.diag, "read_resolv_nameservers", return_value=[]),
            mock.patch.object(
                self.diag, "read_default_gateways", return_value=["172.25.128.1"]
            ),
        ):
            candidates = self.diag.build_candidates(
                self.diag.DEFAULT_PORT,
                ["http://example.test:9444"],
            )

        self.assertEqual(candidates[0].url, "http://example.test:9444")
        self.assertEqual(candidates[0].source, "--candidate")

    def test_failure_help_mentions_portproxy_for_default_port(self) -> None:
        with mock.patch.object(
            self.diag, "read_default_gateways", return_value=["172.25.128.1"]
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                self.diag.print_failure_help(self.diag.DEFAULT_PORT)

        text = output.getvalue()
        self.assertIn("For WSL NAT mode with Windows portproxy:", text)
        self.assertIn("http://172.25.128.1:9334", text)
        self.assertIn("0.0.0.0:9334 -> 127.0.0.1:9333", text)

    def test_failure_help_omits_portproxy_for_non_default_port(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.diag.print_failure_help(9222)

        self.assertNotIn("For WSL NAT mode with Windows portproxy:", output.getvalue())

    def test_success_output_mentions_next_skill(self) -> None:
        candidate = self.diag.Candidate("http://127.0.0.1:9333", "test")
        result = self.diag.Result(
            candidate,
            ok=True,
            data={
                "Browser": "Chrome/Test",
                "webSocketDebuggerUrl": "ws://127.0.0.1:9333/devtools/browser/test",
            },
        )

        with (
            mock.patch.object(self.diag, "build_candidates", return_value=[candidate]),
            mock.patch.object(self.diag, "fetch_versions", return_value=[result]),
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = self.diag.main([])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Next step:", text)
        self.assertIn("wsl-chrome-attach-use skill", text)


if __name__ == "__main__":
    unittest.main()
