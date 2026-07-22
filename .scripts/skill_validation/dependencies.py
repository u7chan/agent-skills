"""Canonical dependency, external dependency, and complexity checks.

Only ``skills[*].depends_on`` in ``skill-categories.yaml`` forms the graph
used by ERROR checks and complexity calculations.  Text extraction and the
Phase 1 inventory are deliberately advisory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shlex
from typing import Any

import yaml

from .model import RepositoryModel, Skill, UniqueKeyLoader
from .external import (
    declared_matches,
    javascript_source_evidence,
    normalize_dependency_name,
    python_source_evidence,
)


CANONICAL_PATH = Path(".rules/skill-categories.yaml")
INVENTORY_PATH = Path("inventory/skills.yaml")
EDGE_CONDITIONS = {"unconditional", "conditional"}
TYPE_BY_SYMBOL = {"R": "required", "C": "conditional", "O": "optional", "F": "fallback"}
SYMBOL_BY_TYPE = {value: key for key, value in TYPE_BY_SYMBOL.items()}
TYPE_PRIORITY = {"fallback": 0, "optional": 1, "conditional": 2, "required": 3}
MARKDOWN_LINK = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
DYNAMIC_PATH = re.compile(r"(?:\$\{?[^/\s}]+\}?|<[^>/\s]+>|\{[^}/\s]+\})")
NAKED_PATH = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"(?:/|\.\.?/)?(?:[A-Za-z0-9_.${}<>{}-]+/)+[A-Za-z0-9_.${}<>{}-]+"
)
EXTERNAL_COMMAND_ALIASES = {
    "bun": ("bun",),
    "cagent": ("cagent",),
    "claude": ("claude", "agent cli"),
    "codex": ("codex", "agent cli"),
    "gh": ("gh",),
    "git": ("git",),
    "herdr": ("herdr",),
    "inkscape": ("inkscape",),
    "jq": ("jq",),
    "node": ("node", "nodejs"),
    "npm": ("npm",),
    "npx": ("npx",),
    "playwright": ("playwright",),
    "playwright-cli": ("playwright", "playwright cli"),
    "python": ("python", "python3"),
    "python3": ("python", "python3"),
    "rg": ("rg", "ripgrep"),
    "rsvg-convert": ("librsvg", "rsvgconvert"),
    "opencode": ("opencode", "agent cli"),
    "uv": ("uv",),
}
PYTHON_IMPORT_ALIASES = {
    "PIL": ("pil", "pillow"),
    "cv2": ("cv2", "opencv", "opencv python"),
    "yaml": ("yaml", "pyyaml"),
}
SHELL_BUILTINS_AND_STANDARD = {
    ".", "[", "alias", "break", "case", "cd", "command", "continue", "do", "done",
    "echo", "elif", "else", "env", "esac", "eval", "exec", "exit", "export", "false",
    "fi", "for", "function", "getopts", "hash", "if", "local", "printf", "pwd", "read",
    "readonly", "return", "set", "shift", "test", "then", "time", "trap", "true", "type",
    "typeset", "ulimit", "umask", "unalias", "unset", "until", "wait", "while",
    "source",
    "awk", "basename", "cat", "chmod", "cmp", "cp", "cut", "date", "dirname", "find",
    "grep", "head", "ln", "ls", "mkdir", "mktemp", "mv", "readlink", "rm", "sed", "sort",
    "tail", "tee", "touch", "tr", "wc", "xargs",
}


@dataclass(frozen=True)
class ExternalDependency:
    name: str
    kind: str


@dataclass(frozen=True)
class ExternalDependencyView:
    direct: tuple[ExternalDependency, ...]
    transitive: tuple[ExternalDependency, ...]
    effective: tuple[ExternalDependency, ...]


def _canonical_line(model: RepositoryModel, name: str) -> int:
    text = (model.root / CANONICAL_PATH).read_text(encoding="utf-8")
    match = re.search(rf"^\s*-\s+name:\s*{re.escape(name)}\s*(?:#.*)?$", text, re.MULTILINE)
    return text[:match.start()].count("\n") + 1 if match else 1


def _relation_values(entry: dict[str, Any], key: str) -> list[Any]:
    value = entry.get(key, [])
    return value if isinstance(value, list) else []


def _canonical_edges(model: RepositoryModel) -> dict[str, tuple[str, ...]]:
    """Return the valid active subset of the canonical depends_on graph."""
    active = set(model.canonical_skills) & set(model.skill_by_name)
    result: dict[str, tuple[str, ...]] = {}
    for name in sorted(active):
        raw = model.canonical_skills[name].get("depends_on", [])
        values = raw if isinstance(raw, list) else []
        result[name] = tuple(sorted({target for target in values if isinstance(target, str) and target in active}))
    return result


def _edge_conditions(model: RepositoryModel, name: str) -> dict[str, str]:
    raw = model.canonical_skills[name].get("depends_on_edge_condition", {})
    if not isinstance(raw, dict):
        return {}
    return {target: value for target, value in raw.items() if isinstance(target, str) and value in EDGE_CONDITIONS}


def _archive_skills(model: RepositoryModel) -> set[str]:
    names: set[str] = set()
    archive = model.root / ".archive"
    if not archive.is_dir():
        return names
    for path in sorted(archive.rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*([^\s#]+)", text, re.MULTILINE)
        names.add(match.group(1) if match else path.parent.name)
    return names


def _note_relations(model: RepositoryModel) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    notes = model.categories_document.get("dependency_notes", {})
    routes = notes.get("routes_to_not_depends", {}) if isinstance(notes, dict) else {}
    items = routes.get("items", []) if isinstance(routes, dict) else []
    if not isinstance(items, list):
        return result
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("from"), str):
            continue
        relation = item.get("relation")
        if not isinstance(relation, str):
            continue
        targets = item.get("to")
        for target in targets if isinstance(targets, list) else [targets]:
            if isinstance(target, str):
                result.append((item["from"], target, relation))
    return result


def _check_relation_targets(model: RepositoryModel) -> None:
    active = set(model.canonical_skills) & set(model.skill_by_name)
    archived = _archive_skills(model)
    for name, entry in sorted(model.canonical_skills.items()):
        line = _canonical_line(model, name)
        for relation in ("depends_on", "routes_to"):
            raw = entry.get(relation, [])
            if not isinstance(raw, list):
                model.diagnostics.error("V-DEP-006", CANONICAL_PATH, line, f"{name}.{relation} must be a list")
                continue
            seen: set[str] = set()
            for target in raw:
                if not isinstance(target, str) or not target:
                    model.diagnostics.error("V-DEP-006", CANONICAL_PATH, line, f"{name}.{relation} contains a non-string or empty target")
                    continue
                if target in seen:
                    model.diagnostics.error("V-DEP-006", CANONICAL_PATH, line, f"{name}.{relation} duplicates {target!r}")
                seen.add(target)
                _check_relation_target(model, name, relation, target, active, archived, line)
    _check_note_relations(model, active, archived)


def _check_note_relations(model: RepositoryModel, active: set[str], archived: set[str]) -> None:
    notes = model.categories_document.get("dependency_notes")
    routes = notes.get("routes_to_not_depends") if isinstance(notes, dict) else None
    items = routes.get("items") if isinstance(routes, dict) else None
    if not isinstance(items, list):
        model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, "dependency_notes.routes_to_not_depends.items must be a list")
        return
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} must be a mapping")
            continue
        source, relation, raw_targets = item.get("from"), item.get("relation"), item.get("to")
        if not isinstance(relation, str) or not relation:
            got = type(relation).__name__
            model.diagnostics.error("V-CFG-001", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} relation must be a string, got {got}")
            continue
        if relation not in {"routes_to", "mention", "used_by"}:
            model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} has invalid relation {relation!r}")
        if not isinstance(source, str) or not source:
            model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} has invalid from")
            continue
        _check_relation_target(model, "dependency_notes", "from", source, active, archived, 1)
        targets = raw_targets if isinstance(raw_targets, list) else [raw_targets]
        if not targets:
            model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} has no to target")
        target_seen: set[str] = set()
        for target in targets:
            if not isinstance(target, str) or not target:
                model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} has invalid to")
                continue
            if target in target_seen:
                model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends item #{index} duplicates to {target!r}")
            target_seen.add(target)
            key = (source, target, str(relation))
            if key in seen:
                model.diagnostics.error("V-DEP-006", CANONICAL_PATH, 1, f"routes_to_not_depends duplicates {source} -> {target} ({relation})")
            seen.add(key)
            _check_relation_target(model, source, str(relation), target, active, archived, 1)


def _check_relation_target(
    model: RepositoryModel,
    source: str,
    relation: str,
    target: str,
    active: set[str],
    archived: set[str],
    line: int,
) -> None:
    if target in archived:
        message = f"active skill {source!r} {relation} references archived skill {target!r}"
        model.diagnostics.error("V-DEP-006", CANONICAL_PATH, line, message)
        model.diagnostics.error("V-ARC-001", CANONICAL_PATH, line, message)
    elif target not in active:
        model.diagnostics.error("V-DEP-006", CANONICAL_PATH, line, f"{source}.{relation} references missing active skill {target!r}")


def _check_edge_conditions(model: RepositoryModel) -> None:
    for name, entry in sorted(model.canonical_skills.items()):
        line = _canonical_line(model, name)
        raw = entry.get("depends_on_edge_condition", {})
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            model.diagnostics.error("V-DEP-007", CANONICAL_PATH, line, f"{name}.depends_on_edge_condition must be a mapping")
            continue
        targets = {value for value in _relation_values(entry, "depends_on") if isinstance(value, str)}
        for target, condition in raw.items():
            if not isinstance(target, str) or not target:
                model.diagnostics.error("V-DEP-007", CANONICAL_PATH, line, f"{name}.depends_on_edge_condition contains an invalid target")
                continue
            if target not in targets:
                model.diagnostics.error("V-DEP-007", CANONICAL_PATH, line, f"edge condition target {target!r} is not in {name}.depends_on")
            if condition not in EDGE_CONDITIONS:
                model.diagnostics.error("V-DEP-007", CANONICAL_PATH, line, f"edge condition for {name} -> {target} must be unconditional or conditional")


def _strongly_connected_components(edges: dict[str, tuple[str, ...]]) -> list[tuple[str, ...]]:
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    result: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in edges.get(node, ()):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        result.append(tuple(sorted(component)))

    for node in sorted(edges):
        if node not in indices:
            visit(node)
    return sorted(result)


def _cycle_path(component: tuple[str, ...], edges: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    if len(component) == 1:
        return (component[0], component[0])
    allowed = set(component)
    start = component[0]

    def find(node: str, path: tuple[str, ...]) -> tuple[str, ...] | None:
        for target in edges[node]:
            if target not in allowed:
                continue
            if target == start:
                return (*path, start)
            if target not in path:
                found = find(target, (*path, target))
                if found:
                    return found
        return None

    return find(start, (start,)) or (*component, start)


def _check_cycles(model: RepositoryModel, edges: dict[str, tuple[str, ...]]) -> None:
    for component in _strongly_connected_components(edges):
        cyclic = len(component) > 1 or component[0] in edges.get(component[0], ())
        if cyclic:
            path = _cycle_path(component, edges)
            model.diagnostics.error("V-DEP-001", CANONICAL_PATH, _canonical_line(model, path[0]), f"depends_on cycle: {' -> '.join(path)}")


def _check_category_direction(model: RepositoryModel, edges: dict[str, tuple[str, ...]]) -> None:
    for source in sorted(edges):
        source_entry = model.canonical_skills[source]
        source_category_id = source_entry.get("category")
        source_category = model.categories.get(source_category_id) if isinstance(source_category_id, str) else None
        if source_category is None:
            continue
        for target in edges[source]:
            target_entry = model.canonical_skills[target]
            target_category_id = target_entry.get("category")
            target_category = model.categories.get(target_category_id) if isinstance(target_category_id, str) else None
            if target_category is None or source_category.get("id") == target_category.get("id"):
                continue
            allowed = source_category.get("allowed_depends_on", [])
            inbound = target_category.get("may_be_depended_on_by", [])
            failures: list[str] = []
            if not isinstance(allowed, list) or target_category.get("id") not in allowed:
                failures.append(f"{target_category.get('id')} is not in {source_category.get('id')}.allowed_depends_on")
            if inbound and (not isinstance(inbound, list) or source_category.get("id") not in inbound):
                failures.append(f"{source_category.get('id')} is not in {target_category.get('id')}.may_be_depended_on_by")
            if failures:
                model.diagnostics.error("V-DEP-002", CANONICAL_PATH, _canonical_line(model, source), f"invalid category edge {source} -> {target}: {'; '.join(failures)}")
            if source_category.get("order") == target_category.get("order"):
                model.diagnostics.warning("V-DEP-004", CANONICAL_PATH, _canonical_line(model, source), f"different categories with the same order: {source} -> {target}")


def _text_skill_mentions(model: RepositoryModel, skill: Skill) -> set[str]:
    text = skill.path.read_text(encoding="utf-8")
    return {
        name for name in model.canonical_skills
        if name != skill.name and re.search(rf"(?<![a-z0-9-]){re.escape(name)}(?![a-z0-9-])", text)
    }


def _check_extracted_relations(model: RepositoryModel) -> None:
    non_dependencies = {(source, target) for source, target, relation in _note_relations(model) if relation in {"routes_to", "mention", "used_by"}}
    for skill in sorted(model.skills, key=lambda item: item.name):
        if not skill.name or skill.name not in model.canonical_skills:
            continue
        canonical = {value for value in _relation_values(model.canonical_skills[skill.name], "depends_on") if isinstance(value, str)}
        extracted = {
            target for target in _text_skill_mentions(model, skill)
            if (skill.name, target) not in non_dependencies
        }
        if canonical == extracted:
            continue
        parts: list[str] = []
        if canonical - extracted:
            parts.append("canonical-only=" + ", ".join(sorted(canonical - extracted)))
        if extracted - canonical:
            parts.append("text-only=" + ", ".join(sorted(extracted - canonical)))
        model.diagnostics.warning("V-DEP-005", skill.path, 1, "depends_on differs from heuristic SKILL.md mentions: " + "; ".join(parts))


def _candidate_tokens(line: str, in_fence: bool) -> set[str]:
    candidates = {match.group(1).strip().split(maxsplit=1)[0].strip("<>") for match in MARKDOWN_LINK.finditer(line)}
    fragments = [match.group(1) for match in INLINE_CODE.finditer(line)]
    if in_fence:
        fragments.append(line)
    fragments.append(line)
    for fragment in fragments:
        for token in re.split(r"\s+", fragment):
            token = token.strip("`'\"(),;:[]").rstrip(".。")
            if "/" in token:
                candidates.add(token)
    candidates.update(match.group(0) for match in NAKED_PATH.finditer(line))
    return {value.split("#", 1)[0] for value in candidates if value}


def _path_target(
    model: RepositoryModel,
    source_path: Path,
    raw: str,
    roots: list[tuple[str, Path]],
) -> tuple[str | None, bool]:
    """Return (other skill name, dynamic candidate)."""
    cleaned = raw.rstrip("\\").strip()
    if cleaned.startswith(("http://", "https://", "mailto:", "#")):
        return None, False
    dynamic = bool(DYNAMIC_PATH.search(cleaned))
    root_names = {name for name, _ in roots}
    mentioned = next((name for name in sorted(root_names, key=len, reverse=True) if re.search(rf"(?<![a-z0-9-]){re.escape(name)}(?=/|$)", cleaned)), None)
    source_name = next((name for name, root in roots if source_path.is_relative_to(root)), None)
    if dynamic:
        if "-worktrees/" in cleaned:
            return None, False
        if "/../" not in cleaned and re.search(r"(?:<skill-dir>|\$\{?SKILL_DIR\}?)/(?:SKILL\.md|references/|scripts/|agents/|tests/)", cleaned, re.IGNORECASE):
            return source_name, False
        if ".claude/skills" in cleaned:
            if mentioned is not None and mentioned != source_name:
                return mentioned, True
            return None, False
        unresolved_cross_skill = bool(re.search(r"(?:\.\./|/\.\./).*(?:SKILL\.md|references/|scripts/)", cleaned))
        return mentioned, mentioned is not None or unresolved_cross_skill
    path = Path(cleaned)
    attempts = [path] if path.is_absolute() else [source_path.parent / path, model.root / path]
    matches: list[str] = []
    for attempt in attempts:
        normalized = attempt.resolve(strict=False)
        for name, root in roots:
            try:
                normalized.relative_to(root.resolve(strict=False))
            except ValueError:
                continue
            matches.append(name)
    target = next((name for name in matches if name != source_name), None)
    return (target or (matches[0] if matches else None)), False


def _check_physical_references(model: RepositoryModel) -> None:
    roots = sorted(((skill.name, skill.directory) for skill in model.skills if skill.name), key=lambda item: item[1].as_posix())
    for skill in sorted(model.skills, key=lambda item: item.path.as_posix()):
        paths = [skill.path]
        references = skill.directory / "references"
        if references.is_dir():
            paths.extend(path for path in sorted(references.rglob("*")) if path.is_file())
        for path in paths:
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            in_fence = False
            for number, line in enumerate(lines, 1):
                if line.lstrip().startswith(("```", "~~~")):
                    in_fence = not in_fence
                    continue
                for raw in sorted(_candidate_tokens(line, in_fence)):
                    target, dynamic = _path_target(model, path, raw, roots)
                    if target == skill.name:
                        continue
                    if dynamic:
                        if target is None:
                            model.diagnostics.warning("V-DEP-003", path, number, f"dynamic physical path candidate cannot be resolved: {raw}")
                        else:
                            model.diagnostics.error("V-DEP-003", path, number, f"dynamic physical path references another active skill {target!r}: {raw}")
                    elif target is None:
                        continue
                    else:
                        model.diagnostics.error("V-DEP-003", path, number, f"physical path references another active skill {target!r}: {raw}")


def _normalize_dependency_name(value: str) -> str:
    return normalize_dependency_name(value)


def _merge_dependency(target: dict[str, ExternalDependency], dependency: ExternalDependency) -> None:
    key = _normalize_dependency_name(dependency.name)
    existing = target.get(key)
    if existing is None or TYPE_PRIORITY[dependency.kind] > TYPE_PRIORITY[existing.kind]:
        target[key] = dependency


def _parse_external_cell(
    model: RepositoryModel,
    skill_name: str,
    cell: str,
    line: int,
    emit: bool,
) -> dict[str, ExternalDependency]:
    result: dict[str, ExternalDependency] = {}
    if cell.strip() == "—":
        return result
    for raw_item in cell.split(","):
        item = " ".join(raw_item.strip().split())
        if not item:
            if emit:
                model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has an empty dependency item")
            continue
        annotations = re.findall(r"\(([^()]*)\)", item)
        malformed = item.count("(") != item.count(")")
        if malformed:
            if emit:
                model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has an unclosed dependency annotation: {item}")
            continue
        if ("(" in item or ")" in item) and not annotations:
            if emit:
                model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has a malformed dependency annotation: {item}")
            continue
        if len(annotations) > 1:
            if emit:
                model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has multiple dependency annotations: {item}")
            continue
        kind = "required"
        name = item
        if annotations:
            annotation = annotations[0].strip()
            suffix = re.search(r"\(\s*([^()]*)\s*\)\s*$", item)
            if suffix is None or annotation not in TYPE_BY_SYMBOL:
                if emit:
                    model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has unknown dependency type annotation: {item}")
                continue
            kind = TYPE_BY_SYMBOL[annotation]
            name = item[:suffix.start()].strip()
        if not name or name == "—":
            if emit:
                model.diagnostics.error("V-EXT-001", "README.md", line, f"{skill_name} has an invalid dependency name: {item}")
            continue
        _merge_dependency(result, ExternalDependency(name, kind))
    return result


def _readme_dependencies(model: RepositoryModel, emit: bool) -> dict[str, dict[str, ExternalDependency]]:
    entries: dict[str, list[Any]] = {}
    for entry in model.readme_entries:
        entries.setdefault(entry.path.removeprefix("./"), []).append(entry)
    result: dict[str, dict[str, ExternalDependency]] = {name: {} for name in model.canonical_skills}
    distributable = {skill.name for skill in model.distributable_skills if skill.name}
    for name in sorted(distributable):
        skill = model.skill_by_name[name]
        expected_path = skill.path.relative_to(model.root).as_posix()
        matches = entries.get(expected_path, [])
        if not matches:
            if emit:
                model.diagnostics.error("V-EXT-005", "README.md", 1, f"distributed skill {name!r} has no External Dependencies cell")
            continue
        if len(matches) > 1 and emit:
            model.diagnostics.error("V-EXT-005", "README.md", matches[1].line, f"distributed skill {name!r} has duplicate External Dependencies cells")
        entry = matches[0]
        if not entry.dependency.strip():
            if emit:
                model.diagnostics.error("V-EXT-005", "README.md", entry.line, f"distributed skill {name!r} has an empty External Dependencies cell")
            continue
        result[name] = _parse_external_cell(model, name, entry.dependency, entry.line, emit)
    return result


def _external_dependency_views(
    model: RepositoryModel,
    direct: dict[str, dict[str, ExternalDependency]],
    edges: dict[str, tuple[str, ...]],
) -> tuple[dict[str, ExternalDependencyView], set[str]]:
    cache: dict[str, tuple[dict[str, ExternalDependency], dict[str, ExternalDependency]]] = {}
    unresolvable: set[str] = set()

    def calculate(name: str, stack: tuple[str, ...]) -> tuple[dict[str, ExternalDependency], dict[str, ExternalDependency]]:
        if name in cache:
            return cache[name]
        if name in stack:
            unresolvable.update(stack[stack.index(name):])
            return {}, dict(direct.get(name, {}))
        transitive: dict[str, ExternalDependency] = {}
        for target in edges.get(name, ()):
            _, target_effective = calculate(target, (*stack, name))
            conditional_edge = _edge_conditions(model, name).get(target, "unconditional") == "conditional"
            for dependency in target_effective.values():
                if dependency.kind in {"optional", "fallback"}:
                    continue
                inherited = ExternalDependency(dependency.name, "conditional" if conditional_edge else dependency.kind)
                _merge_dependency(transitive, inherited)
        effective = dict(transitive)
        for dependency in direct.get(name, {}).values():
            key = _normalize_dependency_name(dependency.name)
            inherited = effective.get(key)
            if inherited is None or TYPE_PRIORITY[dependency.kind] >= TYPE_PRIORITY[inherited.kind]:
                effective[key] = dependency
        cache[name] = transitive, effective
        return cache[name]

    views: dict[str, ExternalDependencyView] = {}
    for name in sorted(edges):
        transitive, effective = calculate(name, ())
        ordered = lambda values: tuple(sorted(values.values(), key=lambda item: (_normalize_dependency_name(item.name), item.kind)))
        views[name] = ExternalDependencyView(ordered(direct.get(name, {})), ordered(transitive), ordered(effective))
    return views, unresolvable


def external_dependency_views(model: RepositoryModel) -> dict[str, ExternalDependencyView]:
    """Build graph-renderer data without emitting a second set of diagnostics."""
    direct = _readme_dependencies(model, emit=False)
    for skill in model.skills:
        if skill.classification != "maintenance" or not skill.name or not isinstance(skill.canonical, dict):
            continue
        raw = skill.canonical.get("external_dependencies")
        if not isinstance(raw, list):
            continue
        deps: dict[str, ExternalDependency] = {}
        for item in raw:
            if isinstance(item, str):
                name = _normalize_dependency_name(item)
                _merge_dependency(deps, ExternalDependency(name, "required"))
        direct.setdefault(skill.name, {}).update(deps)
    views, _ = _external_dependency_views(model, direct, _canonical_edges(model))
    return views


def _inventory_dependencies(model: RepositoryModel) -> dict[str, dict[str, str]] | None:
    path = model.root / INVENTORY_PATH
    if not path.is_file():
        return None
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError):
        return None
    items = document.get("skills", []) if isinstance(document, dict) else []
    if not isinstance(items, list):
        return None
    result: dict[str, dict[str, str]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        dependencies: dict[str, str] = {}
        raw = item.get("external_dependencies", [])
        if isinstance(raw, list):
            for dependency in raw:
                if isinstance(dependency, dict) and isinstance(dependency.get("name"), str) and dependency.get("type") in SYMBOL_BY_TYPE:
                    dependencies[_normalize_dependency_name(dependency["name"])] = dependency["type"]
        result[item["name"]] = dependencies
    return result


def _check_inventory(model: RepositoryModel, direct: dict[str, dict[str, ExternalDependency]]) -> None:
    inventory = _inventory_dependencies(model)
    if inventory is None:
        model.diagnostics.warning("V-EXT-003", INVENTORY_PATH, 1, "inventory snapshot is missing or invalid")
        return
    for name in sorted(set(direct) | set(inventory)):
        readme = {key: dependency.kind for key, dependency in direct.get(name, {}).items()}
        snapshot = inventory.get(name, {})
        if readme == snapshot:
            continue
        parts: list[str] = []
        if readme.keys() - snapshot.keys():
            parts.append("README-only=" + ", ".join(sorted(readme.keys() - snapshot.keys())))
        if snapshot.keys() - readme.keys():
            parts.append("inventory-only=" + ", ".join(sorted(snapshot.keys() - readme.keys())))
        mismatched = sorted(key for key in readme.keys() & snapshot.keys() if readme[key] != snapshot[key])
        if mismatched:
            parts.append("type mismatch=" + ", ".join(f"{key} ({readme[key]} != {snapshot[key]})" for key in mismatched))
        model.diagnostics.warning("V-EXT-003", INVENTORY_PATH, 1, f"{name}: " + "; ".join(parts))


def _declared_external_text(model: RepositoryModel) -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in model.readme_entries:
        chunks = [re.sub(r"\([^()]*\)", "", item) for item in entry.dependency.split(",")]
        path = entry.path.removeprefix("./")
        skill = next((item for item in model.distributable_skills if item.path.relative_to(model.root).as_posix() == path), None)
        if skill and skill.name:
            result[skill.name] = " ".join(_normalize_dependency_name(chunk) for chunk in chunks)
    for skill in model.skills:
        if skill.classification != "maintenance" or not skill.name or not isinstance(skill.canonical, dict):
            continue
        raw = skill.canonical.get("external_dependencies")
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            result[skill.name] = " ".join(_normalize_dependency_name(item) for item in raw)
    return result


def _python_import_evidence(skill: Skill, repo_root: Path) -> list[tuple[Path, int, str]]:
    scripts = skill.directory / "scripts"
    if not scripts.is_dir():
        return []
    local_modules = {path.stem for path in scripts.rglob("*.py")}
    local_modules.update(path.parent.name for path in scripts.rglob("__init__.py"))
    result: list[tuple[Path, int, str]] = []
    for path in sorted(scripts.rglob("*.py")):
        for line, kind, dependency in python_source_evidence(path, repo_root, local_modules):
            if kind == "python-import":
                result.append((path, line, dependency))
    return result


def _source_command_evidence(skill: Skill, repo_root: Path) -> list[tuple[Path, int, str]]:
    scripts = skill.directory / "scripts"
    if not scripts.is_dir():
        return []
    local_modules = {path.stem for path in scripts.rglob("*.py")}
    local_modules.update(path.parent.name for path in scripts.rglob("__init__.py"))
    result: list[tuple[Path, int, str]] = []
    for path in sorted(scripts.rglob("*.py")):
        for line, kind, dependency in python_source_evidence(path, repo_root, local_modules):
            if kind == "command":
                result.append((path, line, dependency))
    for suffix in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs", "*.cjs"):
        for path in sorted(scripts.rglob(suffix)):
            result.extend((path, line, dependency) for line, _kind, dependency in javascript_source_evidence(path))
    return sorted(set(result), key=lambda item: (item[0].as_posix(), item[1], item[2]))


def _shell_command_evidence(skill: Skill) -> list[tuple[Path, int, str]]:
    result: list[tuple[Path, int, str]] = []
    paths: list[tuple[Path, bool]] = [(skill.path, True)]
    references = skill.directory / "references"
    if references.is_dir():
        paths.extend((path, True) for path in sorted(references.rglob("*.md")) if path.is_file())
    scripts = skill.directory / "scripts"
    if scripts.is_dir():
        paths.extend((path, False) for path in sorted(scripts.rglob("*.sh")) if path.is_file())
        for path in sorted(scripts.rglob("*.py")):
            try:
                first = path.read_text(encoding="utf-8").splitlines()[0]
            except (OSError, UnicodeDecodeError, IndexError):
                continue
            match = re.match(r"^#!.*\b(python3?)\b", first)
            if match:
                result.append((path, 1, match.group(1)))
    for path, markdown in paths:
        in_fence = False
        shell_fence = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if markdown and line.lstrip().startswith(("```", "~~~")):
                if not in_fence:
                    language = line.lstrip()[3:].strip().casefold()
                    shell_fence = language in {"bash", "sh", "shell", "console", "zsh"}
                in_fence = not in_fence
                if not in_fence:
                    shell_fence = False
                continue
            for match in re.finditer(r"\bcommand\s+-v\s+([a-zA-Z0-9_.+-]+)", line):
                result.append((path, number, match.group(1)))
            fragments = [match.group(1) for match in INLINE_CODE.finditer(line)]
            if in_fence or not markdown:
                fragments.append(line)
            for fragment in fragments:
                fragment = re.sub(r"<[^>]*>", "<placeholder>", fragment)
                for segment in re.split(r"(?:^|&&|\|\||[|;])\s*", fragment):
                    segment = re.sub(r"^[A-Z_][A-Z0-9_]*=(?:\S+|\"[^\"]*\")\s+", "", segment.strip())
                    if not segment or segment.startswith(("#", "$", "<")):
                        continue
                    try:
                        command = shlex.split(segment, comments=True)[0]
                    except (ValueError, IndexError):
                        continue
                    command = Path(command).name
                    generic_command = bool(re.fullmatch(r"[a-z][a-z0-9_.+-]*", command))
                    if command not in SHELL_BUILTINS_AND_STANDARD and (command in EXTERNAL_COMMAND_ALIASES or (shell_fence or not markdown) and generic_command):
                        result.append((path, number, command))
    return sorted(set(result), key=lambda item: (item[0].as_posix(), item[1], item[2]))


def _evidence_is_declared(evidence: str, declared: str) -> bool:
    return declared_matches(evidence, declared)


def _check_external_evidence(model: RepositoryModel) -> None:
    declared = _declared_external_text(model)
    for skill in sorted(model.skills, key=lambda item: item.name):
        text = declared.get(skill.name, "")
        if skill.classification == "maintenance" and isinstance(skill.canonical, dict) and "external_dependencies" not in skill.canonical:
            model.diagnostics.error("V-EXT-004", CANONICAL_PATH, _canonical_line(model, skill.name), f"maintenance skill {skill.name!r} has no external dependency declaration source")
        seen: set[tuple[str, str]] = set()
        source = "canonical maintenance declaration" if skill.classification == "maintenance" else "README"
        for path, line, module in _python_import_evidence(skill, model.root):
            key = ("import", module)
            if key in seen or _evidence_is_declared(module, text):
                continue
            seen.add(key)
            model.diagnostics.error("V-EXT-004", path, line, f"external Python import {module!r} is not declared in {source}")
        for path, line, command in [*_shell_command_evidence(skill), *_source_command_evidence(skill, model.root)]:
            key = ("command", command)
            if key in seen or _evidence_is_declared(command, text):
                continue
            seen.add(key)
            model.diagnostics.error("V-EXT-004", path, line, f"external command {command!r} is not declared in {source}")


def _longest_depth(name: str, edges: dict[str, tuple[str, ...]], stack: tuple[str, ...] = ()) -> int | None:
    if name in stack:
        return None
    depths = [_longest_depth(target, edges, (*stack, name)) for target in edges.get(name, ())]
    if any(depth is None for depth in depths):
        return None
    return max((depth + 1 for depth in depths if depth is not None), default=0)


def _check_complexity(model: RepositoryModel, edges: dict[str, tuple[str, ...]]) -> None:
    inbound = {name: 0 for name in edges}
    for source in sorted(edges):
        count = len(edges[source])
        if count > 7:
            model.diagnostics.warning("V-CMP-002", CANONICAL_PATH, _canonical_line(model, source), f"{source} has {count} direct dependencies; limit is 7")
        for target in edges[source]:
            inbound[target] += 1
        depth = _longest_depth(source, edges)
        if depth is not None and depth > 3:
            model.diagnostics.warning("V-CMP-001", CANONICAL_PATH, _canonical_line(model, source), f"{source} has longest dependency depth {depth}; limit is 3")
    for target, count in sorted(inbound.items()):
        if count > 5:
            model.diagnostics.warning("V-CMP-003", CANONICAL_PATH, _canonical_line(model, target), f"{target} is directly depended on by {count} skills; limit is 5")


def check(model: RepositoryModel) -> None:
    _check_relation_targets(model)
    _check_edge_conditions(model)
    edges = _canonical_edges(model)
    _check_cycles(model, edges)
    _check_category_direction(model, edges)
    _check_physical_references(model)
    _check_extracted_relations(model)
    direct = _readme_dependencies(model, emit=True)
    _, unresolvable = _external_dependency_views(model, direct, edges)
    for name in sorted(unresolvable):
        model.diagnostics.warning("V-EXT-002", CANONICAL_PATH, _canonical_line(model, name), f"effective external dependencies are not calculable because {name!r} is cyclic")
    _check_inventory(model, direct)
    _check_external_evidence(model)
    _check_complexity(model, edges)


def register(register_check, register_graph_renderer) -> None:
    del register_graph_renderer
    register_check(check)
