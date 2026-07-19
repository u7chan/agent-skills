import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import freeze_resolution  # noqa: E402


class FreezeResolutionTest(unittest.TestCase):
    def test_resolved_values_are_pinned_to_launch_command_and_metadata(self):
        dry_run = (
            "# Resolved level: high\n"
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
        self.assertTrue(result["verified"])
        self.assertEqual(
            result["resolved"],
            {
                "agent_id": "codex",
                "agent": "Codex",
                "model": "gpt-5.6-sol",
                "effort": "high",
            },
        )
        self.assertEqual(
            result["agent_command"],
            "cagent --agent codex --model gpt-5.6-sol --effort high high",
        )
        self.assertEqual(
            result["delegation_metadata"],
            {"agent": "Codex", "model": "gpt-5.6-sol", "effort": "high"},
        )

    def test_missing_value_omits_entire_metadata_snapshot(self):
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="low",
            dry_run="/usr/bin/codex --model gpt-5.6-luna\n",
            verification_dry_run="/usr/bin/codex --model gpt-5.6-luna\n",
        )
        self.assertIsNone(result["delegation_metadata"])
        self.assertNotIn("--effort", result["agent_command"])

    def test_unknown_display_agent_omits_metadata(self):
        result = freeze_resolution.freeze_resolution(
            agent_id="custom",
            base_agent_type="custom",
            level=None,
            dry_run=(
                "# Resolved effort: medium\n"
                "/usr/bin/custom --model custom-model\n"
            ),
            verification_dry_run=(
                "# Resolved effort: medium\n"
                "/usr/bin/custom --model custom-model\n"
            ),
        )
        self.assertIsNone(result["delegation_metadata"])
        self.assertIn("--model custom-model", result["agent_command"])
        self.assertIn("--effort medium", result["agent_command"])

    def test_unverified_result_never_contains_delegation_metadata(self):
        result = freeze_resolution.freeze_resolution(
            agent_id="codex",
            base_agent_type="codex",
            level="high",
            dry_run=(
                "# Resolved effort: high\n"
                "/usr/bin/codex --model gpt-5.6-sol\n"
            ),
        )
        self.assertFalse(result["verified"])
        self.assertIsNone(result["delegation_metadata"])

    def test_mismatched_verification_is_rejected(self):
        with self.assertRaises(ValueError):
            freeze_resolution.freeze_resolution(
                agent_id="codex",
                base_agent_type="codex",
                level="high",
                dry_run=(
                    "# Resolved effort: high\n"
                    "/usr/bin/codex --model gpt-5.6-sol\n"
                ),
                verification_dry_run=(
                    "# Resolved effort: high\n"
                    "/usr/bin/codex --model gpt-5.6-terra\n"
                ),
            )


if __name__ == "__main__":
    unittest.main()
