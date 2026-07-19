#!/usr/bin/env python3
"""Freeze cagent dry-run values into a launch command and metadata snapshot."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Final


DISPLAY_AGENTS: Final = {
    "codex": "Codex",
    "claude": "Claude Code",
    "opencode": "OpenCode",
}
INVALID_METADATA_VALUES: Final = {"—"}


def option_value(arguments: list[str], *names: str) -> str | None:
    for index, argument in enumerate(arguments):
        for name in names:
            if argument == name and index + 1 < len(arguments):
                return arguments[index + 1]
            if argument.startswith(f"{name}="):
                return argument.split("=", 1)[1]
    return None


def parse_dry_run(output: str) -> tuple[str | None, str | None, str | None]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    effort = next(
        (
            line.split(":", 1)[1].strip()
            for line in lines
            if line.startswith("# Resolved effort:")
        ),
        None,
    )
    command_line = next(
        (line for line in reversed(lines) if not line.startswith("#")), ""
    )
    command = shlex.split(command_line) if command_line else []
    agent_cli = Path(command[0]).name if command else None
    model = option_value(command, "--model", "-m")
    return agent_cli, model, effort


def freeze_resolution(
    *,
    agent_id: str,
    base_agent_type: str,
    level: str | None,
    dry_run: str,
    verification_dry_run: str | None = None,
) -> dict[str, object]:
    agent_cli, model, effort = parse_dry_run(dry_run)
    command = ["cagent", "--agent", agent_id]
    if model:
        command.extend(["--model", model])
    if effort:
        command.extend(["--effort", effort])
    if level:
        command.append(level)

    verified = False
    if verification_dry_run is not None:
        verification = parse_dry_run(verification_dry_run)
        if verification != (agent_cli, model, effort):
            raise ValueError("fixed command dry-run does not match initial resolution")
        verified = True

    display_agent = DISPLAY_AGENTS.get(base_agent_type)
    metadata = None
    metadata_values = (display_agent, model, effort)
    if verified and all(
        value and value.strip() not in INVALID_METADATA_VALUES
        for value in metadata_values
    ):
        metadata = {
            "agent": display_agent,
            "model": model,
            "effort": effort,
        }

    return {
        "base_agent_type": base_agent_type,
        "agent_command": shlex.join(command),
        "verified": verified,
        "resolved": {
            "agent_id": agent_id,
            "agent": display_agent,
            "model": model,
            "effort": effort,
        },
        "delegation_metadata": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--base-agent-type", required=True)
    parser.add_argument("--level")
    parser.add_argument("--dry-run-file", type=Path, required=True)
    parser.add_argument("--verification-dry-run-file", type=Path)
    args = parser.parse_args()
    if not args.agent_id.strip() or not args.base_agent_type.strip():
        parser.error("agent and base agent type must not be empty")

    try:
        result = freeze_resolution(
            agent_id=args.agent_id,
            base_agent_type=args.base_agent_type,
            level=args.level,
            dry_run=args.dry_run_file.read_text(encoding="utf-8"),
            verification_dry_run=(
                args.verification_dry_run_file.read_text(encoding="utf-8")
                if args.verification_dry_run_file
                else None
            ),
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
