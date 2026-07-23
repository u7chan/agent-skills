"""Structure, repository-publication, and naming checks."""

from __future__ import annotations

from pathlib import Path
import re

from .model import EXCLUDED_DIRS, MAINTENANCE_ROOT, RepositoryModel, Skill

MAX_LINES = 180
IMPORTANT_LINES = 150
LOCAL_LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")


def _line_of(lines: list[str], needle: str) -> int:
    return next((i for i, value in enumerate(lines, 1) if needle in value), 1)


def check_categories(model: RepositoryModel) -> None:
    actual = model.skill_by_name
    _check_canonical_aggregates(model)
    for name, skill in sorted(actual.items()):
        if name not in model.canonical_skills:
            model.diagnostics.error("V-CAT-001", skill.path, skill.line, "skill is not classified in .rules/skill-categories.yaml")
    for name, canonical in sorted(model.canonical_skills.items()):
        skill = actual.get(name)
        if skill is None:
            model.diagnostics.error("V-CAT-001", ".rules/skill-categories.yaml", 1, f"canonical skill {name!r} has no SKILL.md")
            continue
        category = canonical.get("category")
        if not isinstance(category, str) or category not in model.categories:
            model.diagnostics.error("V-CAT-002", ".rules/skill-categories.yaml", 1, f"skill {name!r} uses unknown category {category!r}")
        declared = canonical.get("classification")
        if not isinstance(declared, str) or declared not in {"distributable", "maintenance"}:
            model.diagnostics.error("V-CAT-002", ".rules/skill-categories.yaml", 1, f"skill {name!r} has invalid classification {declared!r}")
        elif declared != skill.classification:
            model.diagnostics.error("V-CAT-002", skill.path, skill.line, f"classification is {skill.classification}, canonical value is {declared}")
        expected_path = skill.directory.relative_to(model.root).as_posix()
        if canonical.get("path") != expected_path:
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"skill {name!r}.path is {canonical.get('path')!r}; expected {expected_path!r}")
        external_ref = canonical.get("external_dependencies_ref")
        if external_ref != "inventory/skills.yaml" or not (model.root / str(external_ref)).is_file():
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"skill {name!r}.external_dependencies_ref must reference inventory/skills.yaml")
    _check_known_issue_references(model)


def _check_canonical_aggregates(model: RepositoryModel) -> None:
    meta = model.categories_document.get("meta")
    if isinstance(meta, dict):
        expected = {
            "total_skills": len(model.skills),
            "distributable": len(model.distributable_skills),
            "maintenance": len(model.skills) - len(model.distributable_skills),
        }
        for key, value in expected.items():
            actual = meta.get(key)
            if not isinstance(actual, int) or isinstance(actual, bool) or actual != value:
                model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"meta.{key} is {actual!r}; expected {value}")
    summary = model.categories_document.get("category_summary")
    if not isinstance(summary, list):
        return
    grouped: dict[str, set[str]] = {category: set() for category in model.categories}
    for name, entry in model.canonical_skills.items():
        category = entry.get("category")
        if isinstance(category, str):
            grouped.setdefault(category, set()).add(name)
    seen: set[str] = set()
    for item in summary:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, "each category_summary item needs a string id")
            continue
        category = item["id"]
        if category in seen:
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"category_summary duplicates {category!r}")
        seen.add(category)
        skills = item.get("skills")
        if not isinstance(skills, list) or any(not isinstance(value, str) for value in skills):
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"category_summary {category!r}.skills must be a list of strings")
            continue
        if len(skills) != len(set(skills)):
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"category_summary {category!r}.skills contains duplicates")
        expected = grouped.get(category, set())
        if set(skills) != expected:
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"category_summary {category!r}.skills does not match canonical classification")
        count = item.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count != len(expected):
            model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"category_summary {category!r}.count is {count!r}; expected {len(expected)}")
    if seen != set(model.categories):
        model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, "category_summary ids do not match defined categories")


