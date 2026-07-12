#!/usr/bin/env python3
"""Split one delegated Herdr pane without touching unrelated panes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


MAX_PANES_PER_TAB = 4
MIN_PANE_WIDTH = 40
MIN_PANE_HEIGHT = 10
SPLIT_DIRECTIONS = ("right", "down", "right", "down")


def run_herdr(
    arguments: list[str], timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    """Run Herdr; kept as the test injection point."""
    return subprocess.run(
        ["herdr", *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def parse_pane(
    payload: dict[str, Any], label: str, result_key: str = "pane"
) -> dict[str, str]:
    try:
        pane = payload["result"][result_key]
        values = {key: pane[key] for key in ("pane_id", "workspace_id", "tab_id")}
        if any(not isinstance(value, str) or not value for value in values.values()):
            raise ValueError("pane_id, workspace_id, and tab_id must be non-empty strings")
        return values
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{label}: invalid pane payload: {error}") from error


def command_pane(
    arguments: list[str],
    label: str,
    timeout: float = 10,
    result_key: str = "pane",
) -> dict[str, str]:
    result = run_herdr(arguments, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(arguments)} failed: {result.stderr.strip()}")
    try:
        return parse_pane(json.loads(result.stdout), label, result_key=result_key)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label}: invalid JSON: {error}") from error


def get_pane(pane_id: str, label: str) -> dict[str, str]:
    pane = command_pane(["pane", "get", pane_id], label)
    if pane["pane_id"] != pane_id:
        raise ValueError(
            f"{label}: expected pane_id {pane_id}, got {pane['pane_id']}"
        )
    return pane


def validate_scope(
    pane: dict[str, str], workspace_id: str, tab_id: str, label: str
) -> None:
    if pane["workspace_id"] != workspace_id:
        raise ValueError(
            f"{label}: workspace_id mismatch: expected {workspace_id}, "
            f"got {pane['workspace_id']}"
        )
    if pane["tab_id"] != tab_id:
        raise ValueError(
            f"{label}: tab_id mismatch: expected {tab_id}, got {pane['tab_id']}"
        )


def get_layout(parent_pane_id: str) -> dict[str, Any]:
    result = run_herdr(["pane", "layout", "--pane", parent_pane_id], timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"pane layout failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"pane layout returned invalid JSON: {error}") from error


def pane_rect(layout: dict[str, Any], pane_id: str) -> dict[str, int]:
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    pane = next((item for item in panes if item.get("pane_id") == pane_id), None)
    if pane is None:
        raise ValueError(f"split target is not in the current layout: {pane_id}")
    rect = pane.get("rect", {})
    width = int(rect.get("width", 0))
    height = int(rect.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("split target width and height must be positive")
    return {"width": width, "height": height}


def has_unrelated_panes(
    layout: dict[str, Any], parent_pane_id: str, children: list[str]
) -> bool:
    related = {parent_pane_id, *children}
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    return any(
        pane.get("pane_id") and pane.get("pane_id") not in related for pane in panes
    )


def fits_minimum(rect: dict[str, int], direction: str) -> bool:
    if direction == "right":
        return rect["width"] // 2 >= MIN_PANE_WIDTH and rect["height"] >= MIN_PANE_HEIGHT
    return rect["width"] >= MIN_PANE_WIDTH and rect["height"] // 2 >= MIN_PANE_HEIGHT


def split_pane(target_id: str, direction: str, cwd: str) -> dict[str, str]:
    return command_pane(
        [
            "pane",
            "split",
            target_id,
            "--direction",
            direction,
            "--ratio",
            "0.5",
            "--cwd",
            cwd,
            "--no-focus",
        ],
        "split response",
        timeout=15,
    )


def create_in_new_tab(cwd: str, workspace_id: str, old_tab_id: str) -> dict[str, Any]:
    root = command_pane(
        ["tab", "create", "--workspace", workspace_id, "--cwd", cwd, "--no-focus"],
        "new tab pane",
        result_key="root_pane",
    )
    root = get_pane(root["pane_id"], "new tab pane after create")
    if root["workspace_id"] != workspace_id:
        raise ValueError("new tab was created outside the expected workspace")
    if root["tab_id"] == old_tab_id:
        raise ValueError("tab create returned the existing tab")
    return {
        **root,
        "group_parent_pane_id": root["pane_id"],
        "anchor_pane_id": root["pane_id"],
        "new_tab": True,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    current = command_pane(["pane", "current", "--current"], "current pane")
    parent = (
        current
        if current["pane_id"] == args.parent_pane_id
        else get_pane(args.parent_pane_id, "group parent")
    )
    if parent["workspace_id"] != current["workspace_id"]:
        raise ValueError("group parent is outside the orchestrator workspace")

    layout = get_layout(args.parent_pane_id)
    children = list(args.child)
    if args.new_tab or len(children) >= MAX_PANES_PER_TAB or has_unrelated_panes(
        layout, args.parent_pane_id, children
    ):
        return create_in_new_tab(
            args.cwd, parent["workspace_id"], parent["tab_id"]
        )

    target_id = args.parent_pane_id if not children else children[-1]
    target = get_pane(target_id, "split target")
    validate_scope(
        target, parent["workspace_id"], parent["tab_id"], "split target"
    )
    direction = SPLIT_DIRECTIONS[len(children)]
    if not fits_minimum(pane_rect(layout, target_id), direction):
        return create_in_new_tab(
            args.cwd, parent["workspace_id"], parent["tab_id"]
        )

    existing_ids = {
        pane.get("pane_id")
        for pane in layout.get("result", {}).get("layout", {}).get("panes", [])
        if pane.get("pane_id")
    }
    child = split_pane(target_id, direction, args.cwd)
    if child["pane_id"] in existing_ids:
        raise ValueError("pane split returned an existing pane_id")

    try:
        verified = get_pane(child["pane_id"], "new pane after split")
        validate_scope(
            verified,
            parent["workspace_id"],
            parent["tab_id"],
            "new pane after split",
        )
    except (RuntimeError, ValueError):
        # Only the pane returned by this split is eligible for cleanup. Parent,
        # earlier children, and unrelated panes are never closed here.
        if child["pane_id"] not in existing_ids:
            run_herdr(["pane", "close", child["pane_id"]], timeout=10)
        raise
    return {**verified, "new_tab": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-pane-id", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--child", action="append", default=[])
    parser.add_argument(
        "--new-tab",
        action="store_true",
        help="start this group in a new tab (for pre-planned batches)",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False))
    except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
