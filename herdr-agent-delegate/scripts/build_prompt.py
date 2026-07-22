#!/usr/bin/env python3
"""Pure prompt builder: validate delegation metadata and assemble the final prompt.

Does NOT interact with Herdr.  Outputs the built prompt to stdout or reports
validation errors to stderr and exits non-zero.

Prompt source priority: --prompt-file > --prompt > stdin.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Final

METADATA_KEYS: Final = ("agent", "model", "effort")
INVALID_METADATA_VALUES: Final = {"—"}
METADATA_INSTRUCTION: Final = (
    "このメタ情報は現在の委譲タスクにのみ使用し、"
    "再解決・変更・別Agentへの転用をしないこと。"
)


def validate_metadata(value: str) -> dict[str, str]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict) or set(parsed) != set(METADATA_KEYS):
        raise ValueError(
            "--metadata-json must contain exactly agent, model, and effort"
        )
    for key in METADATA_KEYS:
        val = parsed[key]
        if not isinstance(val, str) or not val.strip() or val.strip() in INVALID_METADATA_VALUES:
            raise ValueError(
                "--metadata-json values must be non-empty, non-placeholder strings"
            )
    return {key: parsed[key] for key in METADATA_KEYS}


def build_prompt(prompt: str, metadata: dict[str, str] | None) -> str:
    if metadata is None:
        return prompt
    payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    return (
        f"{prompt.rstrip()}\n\n"
        "<herdr-delegation-metadata>\n"
        f"{payload}\n"
        "</herdr-delegation-metadata>\n\n"
        f"{METADATA_INSTRUCTION}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", type=Path, help="read prompt from file")
    parser.add_argument("--prompt", help="inline prompt (avoid for multi-line/unicode)")
    parser.add_argument(
        "--metadata-json",
        dest="metadata_raw",
        help="optional all-or-nothing delegation metadata JSON",
    )
    args = parser.parse_args()

    if args.prompt_file:
        try:
            prompt_text = args.prompt_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot read --prompt-file: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.prompt:
        prompt_text = args.prompt
    elif not sys.stdin.isatty():
        prompt_text = sys.stdin.read()
    else:
        parser.error("--prompt-file, --prompt, or stdin required")

    if not prompt_text:
        parser.error("prompt must not be empty")

    metadata = None
    if args.metadata_raw is not None:
        try:
            metadata = validate_metadata(args.metadata_raw)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"ERROR: invalid metadata: {exc}", file=sys.stderr)
            sys.exit(1)

    print(build_prompt(prompt_text, metadata))


if __name__ == "__main__":
    main()
