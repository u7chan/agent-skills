#!/usr/bin/env python3
"""Wait for a delegated agent through herdr semantic state or an output marker."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path


def run_herdr(arguments: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["herdr", *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def agent_status(target: str) -> str:
    result = run_herdr(["agent", "get", target], timeout=10)
    if result.returncode != 0:
        return "unavailable"
    try:
        payload = json.loads(result.stdout)
        return str(payload["result"]["agent"]["agent_status"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return "unavailable"


def valid_reply(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (
        path.is_absolute()
        and stat.S_ISREG(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and info.st_uid == os.getuid()
        and info.st_size > 0
    )


def emit(status: str, target: str, started: float, agent_state: str | None = None) -> None:
    result: dict[str, object] = {
        "status": status,
        "target": target,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    if agent_state is not None:
        result["agent_status"] = agent_state
    print(json.dumps(result))


def wait_semantic(args: argparse.Namespace) -> int:
    started = time.monotonic()
    deadline = started + args.timeout / 1000
    seen_working = False
    reply = Path(args.reply_path)

    while time.monotonic() < deadline:
        state = agent_status(args.target)
        seen_working = seen_working or state == "working"
        if state == "blocked":
            emit("blocked", args.target, started, state)
            return 2
        if valid_reply(reply) and (seen_working or state in {"idle", "done"}):
            emit("completed", args.target, started, state)
            return 0
        if state == "done":
            emit("reply_missing", args.target, started, state)
            return 4
        remaining_ms = max(1, int((deadline - time.monotonic()) * 1000))
        poll_ms = min(args.poll_interval, remaining_ms)
        awaited_state = "idle" if seen_working else "working"
        run_herdr(
            ["wait", "agent-status", args.target, "--status", awaited_state, "--timeout", str(poll_ms)],
            timeout=poll_ms / 1000 + 5,
        )

    emit("timeout", args.target, started, agent_status(args.target))
    return 3


def wait_marker(args: argparse.Namespace) -> int:
    started = time.monotonic()
    result = run_herdr([
        "wait", "output", args.target,
        "--match", args.marker,
        "--source", "recent-unwrapped",
        "--timeout", str(args.timeout),
    ], timeout=args.timeout / 1000 + 5)
    if result.returncode != 0:
        emit("timeout", args.target, started)
        return 3
    if not valid_reply(Path(args.reply_path)):
        emit("reply_missing", args.target, started)
        return 4
    emit("completed", args.target, started)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--reply-path", required=True)
    parser.add_argument("--timeout", type=int, default=3_600_000)
    parser.add_argument("--poll-interval", type=int, default=1_000)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("semantic")
    marker = subparsers.add_parser("marker")
    marker.add_argument("--marker", required=True)
    args = parser.parse_args()
    if args.timeout <= 0 or args.poll_interval <= 0:
        parser.error("timeouts must be greater than zero")
    exit_code = wait_semantic(args) if args.mode == "semantic" else wait_marker(args)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
