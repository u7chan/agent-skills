#!/usr/bin/env python3
"""Send a request to a CLI Agent pane and wait for it to start working.

This wrapper exists because Claude Code does not always auto-execute a long
pasted prompt: the input field shows ``[Pasted text #1]`` and stays idle.
For Claude only, when this happens we send a short activation prompt via the
same ``herdr pane run`` primitive to trigger execution. Other agents receive a
single ``herdr pane run`` and the usual working-status wait.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Final


SUPPORTED_AGENTS: Final = ("codex", "claude", "opencode")
DEFAULT_TIMEOUT_MS: Final = 30_000
DEFAULT_ACTIVATION_TIMEOUT_MS: Final = 10_000
DEFAULT_ACTIVATION_TEXT: Final = "実行して"


def run_herdr(
    arguments: list[str], timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["herdr", *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def wait_for_working(target: str, timeout_ms: int) -> bool:
    """Wait up to ``timeout_ms`` for the pane to become ``working``.

    Returns ``True`` if the status was reached, ``False`` on timeout or error.
    """
    if timeout_ms <= 0:
        return False
    result = run_herdr(
        [
            "wait",
            "agent-status",
            target,
            "--status",
            "working",
            "--timeout",
            str(timeout_ms),
        ],
        timeout=timeout_ms / 1000 + 5,
    )
    return result.returncode == 0


def read_recent_output(target: str, lines: int = 80) -> subprocess.CompletedProcess[str]:
    return run_herdr(
        [
            "pane",
            "read",
            target,
            "--source",
            "recent-unwrapped",
            "--lines",
            str(lines),
        ],
        timeout=10,
    )


def diagnose(target: str) -> dict[str, object]:
    pane_get = run_herdr(["pane", "get", target], timeout=10)
    pane_read = read_recent_output(target, lines=80)
    return {
        "pane_get": {
            "returncode": pane_get.returncode,
            "stdout": pane_get.stdout,
            "stderr": pane_get.stderr,
        },
        "pane_read": {
            "returncode": pane_read.returncode,
            "stdout": pane_read.stdout,
            "stderr": pane_read.stderr,
        },
    }


def send_request(args: argparse.Namespace) -> int:
    started = time.monotonic()
    total_timeout_ms = args.timeout
    activation_timeout_ms = min(args.activation_timeout, total_timeout_ms)

    delivery = run_herdr(
        ["pane", "run", args.target, args.prompt],
        timeout=10,
    )
    if delivery.returncode != 0:
        diagnostics = {
            "status": "request_delivery_failed",
            "phase": "delivery",
            "target": args.target,
            "agent": args.agent,
            "delivery": {
                "returncode": delivery.returncode,
                "stdout": delivery.stdout,
                "stderr": delivery.stderr,
            },
        }
        diagnostics.update(diagnose(args.target))
        print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
        return 1

    # First wait: give the agent a chance to start normally.
    first_wait_ms = max(0, min(activation_timeout_ms, total_timeout_ms))
    if wait_for_working(args.target, first_wait_ms):
        return 0

    # Claude-specific fallback for the "[Pasted text #1]" idle state.
    if args.agent == "claude":
        read = read_recent_output(args.target, lines=80)
        output = read.stdout if read.returncode == 0 else ""
        if "[Pasted text" in output:
            activation = run_herdr(
                ["pane", "run", args.target, args.activation_text],
                timeout=10,
            )
            if activation.returncode != 0:
                diagnostics = {
                    "status": "request_delivery_failed",
                    "phase": "activation",
                    "target": args.target,
                    "agent": args.agent,
                    "activation": {
                        "returncode": activation.returncode,
                        "stdout": activation.stdout,
                        "stderr": activation.stderr,
                    },
                }
                diagnostics.update(diagnose(args.target))
                print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
                return 1

            elapsed_ms = int((time.monotonic() - started) * 1000)
            remaining_ms = max(0, total_timeout_ms - elapsed_ms)
            if wait_for_working(args.target, remaining_ms):
                return 0

    diagnostics = {
        "status": "request_delivery_failed",
        "phase": "working_wait",
        "target": args.target,
        "agent": args.agent,
    }
    diagnostics.update(diagnose(args.target))
    print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="target pane id")
    parser.add_argument(
        "--agent",
        required=True,
        choices=SUPPORTED_AGENTS,
        help="agent type running in the target pane",
    )
    parser.add_argument("--prompt", required=True, help="request body to send")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        help="total timeout in milliseconds to wait for working (default: %(default)s)",
    )
    parser.add_argument(
        "--activation-timeout",
        type=int,
        default=DEFAULT_ACTIVATION_TIMEOUT_MS,
        help="timeout in milliseconds before trying the Claude activation fallback "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--activation-text",
        default=DEFAULT_ACTIVATION_TEXT,
        help="short prompt used to activate a stuck Claude paste (default: %(default)s)",
    )
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if args.activation_timeout <= 0:
        parser.error("--activation-timeout must be greater than zero")
    if args.activation_timeout > args.timeout:
        parser.error("--activation-timeout must not exceed --timeout")
    if not args.prompt:
        parser.error("--prompt must not be empty")

    raise SystemExit(send_request(args))


if __name__ == "__main__":
    main()
