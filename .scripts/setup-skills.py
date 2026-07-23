#!/usr/bin/env python3
"""スキル単位のシンボリックリンクをエージェントのスキルルートに作成する。

管理構造 skills/<category>/<skill>/ から各エージェントの探索ルートへ
<skill> -> <repo>/skills/<category>/<skill> のリンクを作成する。
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

AGENT_ROOTS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
    "opencode": ".opencode/skills",
}


def discover_skill_dirs() -> list[Path]:
    """skills/ 配下の全スキルディレクトリを返す。"""
    result = []
    for category_dir in sorted(SKILLS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                result.append(skill_dir)
    return result


def setup(agent: str, home: Path, dry_run: bool = False) -> bool:
    skill_root = home / AGENT_ROOTS[agent]
    if not skill_root.parent.is_dir():
        print(f"ERROR: {skill_root.parent} does not exist", file=sys.stderr)
        return False

    skill_root.mkdir(parents=True, exist_ok=True)

    ok = True
    for skill_dir in discover_skill_dirs():
        name = skill_dir.name
        link = skill_root / name
        target = skill_dir.resolve()

        # すでに正しいリンクがあればスキップ
        if link.is_symlink() and link.resolve() == target:
            if dry_run:
                print(f"  [ok] {name} -> {target}")
            continue

        # 同名の実体がある場合
        if link.exists() and not link.is_symlink():
            print(f"  [skip] {name}: 同名のファイル/ディレクトリが存在します", file=sys.stderr)
            ok = False
            continue

        # 同名の別リンク先がある場合
        if link.is_symlink():
            existing = link.resolve()
            print(f"  [warn] {name}: リンク先が異なります ({existing} != {target})", file=sys.stderr)
            if not dry_run:
                link.unlink()
                link.symlink_to(target)

        # 新規作成
        if not link.exists():
            if dry_run:
                print(f"  [new] {name} -> {target}")
            else:
                link.symlink_to(target)
                print(f"  [ok] {name} -> {target}")

    return ok


def uninstall(agent: str, home: Path, dry_run: bool = False) -> bool:
    skill_root = home / AGENT_ROOTS[agent]
    if not skill_root.is_dir():
        return True

    for skill_dir in discover_skill_dirs():
        name = skill_dir.name
        link = skill_root / name
        if not link.is_symlink():
            continue

        target = link.resolve()
        expected = skill_dir.resolve()
        if target != expected:
            print(f"  [skip] {name}: 管理対象外のリンク", file=sys.stderr)
            continue

        if dry_run:
            print(f"  [del] {name}")
        else:
            link.unlink()
            print(f"  [ok] {name} 削除")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup per-skill symlinks for agent discovery")
    parser.add_argument("--agent", required=True, choices=list(AGENT_ROOTS),
                        help="Target agent")
    parser.add_argument("--home", default=os.environ.get("HOME", str(Path.home())),
                        help="Home directory (default: $HOME)")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove symlinks instead of creating them")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without executing")
    args = parser.parse_args()

    home = Path(args.home)
    if not home.is_dir():
        print(f"ERROR: {home} is not a directory", file=sys.stderr)
        sys.exit(1)

    skill_root = home / AGENT_ROOTS[args.agent]
    print(f"Agent: {args.agent}")
    print(f"Skill root: {skill_root}")

    if args.uninstall:
        print("Mode: uninstall")
        ok = uninstall(args.agent, home, args.dry_run)
    else:
        print("Mode: install")
        print(f"Found {len(discover_skill_dirs())} skills")
        ok = setup(args.agent, home, args.dry_run)

    if args.dry_run:
        print("\nDry run — no changes made.")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
