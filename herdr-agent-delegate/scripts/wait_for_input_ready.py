#!/usr/bin/env python3
"""Wait until a newly started Agent TUI can accept input."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


READY_RULES = {
    "codex": ("›", r"(?m)^\s*›(?:\s|$)"),
    "claude": ("❯", r"(?m)^\s*❯(?:\s|$)"),
    "opencode": ("ctrl+p commands", r"(?i)ctrl\+p\s+commands"),
}


def run_herdr(arguments: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["herdr", *arguments], check=False, capture_output=True, text=True, timeout=timeout
    )


def write_diagnostics(task_dir: Path, payload: dict[str, object]) -> None:
    (task_dir / "input_readiness.diagnostics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def wait_for_input_ready(args: argparse.Namespace) -> int:
    started = time.monotonic()
    marker, pattern = READY_RULES[args.agent]
    waited = run_herdr(
        ["wait", "output", args.target, "--match", marker, "--source", "recent-unwrapped",
         "--timeout", str(args.timeout)],
        timeout=args.timeout / 1000 + 5,
    )
    read = run_herdr(
        ["pane", "read", args.target, "--source", "recent-unwrapped", "--lines", str(args.lines)],
        timeout=10,
    )
    elapsed = round(time.monotonic() - started, 3)
    if waited.returncode == 0 and read.returncode == 0 and re.search(pattern, read.stdout):
        print(json.dumps({"status": "input_ready", "target": args.target, "agent": args.agent,
                          "elapsed_seconds": elapsed}))
        return 0

    diagnostics = {
        "status": "input_not_ready", "target": args.target, "agent": args.agent,
        "elapsed_seconds": elapsed, "wait_returncode": waited.returncode,
        "wait_stderr": waited.stderr, "read_returncode": read.returncode,
        "read_output": read.stdout, "read_stderr": read.stderr,
    }
    write_diagnostics(Path(args.task_dir), diagnostics)
    print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
    return 2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--agent", required=True, choices=sorted(READY_RULES))
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--timeout", type=int, default=30_000)
    parser.add_argument("--lines", type=int, default=80)
    args = parser.parse_args()
    if args.timeout <= 0 or args.lines <= 0:
        parser.error("timeout and lines must be greater than zero")
    raise SystemExit(wait_for_input_ready(args))


if __name__ == "__main__":
    main()
