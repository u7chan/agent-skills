"""Repository loading and source locations for skill validation.

This module deliberately does no policy validation.  It provides a small,
immutable-ish view which Phase 3 graph checks can consume directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import yaml

from .diagnostics import Diagnostics, Suppression

EXCLUDED_DIRS = {".git", ".archive", ".system", ".codex", "node_modules", "__pycache__"}
MAINTENANCE_ROOT = Path(".claude/skills")
IMPLEMENTED_CHECK_IDS = frozenset({
    "V-ARC-001", "V-ARC-002", "V-ARC-003", "V-CAT-001", "V-CAT-002",
    "V-CFG-001", "V-CFG-002", "V-CMP-001", "V-CMP-002", "V-CMP-003", "V-CMP-004",
    "V-DEP-001", "V-DEP-002", "V-DEP-003", "V-DEP-004", "V-DEP-005", "V-DEP-006", "V-DEP-007",
    "V-EXT-001", "V-EXT-002", "V-EXT-003", "V-EXT-004", "V-EXT-005", "V-INV-001",
    "V-NAM-001", "V-NAM-002", "V-NAM-003", "V-PUB-001", "V-PUB-002",
    "V-STR-001", "V-STR-002", "V-STR-003", "V-STR-004", "V-STR-005", "V-STR-006",
})


class DuplicateKeyError(yaml.YAMLError):
    def __init__(self, key: object, mark: yaml.error.Mark):
        super().__init__(f"duplicate key {key!r}")
        self.mark = mark


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe loader that rejects duplicate mapping keys at every nesting level."""

    def construct_mapping(self, node: yaml.nodes.MappingNode, deep: bool = False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise DuplicateKeyError(key, key_node.start_mark)
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


@dataclass
class Skill:
    name: str
    path: Path
    directory: Path
    line: int
    frontmatter: dict[str, Any]
    classification: str
    category: str | None = None
    canonical: dict[str, Any] | None = None

    @property
    def lines(self) -> list[str]:
        return self.path.read_text(encoding="utf-8").splitlines()


@dataclass(frozen=True)
class ReadmeEntry:
    name: str
    path: str
    line: int
    dependency: str


@dataclass
class RepositoryModel:
    root: Path
    diagnostics: Diagnostics
    rules: dict[str, Any] = field(default_factory=dict)
    categories_document: dict[str, Any] = field(default_factory=dict)
    skills: list[Skill] = field(default_factory=list)
    canonical_skills: dict[str, dict[str, Any]] = field(default_factory=dict)
    categories: dict[str, dict[str, Any]] = field(default_factory=dict)
    relations: dict[str, list[str]] = field(default_factory=dict)
    readme_entries: list[ReadmeEntry] = field(default_factory=list)
    readme_lines: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, root: Path, diagnostics: Diagnostics) -> "RepositoryModel":
        model = cls(root=root, diagnostics=diagnostics)
        model.rules = model._load_yaml(Path(".rules/skill-rules.yaml"))
        model.categories_document = model._load_yaml(Path(".rules/skill-categories.yaml"))
        model._load_categories()
        model._discover_skills()
        model._load_readme()
        model._configure_exceptions()
        return model

    def _load_yaml(self, relative: Path) -> dict[str, Any]:
        path = self.root / relative
        if not path.is_file():
            self.diagnostics.error("V-CFG-001", relative, 1, "required YAML file is missing")
            return {}
        try:
            loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        except DuplicateKeyError as exc:
            self.diagnostics.error("V-CFG-001", relative, exc.mark.line + 1, str(exc))
            return {}
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            self.diagnostics.error("V-CFG-001", relative, (mark.line + 1 if mark else 1), f"YAML parse error: {exc}")
            return {}
        if not isinstance(loaded, dict):
            self.diagnostics.error("V-CFG-001", relative, 1, "top-level YAML value must be a mapping")
            return {}
        return loaded

    def _load_categories(self) -> None:
        for document, relative, required in (
            (self.rules, ".rules/skill-rules.yaml", ("meta", "categories", "naming")),
            (self.categories_document, ".rules/skill-categories.yaml", ("meta", "category_summary", "skills")),
        ):
            for key in required:
                if key not in document:
                    self.diagnostics.error("V-CFG-001", relative, 1, f"required key {key!r} is missing")
        for document, relative in (
            (self.rules, ".rules/skill-rules.yaml"),
            (self.categories_document, ".rules/skill-categories.yaml"),
        ):
            if not isinstance(document.get("meta"), dict):
                self.diagnostics.error("V-CFG-001", relative, 1, "meta must be a mapping")

        category_defs = self.rules.get("categories")
        if not isinstance(category_defs, list):
            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "categories must be a list")
            category_defs = []
        for item in category_defs:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "each category needs a string id")
                continue
            category_id = item["id"]
            expected_types = {
                "label": str,
                "order": int,
                "allowed_depends_on": list,
                "may_be_depended_on_by": list,
            }
            for key, expected in expected_types.items():
                value = item.get(key)
                if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
                    self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"category {category_id!r}.{key} must be {expected.__name__}")
            for key in ("allowed_depends_on", "may_be_depended_on_by"):
                values = item.get(key)
                if isinstance(values, list) and any(not isinstance(value, str) or not value for value in values):
                    self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"category {category_id!r}.{key} must contain non-empty strings")
            if category_id in self.categories:
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"duplicate category id {category_id!r}")
            self.categories[category_id] = item
        for category_id, item in self.categories.items():
            for key in ("allowed_depends_on", "may_be_depended_on_by"):
                values = item.get(key, [])
                if isinstance(values, list):
                    for target in values:
                        if isinstance(target, str) and target not in self.categories:
                            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"category {category_id!r}.{key} references unknown category {target!r}")
        naming = self.rules.get("naming")
        if not isinstance(naming, dict) or not isinstance(naming.get("exceptions"), list) or not isinstance(naming.get("borderline"), list):
            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "naming.exceptions and naming.borderline must be lists")
        self._validate_validation_config()
        summary = self.categories_document.get("category_summary")
        if not isinstance(summary, list):
            self.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, "category_summary must be a list")
        entries = self.categories_document.get("skills")
        if not isinstance(entries, list):
            self.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, "skills must be a list")
            entries = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                self.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, "each skill needs a string name")
                continue
            name = entry["name"]
            line = self._yaml_line(".rules/skill-categories.yaml", f"name: {name}")
            expected_types = {
                "category": str,
                "classification": str,
                "path": str,
                "naming": str,
                "depends_on": list,
                "external_dependencies_ref": str,
                "known_issues": list,
            }
            for key, expected in expected_types.items():
                if not isinstance(entry.get(key), expected):
                    self.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", line, f"skill {name!r}.{key} must be {expected.__name__}")
            if name in self.canonical_skills:
                self.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", line, f"duplicate canonical skill {name!r}")
            self.canonical_skills[name] = entry
            depends_on = entry.get("depends_on", [])
            self.relations[name] = list(depends_on) if isinstance(depends_on, list) else []

    def _validate_validation_config(self) -> None:
        validation = self.rules.get("validation")
        if not isinstance(validation, dict):
            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "validation must be a mapping")
            return
        checks = validation.get("checks")
        if not isinstance(checks, list):
            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "validation.checks must be a list")
            return
        seen: set[str] = set()
        for check in checks:
            if not isinstance(check, dict):
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, "each validation check must be a mapping")
                continue
            check_id = check.get("id")
            if not isinstance(check_id, str) or not re.fullmatch(r"V-[A-Z]+-[0-9]{3}", check_id):
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"invalid validation check id {check_id!r}")
                continue
            if check_id in seen:
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"duplicate validation check id {check_id!r}")
            seen.add(check_id)
            if check.get("level") not in {"ERROR", "WARNING"}:
                self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"validation check {check_id!r} has invalid level")
            for key in ("subject", "description", "mechanical_check"):
                if not isinstance(check.get(key), str) or not check[key].strip():
                    self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"validation check {check_id!r}.{key} must be a non-empty string")
        if seen != IMPLEMENTED_CHECK_IDS:
            missing = ", ".join(sorted(IMPLEMENTED_CHECK_IDS - seen)) or "—"
            extra = ", ".join(sorted(seen - IMPLEMENTED_CHECK_IDS)) or "—"
            self.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"validation check IDs differ from implementation: missing={missing}; extra={extra}")

    def _discover_skills(self) -> None:
        paths: list[Path] = []
        for base, dirs, files in self._walk_active():
            if "SKILL.md" in files:
                paths.append(base / "SKILL.md")
        public_roots = [path for path in self.root.iterdir() if not path.name.startswith(".")]
        maintenance_root = self.root / MAINTENANCE_ROOT
        if maintenance_root.is_dir():
            public_roots.extend(maintenance_root.iterdir())
        for directory in public_roots:
            candidate = directory / "SKILL.md"
            if directory.is_symlink() and candidate.is_file() and candidate not in paths:
                paths.append(candidate)
        for path in sorted(paths):
            content = path.read_text(encoding="utf-8")
            frontmatter, line = self._frontmatter(path, content)
            name = frontmatter.get("name") if isinstance(frontmatter, dict) else None
            if not isinstance(name, str) or not name:
                name = ""
            relative = path.relative_to(self.root)
            classification = "maintenance" if relative.is_relative_to(MAINTENANCE_ROOT) else "distributable"
            canonical = self.canonical_skills.get(name)
            self.skills.append(Skill(name, path, path.parent, line, frontmatter, classification,
                                     canonical.get("category") if canonical else None, canonical))

    def _configure_exceptions(self) -> None:
        validation = self.rules.get("validation")
        if not isinstance(validation, dict):
            return
        schema = validation.get("exception_schema")
        exceptions = validation.get("exceptions")
        if not isinstance(schema, dict):
            self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, "validation.exception_schema must be a mapping")
            return
        expected_schema = {
            "required_fields": ["check_id", "target", "reason"],
            "suppressible_levels": ["WARNING"],
            "suppressible_error_check_ids": ["V-STR-002"],
        }
        for key, expected in expected_schema.items():
            if schema.get(key) != expected:
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"validation.exception_schema.{key} must equal {expected!r}")
        if not isinstance(exceptions, list):
            self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, "validation.exceptions must be a list")
            return
        checks = {
            item.get("id"): item.get("level")
            for item in validation.get("checks", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        skill_paths = {
            skill.name: skill.path.relative_to(self.root).as_posix()
            for skill in self.skills
            if skill.name
        }
        configured: list[Suppression] = []
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(exceptions, 1):
            if not isinstance(item, dict):
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"exception #{index} must be a mapping")
                continue
            check_id, target, reason = (item.get(key) for key in ("check_id", "target", "reason"))
            if any(not isinstance(value, str) or not value.strip() for value in (check_id, target, reason)):
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"exception #{index} requires non-empty check_id, target, and reason")
                continue
            check_id, target, reason = check_id.strip(), target.strip().rstrip("/"), reason.strip()
            key = (check_id, target)
            if key in seen:
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"duplicate exception for {check_id} and {target}")
                continue
            seen.add(key)
            if check_id not in checks:
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"exception references unknown check_id {check_id!r}")
                continue
            if checks[check_id] != "WARNING" and check_id != "V-STR-002":
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"exception cannot suppress ERROR check {check_id}")
                continue
            target_path = self.root / target
            if target not in skill_paths and (Path(target).is_absolute() or ".." in Path(target).parts or not target_path.exists()):
                self.diagnostics.error("V-CFG-002", ".rules/skill-rules.yaml", 1, f"exception target does not exist: {target}")
                continue
            targets = [target]
            if target in skill_paths:
                targets.append(skill_paths[target])
            configured.append(Suppression(check_id, tuple(targets), reason))
        self.diagnostics.configure_suppressions(configured)

    def _walk_active(self):
        # pathlib.rglob cannot prune excluded descendants, so use os.walk lazily.
        import os
        for base_text, dirs, files in os.walk(self.root):
            relative = Path(base_text).relative_to(self.root)
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            if relative == Path("."):
                dirs[:] = [d for d in dirs if d != ".claude"] + ([".claude"] if (self.root / ".claude").is_dir() else [])
            elif relative == Path(".claude"):
                dirs[:] = [d for d in dirs if d == "skills"]
            yield Path(base_text), dirs, files

    def _frontmatter(self, path: Path, content: str) -> tuple[dict[str, Any], int]:
        match = re.match(r"^---\s*$\n(.*?)^---\s*$", content, re.MULTILINE | re.DOTALL)
        if not match:
            self.diagnostics.error("V-STR-001", path, 1, "SKILL.md must begin with YAML frontmatter")
            return {}, 1
        try:
            data = yaml.load(match.group(1), Loader=UniqueKeyLoader)
        except DuplicateKeyError as exc:
            self.diagnostics.error("V-CFG-001", path, exc.mark.line + 2, str(exc))
            return {}, 1
        except yaml.YAMLError as exc:
            self.diagnostics.error("V-CFG-001", path, 1, f"frontmatter YAML parse error: {exc}")
            return {}, 1
        if not isinstance(data, dict):
            self.diagnostics.error("V-CFG-001", path, 1, "frontmatter must be a mapping")
            return {}, 1
        name_line = self._line_in_text(content, r"^name:\s*")
        return data, name_line

    def _load_readme(self) -> None:
        path = self.root / "README.md"
        if not path.is_file():
            self.diagnostics.error("V-PUB-001", "README.md", 1, "README.md is missing")
            return
        self.readme_lines = path.read_text(encoding="utf-8").splitlines()
        in_available = False
        row = re.compile(r"^\|\s*\[([^]]+)\]\(([^)]+/SKILL\.md)\)\s*\|.*\|\s*(.*?)\s*\|\s*$")
        for number, line in enumerate(self.readme_lines, 1):
            if line == "## Available Skills":
                in_available = True
                continue
            if in_available and line.startswith("## "):
                break
            if in_available and (match := row.match(line)):
                self.readme_entries.append(ReadmeEntry(match.group(1), match.group(2), number, match.group(3)))

    def _yaml_line(self, relative: str, text: str) -> int:
        path = self.root / relative
        return self._line_in_text(path.read_text(encoding="utf-8"), rf"^\s*{re.escape(text)}")

    @staticmethod
    def _line_in_text(text: str, pattern: str) -> int:
        found = re.search(pattern, text, re.MULTILINE)
        return text[:found.start()].count("\n") + 1 if found else 1

    @property
    def distributable_skills(self) -> list[Skill]:
        return [skill for skill in self.skills if skill.classification == "distributable"]

    @property
    def skill_by_name(self) -> dict[str, Skill]:
        return {skill.name: skill for skill in self.skills if skill.name}
