#!/usr/bin/env python3
"""Split a herdr pane and verify the new pane stays in the parent's fixed scope."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn


def _load_choose_layout() -> Any:
    scripts_dir = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("choose_layout", scripts_dir / "choose_layout.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


choose_layout = _load_choose_layout()


def run_herdr(arguments: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    """Run a herdr CLI command. This function is the injection point for tests."""
    return subprocess.run(
        ["herdr", *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def parse_pane(payload: dict[str, Any], label: str) -> dict[str, str]:
    """Extract pane_id, workspace_id, tab_id from a herdr pane response."""
    try:
        pane = payload["result"]["pane"]
        for key in ("pane_id", "workspace_id", "tab_id"):
            value = pane[key]
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label}: {key} is not a non-empty string")
        return {
            "pane_id": pane["pane_id"],
            "workspace_id": pane["workspace_id"],
            "tab_id": pane["tab_id"],
        }
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{label}: invalid pane payload: {error}") from error


def get_current_pane(expected_parent_id: str) -> dict[str, str]:
    result = run_herdr(["pane", "current", "--current"], timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"pane current failed: {result.stderr.strip()}")
    pane = parse_pane(json.loads(result.stdout), "current pane")
    if pane["pane_id"] != expected_parent_id:
        raise ValueError(
            f"current pane {pane['pane_id']} does not match expected parent {expected_parent_id}"
        )
    return pane


def get_layout_json(layout_file: Path | None, parent_pane_id: str) -> dict[str, Any]:
    if layout_file is not None:
        with layout_file.open(encoding="utf-8") as stream:
            return json.load(stream)
    result = run_herdr(["pane", "layout", "--pane", parent_pane_id], timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"pane layout failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def validate_layout_scope(layout: dict[str, Any], expected: dict[str, str], parent_id: str) -> None:
    panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    pane_ids = {p.get("pane_id") for p in panes}
    if parent_id not in pane_ids:
        raise ValueError("parent pane is not present in the current layout")

    scope_sources = [
        layout.get("result", {}).get("layout", {}),
        layout.get("result", {}),
    ]
    found_scope = False
    for source in scope_sources:
        if "workspace_id" in source or "tab_id" in source:
            found_scope = True
            for key in ("workspace_id", "tab_id"):
                value = source.get(key)
                if not isinstance(value, str) or value == "":
                    raise ValueError(f"layout {key} is missing, null, empty, or not a string")
                if value != expected[key]:
                    raise ValueError(f"layout {key} mismatch: expected {expected[key]}, got {value}")

    if not found_scope:
        pane_scopes = [
            (p.get("workspace_id"), p.get("tab_id"))
            for p in panes
            if "workspace_id" in p or "tab_id" in p
        ]
        if not pane_scopes:
            raise ValueError("layout response does not contain workspace_id or tab_id")
        for workspace_id, tab_id in pane_scopes:
            if workspace_id != expected["workspace_id"] or tab_id != expected["tab_id"]:
                raise ValueError("layout pane scope does not match expected scope")


def get_pane(pane_id: str, label: str) -> dict[str, str]:
    result = run_herdr(["pane", "get", pane_id], timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"pane get {pane_id} failed: {result.stderr.strip()}")
    pane = parse_pane(json.loads(result.stdout), label)
    if pane["pane_id"] != pane_id:
        raise ValueError(
            f"{label}: pane get returned unexpected pane_id: expected {pane_id}, got {pane['pane_id']}"
        )
    return pane


def validate_scope(pane: dict[str, str], expected: dict[str, str], label: str) -> None:
    for key in ("workspace_id", "tab_id"):
        value = pane.get(key)
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{label}: {key} is missing, null, empty, or not a string")
        if value != expected[key]:
            raise ValueError(f"{label}: {key} mismatch: expected {expected[key]}, got {value}")


def split_pane(target_id: str, direction: str, cwd: str) -> dict[str, str]:
    result = run_herdr(
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
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pane split failed: {result.stderr.strip()}")
    return parse_pane(json.loads(result.stdout), "split response")


def close_pane(pane_id: str) -> subprocess.CompletedProcess[str]:
    return run_herdr(["pane", "close", pane_id], timeout=10)


def can_close_safely(new_pane: dict[str, str] | None, forbidden_ids: set[str]) -> bool:
    if new_pane is None:
        return False
    new_pane_id = new_pane.get("pane_id")
    if not isinstance(new_pane_id, str) or new_pane_id == "":
        return False
    if new_pane_id in forbidden_ids:
        return False
    return True


def save_diagnostics(task_dir: Path, diagnostics: dict[str, Any]) -> Path:
    path = task_dir / "split_scoped_pane.diagnostics.json"
    path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def fail_with_diagnostics(
    message: str, diagnostics: dict[str, Any], task_dir: Path, exit_code: int = 1
) -> NoReturn:
    diagnostics["failure_reason"] = message
    save_diagnostics(task_dir, diagnostics)
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def run(args: argparse.Namespace) -> dict[str, str]:
    task_dir = Path(args.task_dir).resolve()
    if not task_dir.is_dir():
        raise SystemExit(f"ERROR: task directory does not exist: {task_dir}")

    diagnostics: dict[str, Any] = {
        "parent_pane_id": args.parent_pane_id,
        "cwd": args.cwd,
        "task_dir": str(task_dir),
        "close_attempted": False,
        "close_succeeded": None,
    }

    try:
        parent_before = get_current_pane(args.parent_pane_id)
        expected_scope = {
            "workspace_id": parent_before["workspace_id"],
            "tab_id": parent_before["tab_id"],
        }
        diagnostics["parent_before"] = parent_before
        diagnostics["expected_scope"] = expected_scope
        validate_scope(parent_before, expected_scope, "parent_before")
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        fail_with_diagnostics(str(error), diagnostics, task_dir)

    try:
        layout = get_layout_json(
            Path(args.layout_file) if args.layout_file is not None else None,
            args.parent_pane_id,
        )
        diagnostics["layout"] = layout
        validate_layout_scope(layout, expected_scope, args.parent_pane_id)
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as error:
        fail_with_diagnostics(str(error), diagnostics, task_dir)

    children = list(args.child)
    try:
        choice = choose_layout.choose(
            layout,
            args.parent_pane_id,
            children,
            args.cell_aspect,
            max_columns=args.max_columns,
            min_width=args.min_width,
            min_height=args.min_height,
            total_children=args.total_children,
        )
        diagnostics["choice"] = choice
        target_id = choice["target_pane_id"]
    except (ValueError, KeyError, TypeError) as error:
        fail_with_diagnostics(str(error), diagnostics, task_dir)

    try:
        target_before = get_pane(target_id, "split_target_before")
        diagnostics["target_before"] = target_before
        validate_scope(target_before, expected_scope, "split_target_before")
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        fail_with_diagnostics(str(error), diagnostics, task_dir)

    pre_split_panes = layout.get("result", {}).get("layout", {}).get("panes", [])
    forbidden_ids: set[str] = {p.get("pane_id") for p in pre_split_panes}
    forbidden_ids.add(args.parent_pane_id)
    forbidden_ids.update(children)

    new_pane: dict[str, str] | None = None
    try:
        new_pane = split_pane(target_id, choice["direction"], args.cwd)
        diagnostics["split_response"] = new_pane
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        fail_with_diagnostics(str(error), diagnostics, task_dir)

    if not new_pane["pane_id"]:
        diagnostics["close_attempted"] = False
        diagnostics["close_succeeded"] = None
        fail_with_diagnostics("split response pane_id is empty", diagnostics, task_dir)

    if new_pane["pane_id"] in forbidden_ids:
        diagnostics["close_attempted"] = False
        diagnostics["close_succeeded"] = None
        fail_with_diagnostics(
            f"split returned a pane ID already present before the split: {new_pane['pane_id']}",
            diagnostics,
            task_dir,
        )

    post_errors: list[str] = []
    try:
        parent_after = get_current_pane(args.parent_pane_id)
        validate_scope(parent_after, expected_scope, "parent_after")
        diagnostics["parent_after"] = parent_after
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        post_errors.append(str(error))

    try:
        new_pane_after = get_pane(new_pane["pane_id"], "new_pane_after")
        validate_scope(new_pane_after, expected_scope, "new_pane_after")
        diagnostics["new_pane_after"] = new_pane_after
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        post_errors.append(str(error))

    if post_errors:
        diagnostics["close_attempted"] = False
        diagnostics["close_succeeded"] = None
        if can_close_safely(new_pane, forbidden_ids):
            diagnostics["close_attempted"] = True
            try:
                close_result = close_pane(new_pane["pane_id"])
                diagnostics["close_exit_code"] = close_result.returncode
                diagnostics["close_stdout"] = close_result.stdout
                diagnostics["close_stderr"] = close_result.stderr
                diagnostics["close_succeeded"] = close_result.returncode == 0
            except subprocess.TimeoutExpired as error:
                diagnostics["close_exit_code"] = None
                diagnostics["close_succeeded"] = False
                diagnostics["close_timeout_seconds"] = error.timeout
        fail_with_diagnostics("; ".join(post_errors), diagnostics, task_dir)

    return {
        "pane_id": new_pane_after["pane_id"],
        "workspace_id": new_pane_after["workspace_id"],
        "tab_id": new_pane_after["tab_id"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-pane-id", required=True, help="HERDR_PANE_ID of the invoking pane")
    parser.add_argument("--task-dir", required=True, help="task directory for diagnostics")
    parser.add_argument("--cwd", required=True, help="working directory for the new pane")
    parser.add_argument("--layout-file", help="herdr pane layout JSON; default: fetch via herdr")
    parser.add_argument("--child", action="append", default=[], help="previously created child pane IDs")
    parser.add_argument("--cell-aspect", type=float, default=0.5)
    parser.add_argument("--max-columns", type=int, default=None, help="grid column limit (0 means auto)")
    parser.add_argument("--min-width", type=int, default=None, help="minimum pane width in cells")
    parser.add_argument("--min-height", type=int, default=None, help="minimum pane height in cells")
    parser.add_argument("--total-children", type=int, default=None, help="planned total number of children (default: len(--child) + 1)")
    args = parser.parse_args()
    if args.cell_aspect <= 0:
        parser.error("--cell-aspect must be greater than zero")
    if args.max_columns is not None and args.max_columns < 0:
        parser.error("--max-columns must be non-negative")
    if args.total_children is not None and args.total_children < 1:
        parser.error("--total-children must be at least 1")
    result = run(args)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
