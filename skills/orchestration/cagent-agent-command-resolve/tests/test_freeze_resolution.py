import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import freeze_resolution  # noqa: E402


class FreezeResolutionTest(unittest.TestCase):
    def test_native_args_is_json_array_not_string(self):
        dry_run = (
            "# Resolved effort: high\n"
            "/usr/bin/codex --model gpt-5.6-sol -c 'reasoning=\"high\"'\n"
        )
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        self.assertIsInstance(result["native_agent_args"], list)
        self.assertGreater(len(result["native_agent_args"]), 0)
        self.assertIn("--model", result["native_agent_args"])

    def test_native_args_preserves_whitespace_and_quotes(self):
        dry_run = (
            "# Resolved effort: high\n"
            "/usr/bin/codex --model 'gpt-5.6 sol' -c \"effort='high'\"\n"
        )
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        args = result["native_agent_args"]
        self.assertIn("gpt-5.6 sol", args)
        self.assertIn("effort='high'", args)

    def test_verification_mismatched_native_args_fails(self):
        # Same model and effort, different -c value
        dry_run1 = (
            "# Resolved effort: high\n"
            "/usr/bin/codex --model gpt-5.6-sol -c x=1\n"
        )
        dry_run2 = (
            "# Resolved effort: high\n"
            "/usr/bin/codex --model gpt-5.6-sol -c x=2\n"
        )
        with self.assertRaises(ValueError):
            freeze_resolution.freeze_resolution(
                agent_id="codex",
                base_agent_type="codex",
                level="high",
                dry_run=dry_run1,
                verification_dry_run=dry_run2,
            )

    def test_verification_mismatched_effort_fails(self):
        dry_run1 = "# Resolved effort: high\n/usr/bin/codex --model gpt\n"
        dry_run2 = "# Resolved effort: low\n/usr/bin/codex --model gpt\n"
        with self.assertRaises(ValueError):
            freeze_resolution.freeze_resolution(
                agent_id="codex",
                base_agent_type="codex",
                level="high",
                dry_run=dry_run1,
                verification_dry_run=dry_run2,
            )

    def test_resolved_values_include_all_fields(self):
        dry_run = (
            "# Resolved effort: high\n"
            "/usr/bin/codex --model gpt-5.6-sol "
            "-c 'model_reasoning_effort=\"high\"'\n"
        )
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        self.assertEqual(result["base_agent_type"], "codex")
        self.assertEqual(result["agent_kind"], "codex")
        self.assertTrue(result["verified"])
        self.assertEqual(result["resolved"]["agent"], "Codex")
        self.assertEqual(result["resolved"]["model"], "gpt-5.6-sol")
        self.assertEqual(result["resolved"]["effort"], "high")
        self.assertEqual(
            result["delegation_metadata"],
            {"agent": "Codex", "model": "gpt-5.6-sol", "effort": "high"},
        )

    def test_native_args_empty_when_no_cli_args(self):
        dry_run = "/usr/bin/codex\n"
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="mid",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        self.assertEqual(result["native_agent_args"], [])

    def test_missing_value_omits_metadata(self):
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="low",
            dry_run="/usr/bin/codex --model gpt-5.6-luna\n",
            verification_dry_run="/usr/bin/codex --model gpt-5.6-luna\n",
        )
        self.assertIsNone(result["delegation_metadata"])

    def test_em_dash_value_omits_metadata(self):
        dry_run = "# Resolved effort: \u2014\n/usr/bin/codex --model gpt-5.6-sol\n"
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        self.assertIsNone(result["delegation_metadata"])

    def test_unverified_result_never_has_metadata(self):
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run="# Resolved effort: high\n/usr/bin/codex --model gpt\n",
        )
        self.assertFalse(result["verified"])
        self.assertIsNone(result["delegation_metadata"])

    def test_unicode_in_args_preserved(self):
        dry_run = (
            '# Resolved effort: high\n'
            '/usr/bin/codex --prompt "日本語テスト"\n'
        )
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        args = result["native_agent_args"]
        self.assertIn("日本語テスト", args)

    def test_joined_string_is_display_only(self):
        dry_run = "/usr/bin/codex --model gpt-5.6-sol -c high\n"
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=dry_run,
            verification_dry_run=dry_run,
        )
        self.assertIsInstance(result["native_agent_args"], list)
        self.assertIsInstance(result["native_agent_args_joined"], str)
        self.assertIn("--model gpt-5.6-sol", result["native_agent_args_joined"])


if __name__ == "__main__":
    unittest.main()
