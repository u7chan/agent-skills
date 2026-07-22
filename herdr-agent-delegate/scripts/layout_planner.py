#!/usr/bin/env python3
"""Deterministic pane layout planner for Herdr 0.7.5 delegation.

Accepts Herdr 0.7.5 ``herdr pane layout`` output on stdin (envelope
``{"result":{"layout":{"panes":[...]}}}``) or a plain ``[{"pane_id":...,"rect":...},...]``
JSON array file as positional argument.

MAX_PANES_PER_TAB = 4 (root included).  After ``use_new_tab=true``, the caller
MUST ``tab create``, extract ``result.root_pane.pane_id`` as the new root,
reset children, re-fetch layout, and re-run this planner.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

MAX_PANES_PER_TAB = 4
MIN_WIDTH = 40
MIN_HEIGHT = 10
SPLIT_DIRECTIONS = ("right", "down", "right")


def extract_panes(data: Any) -> list[dict[str, Any]]:
    """Accept Herdr 0.7.5 envelope ``result.layout.panes`` or a plain array."""
    if isinstance(data, list):
        panes = data
    elif isinstance(data, dict):
        try:
            panes = data["result"]["layout"]["panes"]
        except (KeyError, TypeError):
            raise ValueError("expected JSON array or Herdr layout envelope with result.layout.panes")
    else:
        raise ValueError("expected JSON array or Herdr layout envelope")

    if not isinstance(panes, list):
        raise ValueError("panes must be a JSON array")

    for item in panes:
        if not isinstance(item, dict) or "pane_id" not in item:
            raise ValueError("each pane must have a pane_id")
    return panes


def _rect(panes: list[dict[str, Any]], pane_id: str) -> dict[str, int]:
    for p in panes:
        if p.get("pane_id") == pane_id:
            r = p.get("rect", {})
            w = int(r.get("width", 0))
            h = int(r.get("height", 0))
            if w <= 0 or h <= 0:
                raise ValueError(f"pane {pane_id} has invalid rect: {r}")
            return {"width": w, "height": h}
    raise ValueError(f"pane {pane_id} not found in layout")


def _fits(rect: dict[str, int], direction: str) -> bool:
    if direction == "right":
        return rect["width"] // 2 >= MIN_WIDTH and rect["height"] >= MIN_HEIGHT
    return rect["width"] >= MIN_WIDTH and rect["height"] // 2 >= MIN_HEIGHT


def _has_unrelated(panes: list[dict[str, Any]], related: set[str]) -> bool:
    return any(p.get("pane_id") not in related for p in panes)


def plan(
    panes: list[dict[str, Any]],
    root_pane_id: str,
    child_ids: list[str],
    *,
    new_tab: bool = False,
) -> dict[str, Any]:
    related = {root_pane_id, *child_ids}

    for pid in related:
        _rect(panes, pid)

    child_count = len(child_ids)
    unrelated = _has_unrelated(panes, related)
    need_new_tab = new_tab or unrelated or (child_count + 1 >= MAX_PANES_PER_TAB)

    if need_new_tab:
        return {"use_new_tab": True, "child_index": 1, "direction": None, "split_target": None,
                "next_root_pane_id": None}

    if child_count == 0:
        target = root_pane_id
        di = 0
    else:
        target = child_ids[-1]
        di = child_count

    direction = SPLIT_DIRECTIONS[di]

    if not _fits(_rect(panes, target), direction):
        return {"use_new_tab": True, "child_index": 1, "direction": None, "split_target": None,
                "next_root_pane_id": None}

    return {"use_new_tab": False, "child_index": child_count + 1,
            "direction": direction, "split_target": target, "next_root_pane_id": None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panes_file", nargs="?", help="pane array JSON file; reads stdin if omitted")
    parser.add_argument("--root-pane-id", required=True)
    parser.add_argument("--child", action="append", default=[])
    parser.add_argument("--new-tab", action="store_true")
    args = parser.parse_args()

    try:
        if args.panes_file:
            with open(args.panes_file, encoding="utf-8") as fh:
                raw = json.load(fh)
        else:
            raw = json.load(sys.stdin)
        panes = extract_panes(raw)
        result = plan(panes, args.root_pane_id, args.child, new_tab=args.new_tab)
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
