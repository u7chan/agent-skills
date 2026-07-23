#!/usr/bin/env python3
"""Execute ``herdr agent start`` with individually built argv.

Composes kind, pane, and native agent-args into a safe argument list and
executes via ``subprocess.run``, propagating exit code, stdout, and stderr.

``--print-argv`` prints the JSON argv array and exits without executing.
Use it for inspection when the caller needs to verify or delegate execution.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def build_launch_argv(
    name: str,
    kind: str,
    pane_id: str,
    native_agent_args: list[str] | None = None,
) -> list[str]:
    argv = [
        "herdr", "agent", "start", name,
        "--kind", kind,
        "--pane", pane_id,
    ]
    if native_agent_args:
        argv.append("--")
        argv.extend(native_agent_args)
    return argv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="unique agent name")
    parser.add_argument("--kind", required=True, choices=("codex", "claude", "opencode"))
    parser.add_argument("--pane-id", required=True, help="target pane ID")
    parser.add_argument("--native-args-file", help="JSON file containing native_agent_args array")
    parser.add_argument("--print-argv", action="store_true",
                        help="print argv JSON and exit without executing")
    args = parser.parse_args()

    native_args: list[str] | None = None
    if args.native_args_file:
        with open(args.native_args_file, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list) or not all(isinstance(a, str) for a in data):
            print("ERROR: native-args-file must be a JSON array of strings", file=sys.stderr)
            sys.exit(1)
        native_args = data

    argv = build_launch_argv(args.name, args.kind, args.pane_id, native_args)

    if args.print_argv:
        json.dump(argv, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return

    result = subprocess.run(argv, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
