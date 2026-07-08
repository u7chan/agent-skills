#!/usr/bin/env python3
"""Choose the next herdr pane split so delegated agents form a grid."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_layout_planner() -> Any:
    scripts_dir = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "layout_planner", scripts_dir / "layout_planner.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


layout_planner = _load_layout_planner()


def choose(
    layout: dict,
    parent: str,
    children: list[str],
    cell_aspect: float,
    max_columns: int | None = None,
    min_width: int | None = None,
    min_height: int | None = None,
    total_children: int | None = None,
) -> dict:
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    by_id = {pane.get("pane_id"): pane.get("rect", {}) for pane in panes}
    candidates = [pane_id for pane_id in [parent, *children] if pane_id in by_id]
    if parent not in by_id:
        raise ValueError(f"parent pane is not in the current layout: {parent}")
    if not candidates:
        raise ValueError("no candidate panes are in the current layout")

    child_rank = {pane_id: index + 1 for index, pane_id in enumerate(children)}

    def score(pane_id: str) -> tuple[int, int]:
        rect = by_id[pane_id]
        area = int(rect.get("width", 0)) * int(rect.get("height", 0))
        return area, child_rank.get(pane_id, 0)

    target = max(candidates, key=score)
    rect = by_id[target]
    tab_width, tab_height = layout_planner.tab_size_from_layout(layout)

    child_count = total_children if total_children is not None else len(children) + 1
    plan = layout_planner.plan_grid(
        child_count,
        tab_width,
        tab_height,
        cell_aspect=cell_aspect,
        max_columns=max_columns,
        min_width=min_width,
        min_height=min_height,
    )
    if child_count > plan["capacity"]:
        raise ValueError(
            f"splitting child {child_count} would exceed grid capacity {plan['capacity']} "
            f"(min {plan['min_width']}x{plan['min_height']})"
        )

    columns = plan["columns"] or 1
    rows = plan["rows"] or 1
    target_w = tab_width / columns if columns else tab_width
    target_h = tab_height / rows if rows else tab_height

    width = float(rect.get("width", 0))
    height = float(rect.get("height", 0))
    # Split along the axis that most exceeds the target cell size.
    if target_w > 0 and target_h > 0:
        direction = "right" if (width / target_w) >= (height / target_h) else "down"
    else:
        physical_width = width * cell_aspect
        direction = "right" if physical_width >= height else "down"

    return {
        "target_pane_id": target,
        "direction": direction,
        "ratio": 0.5,
        "plan": plan,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-file", help="herdr pane layout JSON; default: stdin")
    parser.add_argument("--parent", required=True)
    parser.add_argument("--child", action="append", default=[])
    parser.add_argument("--cell-aspect", type=float, default=0.5)
    parser.add_argument("--max-columns", type=int, default=None)
    parser.add_argument("--min-width", type=int, default=None)
    parser.add_argument("--min-height", type=int, default=None)
    parser.add_argument("--total-children", type=int, default=None, help="planned total number of children (default: len(children) + 1)")
    args = parser.parse_args()
    if args.cell_aspect <= 0:
        parser.error("--cell-aspect must be greater than zero")

    try:
        if args.layout_file:
            with open(args.layout_file, encoding="utf-8") as stream:
                layout = json.load(stream)
        else:
            layout = json.load(sys.stdin)
        print(
            json.dumps(
                choose(
                    layout,
                    args.parent,
                    args.child,
                    args.cell_aspect,
                    max_columns=args.max_columns,
                    min_width=args.min_width,
                    min_height=args.min_height,
                    total_children=args.total_children,
                ),
                ensure_ascii=False,
            )
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
