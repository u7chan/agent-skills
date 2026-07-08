#!/usr/bin/env python3
"""Plan a constrained grid layout for delegated herdr panes."""

from __future__ import annotations

import math
import os
from typing import Any


DEFAULT_MIN_WIDTH = int(os.environ.get("HERDR_DELEGATE_MIN_PANE_WIDTH", "80"))
DEFAULT_MIN_HEIGHT = int(os.environ.get("HERDR_DELEGATE_MIN_PANE_HEIGHT", "24"))
DEFAULT_MAX_COLUMNS_ENV = os.environ.get("HERDR_DELEGATE_GRID_COLUMNS", "0")
DEFAULT_MAX_COLUMNS = int(DEFAULT_MAX_COLUMNS_ENV) if DEFAULT_MAX_COLUMNS_ENV else 3
DEFAULT_MAX_PANES_PER_TAB = int(os.environ.get("HERDR_DELEGATE_MAX_PANES_PER_TAB", "6"))


def compute_columns(
    child_count: int,
    tab_width: int,
    tab_height: int,
    cell_aspect: float,
    max_columns: int,
    min_width: int,
    min_height: int,
) -> int:
    """Choose the number of columns for a grid of ``child_count`` panes."""
    if child_count <= 0:
        return 0
    max_columns = max(1, max_columns)
    tab_width = max(1, tab_width)
    tab_height = max(1, tab_height)
    # Estimate columns that produce cells close to the desired aspect ratio.
    # cols / rows ~= (W/H) / aspect  and  cols * rows >= child_count
    # => cols ~= sqrt(child_count * (H/W) / aspect)
    ratio = tab_height / tab_width
    estimated = max(1, round(math.sqrt(child_count * ratio / cell_aspect)))
    columns = min(max_columns, estimated)
    # Do not let cells fall below the minimum size.
    while columns > 1 and (tab_width // columns) < min_width:
        columns -= 1
    return columns


def compute_rows(child_count: int, columns: int) -> int:
    """Return the number of rows required for ``child_count`` cells."""
    if child_count <= 0 or columns <= 0:
        return 0
    return math.ceil(child_count / columns)


def target_slot(index: int, columns: int) -> dict[str, int]:
    """Return the (row, col) slot for the zero-based child ``index``."""
    if columns <= 0:
        return {"row": 0, "col": index}
    return {"row": index // columns, "col": index % columns}


def fit_capacity(
    tab_width: int,
    tab_height: int,
    cell_aspect: float,
    max_columns: int,
    min_width: int,
    min_height: int,
) -> int:
    """Return the maximum number of children that fit without breaking min size."""
    tab_width = max(1, tab_width)
    tab_height = max(1, tab_height)
    for count in range(1, DEFAULT_MAX_PANES_PER_TAB + 1):
        columns = compute_columns(count, tab_width, tab_height, cell_aspect, max_columns, min_width, min_height)
        rows = compute_rows(count, columns)
        cell_w = tab_width // columns if columns else tab_width
        cell_h = tab_height // rows if rows else tab_height
        if cell_w < min_width or cell_h < min_height:
            return count - 1
    return DEFAULT_MAX_PANES_PER_TAB


def plan_grid(
    child_count: int,
    tab_width: int,
    tab_height: int,
    cell_aspect: float = 0.5,
    max_columns: int | None = None,
    min_width: int | None = None,
    min_height: int | None = None,
) -> dict[str, Any]:
    """Plan a grid for ``child_count`` children inside the given tab size."""
    max_columns = max_columns if max_columns is not None else DEFAULT_MAX_COLUMNS
    min_width = min_width if min_width is not None else DEFAULT_MIN_WIDTH
    min_height = min_height if min_height is not None else DEFAULT_MIN_HEIGHT

    columns = compute_columns(
        child_count, tab_width, tab_height, cell_aspect, max_columns, min_width, min_height
    )
    rows = compute_rows(child_count, columns)
    slots = [target_slot(i, columns) for i in range(child_count)]
    capacity = fit_capacity(
        tab_width, tab_height, cell_aspect, max_columns, min_width, min_height
    )

    return {
        "columns": columns,
        "rows": rows,
        "slots": slots,
        "capacity": capacity,
        "min_width": min_width,
        "min_height": min_height,
        "max_columns": max_columns,
        "cell_aspect": cell_aspect,
    }


def tab_size_from_layout(layout: dict[str, Any]) -> tuple[int, int]:
    """Estimate the tab size from a herdr pane layout payload."""
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    if not panes:
        return 0, 0
    max_width = max(int(p.get("rect", {}).get("width", 0)) for p in panes)
    max_height = max(int(p.get("rect", {}).get("height", 0)) for p in panes)
    return max_width, max_height
