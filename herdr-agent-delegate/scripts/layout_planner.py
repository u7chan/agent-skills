#!/usr/bin/env python3
"""Plan delegated Herdr panes with a small, deterministic rule set."""

from __future__ import annotations

from typing import Any


MAX_PANES_PER_TAB = 4
SPLIT_DIRECTIONS = ("right", "down", "right", "down")


def incremental_slot(child_number: int) -> dict[str, Any]:
    """Return the tab, slot, and split direction for a one-based child number."""
    if child_number < 1:
        raise ValueError("child_number must be at least 1")
    zero_based = child_number - 1
    slot = zero_based % MAX_PANES_PER_TAB
    return {
        "tab_index": zero_based // MAX_PANES_PER_TAB,
        "slot": slot + 1,
        "direction": SPLIT_DIRECTIONS[slot],
        "starts_new_tab": zero_based >= MAX_PANES_PER_TAB and slot == 0,
    }


def plan_tabs(child_count: int) -> list[dict[str, Any]]:
    """Group a known batch into tabs of at most four delegated panes."""
    if child_count < 0:
        raise ValueError("child_count must not be negative")
    tabs: list[dict[str, Any]] = []
    for first in range(1, child_count + 1, MAX_PANES_PER_TAB):
        count = min(MAX_PANES_PER_TAB, child_count - first + 1)
        tabs.append(
            {
                "tab_index": len(tabs),
                "first_child": first,
                "child_count": count,
                "directions": list(SPLIT_DIRECTIONS[:count]),
            }
        )
    return tabs


def tab_size_from_layout(layout: dict[str, Any]) -> tuple[int, int]:
    """Return the enclosing width and height from a Herdr layout payload."""
    layout_data = layout.get("result", {}).get("layout", {})
    area = layout_data.get("area", {})
    if int(area.get("width", 0)) > 0 and int(area.get("height", 0)) > 0:
        return int(area["width"]), int(area["height"])
    panes = layout_data.get("panes", [])
    if not panes:
        return 0, 0
    left = min(int(pane.get("rect", {}).get("x", 0)) for pane in panes)
    top = min(int(pane.get("rect", {}).get("y", 0)) for pane in panes)
    right = max(
        int(pane.get("rect", {}).get("x", 0))
        + int(pane.get("rect", {}).get("width", 0))
        for pane in panes
    )
    bottom = max(
        int(pane.get("rect", {}).get("y", 0))
        + int(pane.get("rect", {}).get("height", 0))
        for pane in panes
    )
    return right - left, bottom - top


def detect_existing_panes(
    layout: dict[str, Any],
    parent_id: str | None = None,
    children: list[str] | None = None,
) -> dict[str, Any]:
    """Report panes unrelated to the parent and children created by this run."""
    related = {pane_id for pane_id in [parent_id, *(children or [])] if pane_id}
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    unrelated = [
        pane.get("pane_id")
        for pane in panes
        if pane.get("pane_id") and pane.get("pane_id") not in related
    ]
    return {"has_unrelated": bool(unrelated), "unrelated_count": len(unrelated)}


def should_use_dedicated_tabs(
    child_count: int, existing_pane_info: dict[str, Any]
) -> bool:
    """Use new tabs for known batches over four or tabs with unrelated panes."""
    if child_count < 0:
        raise ValueError("child_count must not be negative")
    return child_count > MAX_PANES_PER_TAB or bool(
        existing_pane_info.get("has_unrelated")
    )
