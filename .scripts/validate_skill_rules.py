#!/usr/bin/env python3
"""CLI entry point for repository skill validation.

Extension modules register additional checks and a graph renderer via
``register_check`` and ``register_graph_renderer``; this file remains the sole CLI.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from skill_validation import Diagnostics, RepositoryModel, core_checks

GRAPH_RENDERER = None


def register_check(check) -> None:
    """A2 may call this before ``main`` to add a check(model) callable."""
    EXTRA_CHECKS.append(check)


def register_graph_renderer(renderer) -> None:
    """A2 graph module registers ``renderer(model, output_path)`` here."""
    global GRAPH_RENDERER
    GRAPH_RENDERER = renderer


EXTRA_CHECKS = []


def load_optional_extensions() -> None:
    """Load extension modules when they are present.

    An extension module named ``skill_validation.dependencies`` or
    ``skill_validation.graph`` exposes ``register(register_check,
    register_graph_renderer)``.  This keeps additions out of the public Bash
    entry point.
    """
    for module_name in ("skill_validation.dependencies", "skill_validation.inventory_check", "skill_validation.graph"):
        if importlib.util.find_spec(module_name) is None:
            continue
        extension = importlib.import_module(module_name)
        register = getattr(extension, "register", None)
        if not callable(register):
            raise RuntimeError(f"{module_name} must expose register(register_check, register_graph_renderer)")
        register(register_check, register_graph_renderer)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate agent-skill repository rules.")
    parser.add_argument("--graph", metavar="PATH", help="write the dependency graph")
    args = parser.parse_args(argv)
    load_optional_extensions()
    if args.graph and GRAPH_RENDERER is None:
        parser.error("--graph is not available until the dependency graph validator is installed")

    root = SCRIPT_DIR.parent
    diagnostics = Diagnostics(root)
    model = RepositoryModel.load(root, diagnostics)
    for check in [*core_checks(), *EXTRA_CHECKS]:
        check(model)
    graph_error = None
    if args.graph:
        try:
            GRAPH_RENDERER(model, Path(args.graph))
        except (OSError, RuntimeError) as exc:
            graph_error = str(exc)
    for diagnostic in diagnostics.sorted():
        print(diagnostic.format(), file=sys.stderr)
    if graph_error is not None:
        print(f"CLI ERROR [graph-output] {args.graph}: {graph_error}", file=sys.stderr)
        return 2
    return 1 if diagnostics.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
