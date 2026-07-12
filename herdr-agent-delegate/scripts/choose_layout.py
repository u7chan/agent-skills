#!/usr/bin/env python3
"""Choose a Herdr split direction from the target pane geometry."""

from __future__ import annotations

import argparse
import json
import sys


def choose(layout: dict, target_pane_id: str) -> dict[str, object]:
    """Split right when the target is wider than tall, otherwise split down."""
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    pane = next((item for item in panes if item.get("pane_id") == target_pane_id), None)
    if pane is None:
        raise ValueError(f"target pane is not in the current layout: {target_pane_id}")
    rect = pane.get("rect", {})
    width = int(rect.get("width", 0))
    height = int(rect.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("target pane width and height must be positive")
    return {
        "target_pane_id": target_pane_id,
        "direction": "right" if width > height else "down",
        "ratio": 0.5,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-file", help="herdr pane layout JSON; default: stdin")
    parser.add_argument("--target-pane-id", required=True)
    args = parser.parse_args()
    try:
        if args.layout_file:
            with open(args.layout_file, encoding="utf-8") as stream:
                layout = json.load(stream)
        else:
            layout = json.load(sys.stdin)
        print(json.dumps(choose(layout, args.target_pane_id), ensure_ascii=False))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