def _check_known_issue_references(model: RepositoryModel) -> None:
    import yaml
    from .model import UniqueKeyLoader

    path = model.root / "inventory/findings.yaml"
    finding_ids: set[str] = set()
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        findings = document.get("findings", []) if isinstance(document, dict) else []
        if isinstance(findings, list):
            finding_ids = {item["id"] for item in findings if isinstance(item, dict) and isinstance(item.get("id"), str)}
    except (OSError, yaml.YAMLError):
        pass
    for name, canonical in sorted(model.canonical_skills.items()):
        known = canonical.get("known_issues")
        if not isinstance(known, list):
            continue
        seen: set[str] = set()
        for item in known:
            if not isinstance(item, dict) or not isinstance(item.get("ref"), str) or not item["ref"].strip() or not isinstance(item.get("note"), str) or not item["note"].strip():
                model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"skill {name!r}.known_issues items require non-empty ref and note")
                continue
            ref = item["ref"]
            if ref in seen:
                model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"skill {name!r}.known_issues duplicates {ref!r}")
            seen.add(ref)
            if ref not in finding_ids:
                model.diagnostics.error("V-CFG-001", ".rules/skill-categories.yaml", 1, f"skill {name!r}.known_issues references missing finding {ref!r}")


def check_naming(model: RepositoryModel) -> None:
    naming = model.rules.get("naming", {}) if isinstance(model.rules.get("naming"), dict) else {}
    excluded: set[str] = set()
    for group in ("exceptions", "borderline"):
        items = naming.get(group, []) if isinstance(naming.get(group), list) else []
        for index, item in enumerate(items, 1):
            if not isinstance(item, dict):
                model.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"naming.{group} item #{index} must be a mapping")
                continue
            skill = item.get("skill")
            if not isinstance(skill, str) or not skill:
                got = type(skill).__name__
                model.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"naming.{group} item #{index} skill must be a string, got {got}")
                continue
            for field in ("reason", "note", "suffix"):
                value = item.get(field)
                if value is not None and not isinstance(value, str):
                    got = type(value).__name__
                    model.diagnostics.error("V-CFG-001", ".rules/skill-rules.yaml", 1, f"naming.{group} item #{index} {field} must be a string, got {got}")
            excluded.add(skill)
    seen: dict[str, Skill] = {}
    convention = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){2,}$")
    for skill in sorted(model.skills, key=lambda value: value.path.as_posix()):
        if not skill.name:
            model.diagnostics.error("V-NAM-002", skill.path, skill.line, "frontmatter name is missing")
            continue
        previous = seen.get(skill.name)
        if previous:
            model.diagnostics.error("V-NAM-002", skill.path, skill.line, f"frontmatter name duplicates {previous.path.relative_to(model.root)}")
        else:
            seen[skill.name] = skill
        if skill.directory.name != skill.name:
            model.diagnostics.error("V-NAM-003", skill.path, skill.line, f"directory name {skill.directory.name!r} does not match frontmatter name {skill.name!r}")
        if skill.name not in excluded and not convention.fullmatch(skill.name):
            model.diagnostics.warning("V-NAM-001", skill.path, skill.line, "name does not use service-target-action form")


def _reference_targets(skill: Skill):
    for number, line in enumerate(skill.lines, 1):
        for target in re.findall(r"`(references/[^`]+)`", line):
            yield number, target


def check_structure(model: RepositoryModel) -> None:
    for skill in model.skills:
        lines = skill.lines
        if len(lines) > MAX_LINES:
            model.diagnostics.error("V-STR-002", skill.path, 1, f"SKILL.md has {len(lines)} lines; limit is {MAX_LINES}")
        if len(lines) > IMPORTANT_LINES:
            model.diagnostics.warning("V-CMP-004", skill.path, 1, f"SKILL.md has {len(lines)} lines; keep required rules within the first {IMPORTANT_LINES}")
        for line, target in _reference_targets(skill):
            if not (skill.directory / target).exists():
                model.diagnostics.error("V-STR-003", skill.path, line, f"references missing path: {target}")
        _check_markdown_links(model, skill)
        _check_openai_metadata(model, skill)
        _check_owned_resources(model, skill)


