"""Deterministic Markdown rendering for the canonical dependency graph."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from .dependencies import ExternalDependency, external_dependency_views
from .model import RepositoryModel


class GraphOutputError(RuntimeError):
    pass


def _node_id(index: int) -> str:
    return f"skill_{index:02d}"


def _format_dependencies(dependencies: tuple[ExternalDependency, ...]) -> str:
    if not dependencies:
        return "—"
    values = (dependency.name.replace("|", "&#124;") for dependency in dependencies)
    return "<br>".join(values)


def _markdown(model: RepositoryModel) -> str:
    names = sorted(set(model.canonical_skills) & set(model.skill_by_name))
    node_ids = {name: _node_id(index) for index, name in enumerate(names, 1)}
    lines = [
        "# Skill Dependency Graph",
        "",
        "This file is generated from `.rules/skill-categories.yaml` and `README.md`.",
        "Only canonical `depends_on` relations are graph edges.",
        "",
        "## Canonical dependencies",
        "",
        "```mermaid",
        "graph LR",
    ]
    for name in names:
        label = name.replace('"', "&quot;")
        lines.append(f'    {node_ids[name]}["{label}"]')
    for source in names:
        entry = model.canonical_skills[source]
        raw_targets = entry.get("depends_on", [])
        targets = sorted({target for target in raw_targets if isinstance(target, str) and target in node_ids}) if isinstance(raw_targets, list) else []
        conditions = entry.get("depends_on_edge_condition", {})
        conditions = conditions if isinstance(conditions, dict) else {}
        for target in targets:
            if conditions.get(target, "unconditional") == "conditional":
                lines.append(f"    {node_ids[source]} -. conditional .-> {node_ids[target]}")
            else:
                lines.append(f"    {node_ids[source]} --> {node_ids[target]}")
    lines.extend([
        "```",
        "",
        "## External dependencies",
        "",
        "",
        "| Skill | Direct | Transitive | Effective |",
        "| --- | --- | --- | --- |",
    ])
    views = external_dependency_views(model)
    for name in names:
        view = views[name]
        lines.append(
            f"| {name} | {_format_dependencies(view.direct)} | "
            f"{_format_dependencies(view.transitive)} | {_format_dependencies(view.effective)} |"
        )
    return "\n".join(lines) + "\n"


def render_graph(model: RepositoryModel, output_path: Path) -> None:
    output_path = output_path if output_path.is_absolute() else model.root / output_path
    if model.diagnostics.has_errors:
        return
    temporary: Path | None = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = _markdown(model)
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False)
        temporary = Path(handle.name)
        with handle:
            handle.write(content)
        os.replace(temporary, output_path)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise GraphOutputError(f"cannot write graph to {output_path}: {detail}") from None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def register(register_check, register_graph_renderer) -> None:
    del register_check
    register_graph_renderer(render_graph)
