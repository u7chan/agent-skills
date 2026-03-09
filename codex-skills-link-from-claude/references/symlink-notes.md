# Symlink Notes

## Known Good Pattern

For this repository layout, the working symlink is:

    .codex/skills -> ../.claude/skills

This matches the monorepo-level pattern:

    /home/u7dev/workspace/monorepo/.codex/skills -> ../.claude/skills

## Known Bad Pattern

This looks plausible but is wrong:

    .codex/skills -> ./.claude/skills

Why it fails:
- Symlink targets are resolved relative to the symlink location, not the repo root.
- From `.codex/skills`, `./.claude/skills` points at `.codex/.claude/skills`.

## Practical Guidance

- If a user says editor discovery or VSCode tree behavior still looks wrong, compare the repo-local link against a known working parent repo link with `readlink`.
- When in doubt, recreate `.codex/skills` using `../.claude/skills` and verify with `readlink -f`.
