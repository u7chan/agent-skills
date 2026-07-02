#!/usr/bin/env python3
"""Choose the next herdr pane split so delegated agents form a grid."""

from __future__ import annotations

import argparse
import json
import sys


def choose(layout: dict, parent: str, children: list[str], cell_aspect: float) -> dict:
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
    physical_width = float(rect["width"]) * cell_aspect
    direction = "right" if physical_width >= float(rect["height"]) else "down"
    return {"target_pane_id": target, "direction": direction, "ratio": 0.5}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-file", help="herdr pane layout JSON; default: stdin")
    parser.add_argument("--parent", required=True)
    parser.add_argument("--child", action="append", default=[])
    parser.add_argument("--cell-aspect", type=float, default=0.5)
    args = parser.parse_args()
    if args.cell_aspect <= 0:
        parser.error("--cell-aspect must be greater than zero")

    try:
        if args.layout_file:
            with open(args.layout_file, encoding="utf-8") as stream:
                layout = json.load(stream)
        else:
            layout = json.load(sys.stdin)
        print(json.dumps(choose(layout, args.parent, args.child, args.cell_aspect)))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
