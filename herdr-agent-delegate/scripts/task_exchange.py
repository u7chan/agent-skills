#!/usr/bin/env python3
"""Create and collect Markdown task exchanges for herdr agent delegation."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import stat
import sys
import time
from pathlib import Path
from typing import NoReturn


def die(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _require_absolute(path: str, name: str) -> None:
    if not os.path.isabs(path):
        die(f"{name} must be an absolute path: {path}")


def storage_root() -> Path:
    configured = os.environ.get("HERDR_AGENT_DELEGATE_ROOT")
    if configured:
        _require_absolute(configured, "HERDR_AGENT_DELEGATE_ROOT")
        base = Path(configured)
    else:
        workspace = os.environ.get("HERDR_AGENT_DELEGATE_WORKSPACE")
        if workspace:
            _require_absolute(workspace, "HERDR_AGENT_DELEGATE_WORKSPACE")
            base = Path(workspace) / ".herdr-agent-delegate"
        else:
            base = Path.cwd() / ".herdr-agent-delegate"
    return base / str(os.getuid())


def ensure_directory(path: Path, *, create: bool = False) -> Path:
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        info = path.lstat()
    except FileNotFoundError:
        die(f"directory does not exist: {path}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        die(f"directory must not be a symlink: {path}")
    if info.st_uid != os.getuid():
        die(f"directory is not owned by the current user: {path}")
    path.chmod(0o700)
    return path.resolve(strict=True)


def safe_task_dir(raw_path: str) -> Path:
    root = ensure_directory(storage_root(), create=True)
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        die("task directory must be an absolute path")
    resolved = ensure_directory(candidate)
    if resolved.parent != root:
        die(f"task directory is outside the storage root: {candidate}")
    return resolved


def safe_regular_file(path: Path, *, require_nonempty: bool = False) -> Path:
    if not path.is_absolute():
        die(f"file must be an absolute path: {path}")
    try:
        info = path.lstat()
    except FileNotFoundError:
        die(f"file does not exist: {path}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        die(f"file must be a regular file, not a symlink: {path}")
    if info.st_uid != os.getuid():
        die(f"file is not owned by the current user: {path}")
    if require_nonempty and info.st_size == 0:
        die(f"file is empty: {path}")
    return path.resolve(strict=True)


def atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def new_tag() -> str:
    return f"{int(time.time()):x}-{secrets.token_hex(6)}"


def create_exchange(args: argparse.Namespace) -> None:
    root = ensure_directory(storage_root(), create=True)
    source = safe_regular_file(Path(args.task_file), require_nonempty=True)
    contexts = [safe_regular_file(Path(item)) for item in args.context_file]
    tag = new_tag()
    task_dir = root / tag
    task_dir.mkdir(mode=0o700)
    marker = f"HERDR_DELEGATE_DONE_{tag.upper().replace('-', '_')}"
    reply_tmp = task_dir / "reply.tmp.md"
    reply = task_dir / "reply.md"
    result = task_dir / "result.md"
    script = Path(__file__).resolve()

    context_lines = "\n".join(f"- `{path}`" for path in contexts) or "- なし"
    task_text = source.read_text(encoding="utf-8")
    document = f"""# Delegated task

## Task

{task_text.rstrip()}

## Additional context files

{context_lines}

## Completion contract

1. この依頼だけを実行し、結果をMarkdownで作成する。
2. 結果を `{result}` へ書き、次のコマンドをそのまま実行して確定する。

   `{script} complete --task-dir {task_dir} --reply-file {result}`

3. コマンドが出力する一意な完了markerを改変せず表示して完了する。
4. 結果は直上の親にだけ返す。ネスト委譲時もrootへ直接通知しない。

確定先は `{reply}`、書き込み中の一時先は `{reply_tmp}` である。
"""
    atomic_write(task_dir / "task.md", document)
    atomic_write(task_dir / "marker", marker + "\n")
    print(json.dumps({
        "tag": tag,
        "task_dir": str(task_dir),
        "task_path": str(task_dir / "task.md"),
        "reply_path": str(reply),
        "marker": marker,
    }, ensure_ascii=False))


def complete_exchange(args: argparse.Namespace) -> None:
    task_dir = safe_task_dir(args.task_dir)
    source = safe_regular_file(Path(args.reply_file), require_nonempty=True)
    marker_path = safe_regular_file(task_dir / "marker", require_nonempty=True)
    reply_tmp = task_dir / "reply.tmp.md"
    reply = task_dir / "reply.md"
    lock = task_dir / ".complete.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError:
        die(f"another process is finalizing this reply: {reply}")
    try:
        if reply.exists() or reply.is_symlink():
            die(f"reply is already finalized: {reply}")
        atomic_write(reply_tmp, source.read_text(encoding="utf-8"))
        os.replace(reply_tmp, reply)
    finally:
        lock.rmdir()
    print(marker_path.read_text(encoding="utf-8").strip())


def collect_exchange(args: argparse.Namespace) -> None:
    task_dir = safe_task_dir(args.task_dir)
    reply = safe_regular_file(task_dir / "reply.md", require_nonempty=True)
    content = reply.read_text(encoding="utf-8")
    print(content, end="" if content.endswith("\n") else "\n")
    if not args.keep:
        shutil.rmtree(task_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a Markdown task exchange")
    create.add_argument("--task-file", required=True)
    create.add_argument("--context-file", action="append", default=[])
    create.set_defaults(handler=create_exchange)

    complete = subparsers.add_parser("complete", help="atomically finalize a child reply")
    complete.add_argument("--task-dir", required=True)
    complete.add_argument("--reply-file", required=True)
    complete.set_defaults(handler=complete_exchange)

    collect = subparsers.add_parser("collect", help="validate and print a finalized reply")
    collect.add_argument("--task-dir", required=True)
    collect.add_argument("--keep", action="store_true")
    collect.set_defaults(handler=collect_exchange)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