def _check_owned_resources(model: RepositoryModel, skill: Skill) -> None:
    skill_text = skill.path.read_text(encoding="utf-8")
    references = skill.directory / "references"
    reference_paths = [path for path in sorted(references.rglob("*")) if path.is_file()] if references.is_dir() else []
    for path in reference_paths:
        relative = path.relative_to(skill.directory).as_posix()
        if relative not in skill_text:
            model.diagnostics.error("V-STR-005", path, 1, f"reference file is not owned by a direct SKILL.md reference: {relative}")
    scripts = skill.directory / "scripts"
    script_paths = [path for path in sorted(scripts.rglob("*")) if path.is_file() and "__pycache__" not in path.parts] if scripts.is_dir() else []
    owner_text = skill_text + "\n" + "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in reference_paths
    )
    for path in script_paths:
        relative = path.relative_to(skill.directory).as_posix()
        if relative not in owner_text and path.name not in owner_text:
            model.diagnostics.error("V-STR-005", path, 1, f"script file is not referenced by SKILL.md or references/: {relative}")


def _check_markdown_links(model: RepositoryModel, skill: Skill) -> None:
    for path in sorted(skill.directory.rglob("*.md")):
        for line, content in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for raw in LOCAL_LINK.findall(content):
                target = raw.strip().split(maxsplit=1)[0].strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                    continue
                if target.startswith("/") or "$" in target:
                    continue
                target = target.split("#", 1)[0]
                if target and not (path.parent / target).exists():
                    model.diagnostics.error("V-STR-004", path, line, f"local Markdown link target is missing: {raw}")


