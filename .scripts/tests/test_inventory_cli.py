"""Inventory generation and checked-in schema contracts."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO = Path(__file__).parents[2]
NAMES = ("skills.yaml", "dependency-graph.yaml", "findings.yaml", "summary.yaml")


class InventoryCliTest(unittest.TestCase):
    def generate(self, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, ".scripts/inventory.py", "--output-dir", str(output)],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_checked_in_inventory_has_all_four_files(self):
        for name in NAMES:
            path = REPO / "inventory" / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8"))["schema_version"], 2)

    def test_two_generations_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = self.generate(Path(first))
            two = self.generate(Path(second))
            self.assertEqual(one.returncode, 0, one.stderr)
            self.assertEqual(two.returncode, 0, two.stderr)
            for name in NAMES:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes(), name)

    def test_generated_output_matches_checked_in_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.generate(Path(temporary))
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in NAMES:
                self.assertEqual((Path(temporary) / name).read_bytes(), (REPO / "inventory" / name).read_bytes(), name)

    def test_summary_and_skills_counts_agree(self):
        summary = yaml.safe_load((REPO / "inventory/summary.yaml").read_text(encoding="utf-8"))
        skills = yaml.safe_load((REPO / "inventory/skills.yaml").read_text(encoding="utf-8"))
        self.assertEqual(summary["total_skills"], skills["total_count"])
        self.assertEqual(summary["distributable"], skills["distributable_count"])
        self.assertEqual(summary["maintenance"], skills["maintenance_count"])

    def test_canonical_known_issue_ids_exist_in_findings(self):
        categories = yaml.safe_load((REPO / ".rules/skill-categories.yaml").read_text(encoding="utf-8"))
        findings = yaml.safe_load((REPO / "inventory/findings.yaml").read_text(encoding="utf-8"))
        actual = {item["id"] for item in findings["findings"]}
        referenced = {
            issue["ref"]
            for skill in categories["skills"]
            for issue in skill["known_issues"]
        }
        self.assertLessEqual(referenced, actual)

    def test_dependency_graph_uses_only_canonical_depends_on_edges(self):
        categories = yaml.safe_load((REPO / ".rules/skill-categories.yaml").read_text(encoding="utf-8"))
        graph = yaml.safe_load((REPO / "inventory/dependency-graph.yaml").read_text(encoding="utf-8"))
        expected = {
            (skill["name"], target)
            for skill in categories["skills"]
            for target in skill.get("depends_on", [])
        }
        actual = {(edge["from"], edge["to"]) for edge in graph["edges"]}
        self.assertEqual(actual, expected)
        self.assertTrue(all(edge["relation"] == "depends_on" for edge in graph["edges"]))


if __name__ == "__main__":
    unittest.main()
