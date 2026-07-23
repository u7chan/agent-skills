"""Black-box regressions for the public Bash and Python validation contract."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "valid"


class ValidationCliTest(unittest.TestCase):
    def make_repo(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "repo"
        shutil.copytree(FIXTURE, root)
        for template in root.rglob("SKILL.md.in"):
            template.rename(template.with_name("SKILL.md"))
        scripts = root / ".scripts"
        scripts.mkdir()
        for name in ("validate_skill_rules.py", "inventory.py", "validate-skills.sh"):
            shutil.copy2(REPO / ".scripts" / name, scripts / name)
        shutil.copytree(REPO / ".scripts" / "skill_validation", scripts / "skill_validation", ignore=shutil.ignore_patterns("__pycache__"))
        return root

    def invoke(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, ".scripts/validate_skill_rules.py", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def invoke_bash(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", ".scripts/validate-skills.sh", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def refresh_inventory(self, root: Path) -> None:
        result = subprocess.run(
            [sys.executable, ".scripts/inventory.py"], cwd=root, text=True, capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def assert_error(self, root: Path, check_id: str, path: str, reason: str) -> subprocess.CompletedProcess[str]:
        result = self.invoke(root)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f"ERROR [{check_id}] {path}:", result.stderr)
        self.assertIn(reason, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def skill(self, root: Path, name: str) -> Path:
        return root / name / "SKILL.md"

    def replace(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def pad_skill(self, root: Path, name: str, length: int) -> None:
        path = self.skill(root, name)
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), length)
        path.write_text("\n".join(lines + ["padding"] * (length - len(lines))) + "\n", encoding="utf-8")

    def add_exception(self, root: Path, check_id: str, target: str, reason: str = "fixture debt") -> None:
        self.set_exceptions(
            root,
            f"  exceptions:\n    - check_id: {check_id}\n      target: {target}\n      reason: {reason}",
        )

    def set_exceptions(self, root: Path, replacement: str) -> None:
        path = root / ".rules/skill-rules.yaml"
        text = path.read_text(encoding="utf-8")
        before, separator, after = text.rpartition("  exceptions: []")
        self.assertTrue(separator)
        path.write_text(before + replacement + after, encoding="utf-8")

    def add_maintenance(self, root: Path, declaration: str | None) -> Path:
        source = root / "tool-leaf-validate"
        target = root / ".claude/skills/maint-tool-validate"
        shutil.copytree(source, target)
        self.replace(target / "SKILL.md", "tool-leaf-validate", "maint-tool-validate")
        self.replace(target / "agents/openai.yaml", "tool-leaf-validate", "maint-tool-validate")
        scripts = target / "scripts"
        scripts.mkdir()
        (scripts / "probe.py").write_text('import subprocess\nsubprocess.run(["maint-cli", "--version"])\n', encoding="utf-8")
        with (target / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("\nRun `scripts/probe.py`.\n")
        categories = root / ".rules/skill-categories.yaml"
        text = categories.read_text(encoding="utf-8")
        text = text.replace("total_skills: 3, distributable: 3, maintenance: 0", "total_skills: 4, distributable: 3, maintenance: 1")
        text = text.replace("{id: tool, count: 1, skills: [tool-leaf-validate]}", "{id: tool, count: 2, skills: [tool-leaf-validate, maint-tool-validate]}")
        extra = (
            "\n  - name: maint-tool-validate\n"
            "    path: .claude/skills/maint-tool-validate\n"
            "    category: tool\n"
            "    classification: maintenance\n"
            "    naming: conforms\n"
            "    depends_on: []\n"
            "    external_dependencies_ref: inventory/skills.yaml\n"
        )
        if declaration is not None:
            extra += f"    external_dependencies: [{declaration}]\n"
        extra += "    known_issues: []\n"
        text = text.replace("dependency_notes:\n", extra + "dependency_notes:\n")
        categories.write_text(text, encoding="utf-8")
        return target

    def test_exit_codes_ordering_and_cli_misuse(self):
        root = self.make_repo()
        normal = self.invoke(root)
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(normal.stderr, "")

        self.replace(self.skill(root, "tool-leaf-validate"), "name: tool-leaf-validate", "name: bad")
        error = self.invoke(root)
        self.assertEqual(error.returncode, 1)
        self.assertIn("ERROR [V-NAM-003]", error.stderr)
        lines = error.stderr.splitlines()

        def diagnostic_key(line: str) -> tuple[str, int, str, str, str]:
            match = re.fullmatch(r"(ERROR|WARNING) \[([^]]+)] (.*):(\d+): (.*)", line)
            self.assertIsNotNone(match)
            assert match is not None
            return (match.group(3), int(match.group(4)), match.group(2), match.group(1), match.group(5))

        self.assertEqual(lines, sorted(lines, key=diagnostic_key))
        misuse = self.invoke(root, "--unknown-option")
        self.assertEqual(misuse.returncode, 2)
        self.assertIn("usage:", misuse.stderr)

    def test_exception_schema_warning_and_v_str_002(self):
        root = self.make_repo()
        self.pad_skill(root, "tool-leaf-validate", 151)
        self.add_exception(root, "V-CMP-004", "tool-leaf-validate", "temporary prose")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING [V-CMP-004] tool-leaf-validate/SKILL.md:", result.stderr)
        self.assertIn("suppressed by configured exception (temporary prose)", result.stderr)

        root = self.make_repo()
        self.pad_skill(root, "tool-leaf-validate", 181)
        self.add_exception(root, "V-STR-002", "tool-leaf-validate/SKILL.md", "approved line debt")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING [V-STR-002] tool-leaf-validate/SKILL.md:", result.stderr)
        self.assertIn("approved line debt", result.stderr)
        self.assertNotIn("ERROR [V-STR-002]", result.stderr)

    def test_invalid_duplicate_unknown_and_forbidden_exceptions(self):
        root = self.make_repo()
        self.set_exceptions(root, "  exceptions:\n    - {check_id: V-CMP-004, target: tool-leaf-validate}")
        self.assert_error(root, "V-CFG-002", ".rules/skill-rules.yaml", "requires non-empty")

        root = self.make_repo()
        self.set_exceptions(
            root,
            "  exceptions:\n    - {check_id: V-CMP-004, target: tool-leaf-validate, reason: one}\n    - {check_id: V-CMP-004, target: tool-leaf-validate, reason: two}",
        )
        self.assert_error(root, "V-CFG-002", ".rules/skill-rules.yaml", "duplicate exception")

        root = self.make_repo()
        self.add_exception(root, "V-NOPE-999", "tool-leaf-validate")
        self.assert_error(root, "V-CFG-002", ".rules/skill-rules.yaml", "unknown check_id")

        root = self.make_repo()
        self.add_exception(root, "V-NAM-003", "tool-leaf-validate")
        self.assert_error(root, "V-CFG-002", ".rules/skill-rules.yaml", "cannot suppress ERROR")

    def test_canonical_schema_aggregates_and_types(self):
        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "category: tool", "category: [tool]")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", ".category must be str")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "total_skills: 3", "total_skills: 99")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "meta.total_skills")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "count: 1, skills: [tool-leaf-validate]", "count: 2, skills: [tool-leaf-validate]")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "category_summary 'tool'.count")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "skills: [tool-leaf-validate]", "skills: [git-child-validate]")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "does not match canonical classification")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "path: tool-leaf-validate", "path: wrong")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", ".path is 'wrong'")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "classification: distributable", "classification: []")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", ".classification must be str")

    def test_external_ref_known_issue_and_check_id_contracts(self):
        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "external_dependencies_ref: inventory/skills.yaml", "external_dependencies_ref: inventory/missing.yaml")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "must reference inventory/skills.yaml")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "known_issues: []", "known_issues: [{ref: F999, note: missing}]")
        self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "missing finding 'F999'")

        root = self.make_repo()
        self.replace(root / ".rules/skill-rules.yaml", "V-CMP-004", "V-CMP-099")
        self.assert_error(root, "V-CFG-001", ".rules/skill-rules.yaml", "check IDs differ from implementation")

    def test_all_dependency_note_items_are_validated(self):
        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "items: []", "items: [{from: tool-leaf-validate, to: git-child-validate, relation: invalid}]")
        self.assert_error(root, "V-DEP-006", ".rules/skill-categories.yaml", "invalid relation")

        root = self.make_repo()
        self.replace(root / ".rules/skill-categories.yaml", "items: []", "items: [{from: missing-source, to: git-child-validate, relation: mention}]")
        self.assert_error(root, "V-DEP-006", ".rules/skill-categories.yaml", "references missing active skill 'missing-source'")

        root = self.make_repo()
        self.replace(
            root / ".rules/skill-categories.yaml",
            "items: []",
            "items:\n      - {from: tool-leaf-validate, to: git-child-validate, relation: mention}\n      - {from: tool-leaf-validate, to: git-child-validate, relation: mention}",
        )
        self.assert_error(root, "V-DEP-006", ".rules/skill-categories.yaml", "duplicates tool-leaf-validate")

        root = self.make_repo()
        archived = root / ".archive/archived-tool-validate"
        archived.mkdir(parents=True)
        (archived / "SKILL.md").write_text("---\nname: archived-tool-validate\ndescription: archive\n---\n", encoding="utf-8")
        self.replace(root / ".rules/skill-categories.yaml", "items: []", "items: [{from: tool-leaf-validate, to: archived-tool-validate, relation: used_by}]")
        result = self.assert_error(root, "V-DEP-006", ".rules/skill-categories.yaml", "references archived skill")
        self.assertIn("ERROR [V-ARC-001]", result.stderr)

    def test_relation_aware_v_dep_005(self):
        root = self.make_repo()
        self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", "Mention `git-child-validate` and read `references/local.md`.")
        self.replace(root / ".rules/skill-categories.yaml", "items: []", "items: [{from: tool-leaf-validate, to: git-child-validate, relation: mention}]")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[V-DEP-005]", result.stderr)

    def test_naked_repo_root_dynamic_and_symlink_paths(self):
        cases = (
            ("See ../git-child-validate/SKILL.md.", "physical path references"),
            ("See git-child-validate/SKILL.md in normal prose.", "physical path references"),
            ("See <skill-dir>/../git-child-validate/SKILL.md.", "dynamic physical path references"),
        )
        for text, reason in cases:
            with self.subTest(text=text):
                root = self.make_repo()
                self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", text)
                self.assert_error(root, "V-DEP-003", "tool-leaf-validate/SKILL.md", reason)

        root = self.make_repo()
        absolute = root / "git-child-validate/SKILL.md"
        self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", f"See {absolute} in normal prose.")
        self.assert_error(root, "V-DEP-003", "tool-leaf-validate/SKILL.md", "physical path references")

        root = self.make_repo()
        link = root / "tool-leaf-validate/references/escape"
        link.symlink_to(root / "git-child-validate", target_is_directory=True)
        self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", "Read `references/local.md` and references/escape/SKILL.md.")
        self.assert_error(root, "V-DEP-003", "tool-leaf-validate/SKILL.md", "another active skill")

    def test_truly_unresolved_dynamic_path_warns(self):
        root = self.make_repo()
        self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", "See <skill-dir>/../<unknown-skill>/SKILL.md and `references/local.md`.")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING [V-DEP-003] tool-leaf-validate/SKILL.md:", result.stderr)
        self.assertIn("cannot be resolved", result.stderr)

    def test_public_labels_depth_and_symlinks(self):
        root = self.make_repo()
        self.replace(root / "README.md", "[tool-leaf-validate]", "[wrong-label]")
        self.assert_error(root, "V-PUB-001", "README.md", "link label 'wrong-label'")

        root = self.make_repo()
        nested = root / "tool-leaf-validate/nested-skill-validate"
        shutil.copytree(root / "git-child-validate", nested)
        self.replace(nested / "SKILL.md", "git-child-validate", "nested-skill-validate")
        self.replace(nested / "agents/openai.yaml", "git-child-validate", "nested-skill-validate")
        self.assert_error(root, "V-PUB-002", "tool-leaf-validate/nested-skill-validate/SKILL.md", "outside the allowed public depth")

        root = self.make_repo()
        (root / "broken-public-validate").symlink_to("missing-target", target_is_directory=True)
        self.assert_error(root, "V-PUB-002", "broken-public-validate", "symlink is broken")

        root = self.make_repo()
        (root / "alias-public-validate").symlink_to("tool-leaf-validate", target_is_directory=True)
        self.assert_error(root, "V-PUB-002", "tool-leaf-validate", "same SKILL.md")

        root = self.make_repo()
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_skill_and_readme_name_path_duplicates_are_errors(self):
        root = self.make_repo()
        self.replace(self.skill(root, "git-child-validate"), "name: git-child-validate", "name: tool-leaf-validate")
        self.assert_error(root, "V-NAM-002", "tool-leaf-validate/SKILL.md", "duplicates")

        root = self.make_repo()
        readme = root / "README.md"
        with readme.open("a", encoding="utf-8") as handle:
            handle.write("| [tool-leaf-validate](tool-leaf-validate/SKILL.md) | duplicate | Leaf (R) |\n")
        self.assert_error(root, "V-PUB-001", "README.md", "duplicates tool-leaf-validate/SKILL.md")

    def test_unreferenced_reference_and_script(self):
        root = self.make_repo()
        (root / "tool-leaf-validate/references/orphan.md").write_text("orphan\n", encoding="utf-8")
        self.assert_error(root, "V-STR-005", "tool-leaf-validate/references/orphan.md", "not owned")

        root = self.make_repo()
        scripts = root / "tool-leaf-validate/scripts"
        scripts.mkdir()
        (scripts / "orphan.py").write_text("print('orphan')\n", encoding="utf-8")
        self.assert_error(root, "V-STR-005", "tool-leaf-validate/scripts/orphan.py", "not referenced")

    def test_python_subprocess_and_javascript_import_evidence(self):
        root = self.make_repo()
        scripts = root / "tool-leaf-validate/scripts"
        scripts.mkdir()
        (scripts / "probe.py").write_text('import os\nimport subprocess\nsubprocess.Popen(["missing-cli", "--version"])\nos.system("other-cli --version")\n', encoding="utf-8")
        with self.skill(root, "tool-leaf-validate").open("a", encoding="utf-8") as handle:
            handle.write("\nRun `scripts/probe.py`.\n")
        result = self.assert_error(root, "V-EXT-004", "tool-leaf-validate/scripts/probe.py", "external command 'missing-cli'")
        self.assertIn("other-cli", result.stderr)

        root = self.make_repo()
        scripts = root / "tool-leaf-validate/scripts"
        scripts.mkdir()
        (scripts / "probe.js").write_text('const pad = require("left-pad");\n', encoding="utf-8")
        with self.skill(root, "tool-leaf-validate").open("a", encoding="utf-8") as handle:
            handle.write("\nRun `scripts/probe.js`.\n")
        self.assert_error(root, "V-EXT-004", "tool-leaf-validate/scripts/probe.js", "external command 'left-pad'")

    def test_stdlib_and_repository_scripts_are_not_external(self):
        root = self.make_repo()
        scripts = root / "tool-leaf-validate/scripts"
        scripts.mkdir()
        (scripts / "helper.py").write_text("import json\n", encoding="utf-8")
        (scripts / "probe.py").write_text('import subprocess\nsubprocess.run(["scripts/helper.py"])\n', encoding="utf-8")
        with self.skill(root, "tool-leaf-validate").open("a", encoding="utf-8") as handle:
            handle.write("\nRun `scripts/helper.py` and `scripts/probe.py`.\n")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[V-EXT-004]", result.stderr)

    def test_maintenance_declaration_source_is_explicit(self):
        root = self.make_repo()
        self.add_maintenance(root, None)
        self.assert_error(root, "V-EXT-004", ".rules/skill-categories.yaml", "has no external dependency declaration source")

        root = self.make_repo()
        self.add_maintenance(root, "maint-cli")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_inventory_staleness_is_error_and_regeneration_recovers(self):
        root = self.make_repo()
        with self.skill(root, "tool-leaf-validate").open("a", encoding="utf-8") as handle:
            handle.write("\nstale inventory input\n")
        self.assert_error(root, "V-INV-001", "inventory/skills.yaml", "stale")
        self.refresh_inventory(root)
        result = self.invoke(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_graph_is_deterministic_atomic_and_preserved_on_error(self):
        root = self.make_repo()
        first = self.invoke(root, "--graph", "first.md")
        second = self.invoke(root, "--graph", "second.md")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((root / "first.md").read_bytes(), (root / "second.md").read_bytes())

        output = root / "preserve.md"
        output.write_text("old", encoding="utf-8")
        self.replace(root / "README.md", "Parent (O)", "Parent (Z)")
        error = self.invoke(root, "--graph", str(output))
        self.assertEqual(error.returncode, 1, error.stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "old")

    def test_graph_io_error_is_exit_2_without_losing_diagnostics(self):
        root = self.make_repo()
        self.pad_skill(root, "tool-leaf-validate", 151)
        self.refresh_inventory(root)
        output = root / "graph-directory"
        output.mkdir()
        result = self.invoke(root, "--graph", str(output))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("WARNING [V-CMP-004]", result.stderr)
        self.assertIn("CLI ERROR [graph-output]", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_bash_entrypoint_is_integrated(self):
        root = self.make_repo()
        success = self.invoke_bash(root)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.replace(self.skill(root, "tool-leaf-validate"), "Read `references/local.md`.", "See git-child-validate/SKILL.md.")
        error = self.invoke_bash(root)
        self.assertEqual(error.returncode, 1, error.stderr)
        self.assertIn("ERROR [V-DEP-003] tool-leaf-validate/SKILL.md:", error.stderr)

    def test_routes_to_not_depends_relation_list_is_schema_error(self):
        root = self.make_repo()
        self.replace(
            root / ".rules/skill-categories.yaml",
            "items: []",
            "items: [{from: tool-leaf-validate, to: git-child-validate, relation: [mention]}]",
        )
        result = self.assert_error(root, "V-CFG-001", ".rules/skill-categories.yaml", "relation must be a string, got list")
        self.assertNotIn("Traceback", result.stderr)

    def test_naming_exception_skill_list_is_schema_error(self):
        root = self.make_repo()
        self.replace(
            root / ".rules/skill-rules.yaml",
            "exceptions: []",
            "exceptions:\n    - skill: [grilling]\n      reason: invalid",
        )
        result = self.assert_error(root, "V-CFG-001", ".rules/skill-rules.yaml", "skill must be a string, got list")
        self.assertNotIn("Traceback", result.stderr)

    def test_known_cross_skill_dynamic_path_is_dep_error(self):
        root = self.make_repo()
        self.add_maintenance(root, "maint-cli")
        self.replace(
            self.skill(root, "tool-leaf-validate"),
            "Read `references/local.md`.",
            "See `<skill-dir>/../.claude/skills/maint-tool-validate/SKILL.md`.",
        )
        self.assert_error(
            root,
            "V-DEP-003",
            "tool-leaf-validate/SKILL.md",
            "dynamic physical path references another active skill 'maint-tool-validate'",
        )

    def test_python_import_alias_and_from_import_process_calls(self):
        root = self.make_repo()
        scripts = root / "tool-leaf-validate/scripts"
        scripts.mkdir()
        (scripts / "probe.py").write_text(
            'import subprocess as sp\nfrom os import system\nsp.run(["missing-cli", "--version"])\nsystem("other-cli --version")\n',
            encoding="utf-8",
        )
        with self.skill(root, "tool-leaf-validate").open("a", encoding="utf-8") as handle:
            handle.write("\nRun `scripts/probe.py`.\n")
        result = self.assert_error(
            root,
            "V-EXT-004",
            "tool-leaf-validate/scripts/probe.py",
            "external command 'missing-cli'",
        )
        self.assertIn("other-cli", result.stderr)

    def test_maintenance_external_dependencies_appear_in_graph(self):
        root = self.make_repo()
        self.add_maintenance(root, "maint-cli")
        self.refresh_inventory(root)
        result = self.invoke(root, "--graph", "graph.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        graph = (root / "graph.md").read_text(encoding="utf-8")
        self.assertIn("maint-tool-validate", graph)
        self.assertIn("maint cli (R)", graph)


if __name__ == "__main__":
    unittest.main()