def _check_openai_metadata(model: RepositoryModel, skill: Skill) -> None:
    path = skill.directory / "agents/openai.yaml"
    if not path.is_file():
        model.diagnostics.error("V-STR-006", path, 1, "agents/openai.yaml is missing")
        return
    try:
        import yaml
        from .model import UniqueKeyLoader
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except Exception as exc:
        model.diagnostics.error("V-STR-006", path, 1, f"invalid YAML: {exc}")
        return
    interface = document.get("interface") if isinstance(document, dict) else None
    if not isinstance(interface, dict):
        model.diagnostics.error("V-STR-006", path, 1, "interface mapping is missing")
        return
    display_name = interface.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        model.diagnostics.error("V-STR-006", path, 1, "display_name is missing or empty")
    short = interface.get("short_description")
    if not isinstance(short, str) or not short.strip():
        model.diagnostics.error("V-STR-006", path, 1, "short_description is missing or empty")
    elif not 25 <= len(short) <= 64:
        model.diagnostics.error("V-STR-006", path, 1, f"short_description is {len(short)} chars; required range is 25..64")
    prompt = interface.get("default_prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        model.diagnostics.error("V-STR-006", path, 1, "default_prompt is missing or empty")
    elif skill.name and not re.search(rf"\${re.escape(skill.name)}(?:[^a-z0-9-]|$)", prompt):
        model.diagnostics.error("V-STR-006", path, 1, f"default_prompt does not reference ${skill.name}")


def check_publication(model: RepositoryModel) -> None:
    expected = {skill.path.relative_to(model.root).as_posix(): skill for skill in model.distributable_skills}
    actual: dict[str, int] = {}
    labels: dict[str, int] = {}
    for entry in model.readme_entries:
        path = entry.path.removeprefix("./")
        if path in actual:
            model.diagnostics.error("V-PUB-001", "README.md", entry.line, f"Available Skills duplicates {path}")
        actual[path] = entry.line
        if entry.name in labels:
            model.diagnostics.error("V-PUB-001", "README.md", entry.line, f"Available Skills duplicates label {entry.name!r}")
        labels[entry.name] = entry.line
        target = model.root / path
        target_skill = next((skill for skill in model.skills if skill.path.resolve(strict=False) == target.resolve(strict=False)), None)
        if target_skill is not None and entry.name != target_skill.name:
            model.diagnostics.error("V-PUB-001", "README.md", entry.line, f"link label {entry.name!r} does not match frontmatter name {target_skill.name!r}")
        expected_link = target_skill.path.relative_to(model.root).as_posix() if target_skill is not None else f"{entry.name}/SKILL.md"
        if path != expected_link:
            model.diagnostics.error("V-PUB-001", "README.md", entry.line, f"link path {path!r} does not match expected {expected_link!r}")
        if path.startswith(tuple(f"{item}/" for item in EXCLUDED_DIRS | {".claude"})):
            model.diagnostics.error("V-ARC-002", "README.md", entry.line, f"excluded or maintenance skill must not be public: {path}")
        if not entry.dependency:
            model.diagnostics.error("V-PUB-001", "README.md", entry.line, "External Dependencies cell must not be empty")
    for path, skill in sorted(expected.items()):
        if path not in actual:
            model.diagnostics.error("V-PUB-001", "README.md", 1, f"Available Skills is missing: {path}")
    for path, line in sorted(actual.items()):
        if path not in expected and not path.startswith(".claude/") and not path.startswith(tuple(f"{item}/" for item in EXCLUDED_DIRS)):
            model.diagnostics.error("V-PUB-001", "README.md", line, f"Available Skills references missing skill: {path}")
    _check_readme_table_shape(model)
    _check_badge(model, len(expected))
    _check_public_layout(model)


def _check_public_layout(model: RepositoryModel) -> None:
    for skill in model.skills:
        relative = skill.path.relative_to(model.root)
        valid = (
            len(relative.parts) == 2
            and relative.parts[1] == "SKILL.md"
            and not relative.parts[0].startswith(".")
        ) or (
            len(relative.parts) == 4
            and relative.parts[:2] == (".claude", "skills")
            and relative.parts[3] == "SKILL.md"
        ) or (
            len(relative.parts) == 4
            and relative.parts[0] == "skills"
            and relative.parts[3] == "SKILL.md"
        )
        if not valid:
            model.diagnostics.error("V-PUB-002", skill.path, 1, "SKILL.md is outside the allowed public depth")

    roots: list[Path] = []
    roots.extend(path for path in model.root.iterdir() if not path.name.startswith(".") and (path.is_dir() or path.is_symlink()))
    maintenance = model.root / ".claude/skills"
    if maintenance.is_dir():
        roots.extend(path for path in maintenance.iterdir() if path.is_dir() or path.is_symlink())
    resolved: dict[Path, Path] = {}
    for path in sorted(roots, key=lambda item: item.as_posix()):
        try:
            path.lstat()
        except OSError as exc:
            model.diagnostics.error("V-PUB-002", path, 1, f"cannot lstat public skill root: {exc.strerror or exc}")
            continue
        if path.is_symlink() and not path.exists():
            model.diagnostics.error("V-PUB-002", path, 1, "public skill symlink is broken")
            continue
        skill_file = path / "SKILL.md"
        if not skill_file.is_file():
            continue
        target = skill_file.resolve(strict=False)
        previous = resolved.get(target)
        if previous is not None and previous != path:
            model.diagnostics.error("V-PUB-002", path, 1, f"public skill root resolves to the same SKILL.md as {previous.relative_to(model.root)}")
        else:
            resolved[target] = path


def _check_readme_table_shape(model: RepositoryModel) -> None:
    headers = 0
    invalid = False
    for line in model.readme_lines:
        if line.startswith("| Skill |"):
            headers += 1
            invalid |= line != "| Skill | Description | External Dependencies |"
    if not headers or not model.readme_entries or invalid:
        model.diagnostics.error("V-PUB-001", "README.md", 1, "skill tables must use Skill | Description | External Dependencies")


def _check_badge(model: RepositoryModel, expected: int) -> None:
    badge = next((re.search(r"badgen\.net/static/skills/(\d+)/", line) for line in model.readme_lines if "badgen.net/static/skills/" in line), None)
    if badge is None:
        model.diagnostics.error("V-ARC-003", "README.md", 1, "Skills badge is missing")
    elif int(badge.group(1)) != expected:
        model.diagnostics.error("V-ARC-003", "README.md", 1, f"Skills badge count is {badge.group(1)}; expected {expected}")


CHECKS = (check_categories, check_naming, check_structure, check_publication)
