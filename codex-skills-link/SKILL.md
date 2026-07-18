---
name: codex-skills-link
description: >
  Claude CodeのスキルをCodexでも使えるように依頼されたときに使う。
  `.claude/skills` を指す `.codex/skills` symlinkを正しい相対パスで作成する。
  操作対象は`.codex/skills`だけとし、`.codex`全体は削除しない。
---

# Codex Skills Link

## Overview

Use this skill when a project already stores skills under `.claude/skills` and you want Codex to reuse them through `.codex/skills`.
It documents the exact symlink shape that worked here, including the path-resolution gotcha.

## When to Use This Skill

- When asked to let Codex use existing Claude Code skills
- When a repo already has `.claude/skills` and is missing `.codex/skills`
- When `.codex/skills` exists but editor or tool discovery is failing

## What the Agent Does

1. Check whether `.claude/skills` exists.
2. Check whether `.codex/skills` already exists and what it points to.
3. Create `.codex` if needed and create or replace only `.codex/skills`.
4. Verify the link with `readlink` and `readlink -f`.
5. Confirm that files under `.codex/skills/...` are reachable.

## Input and Output

**Input:**
- A repository with skills under `.claude/skills`

**Output:**
- `.codex/skills` symlinked to the same skill directory
- Verification output showing the resolved target

## Step Details

### Step 1: Inspect Current State

Check:
- `.claude/skills`
- `.codex`
- `.codex/skills`

If `.codex/skills` already exists, inspect it before changing anything.

Never remove, recreate, or overwrite the whole `.codex` directory. Files such as `.codex/config.toml` and other entries are out of scope.

### Step 2: Use the Correct Relative Symlink

From the project root, create:

    .codex/skills -> ../.claude/skills

Important:
- Do not use `./.claude/skills` as the symlink target from inside `.codex`.
- `./.claude/skills` resolves to `.codex/.claude/skills`, which is wrong.
- The working target is `../.claude/skills`.

### Step 3: Limit Changes to `.codex/skills`

If `.codex` is missing, create it. Then create the link only when `.codex/skills` is absent:

    mkdir -p .codex
    ln -s ../.claude/skills .codex/skills

If `.codex/skills` is already the expected symlink, do nothing. If it is another symlink, resolve the exact target and replace only that symlink after confirming the requested target. If it is a real file or directory, stop and request approval before replacing it. Do not use recursive deletion.

### Step 4: Verify Resolution

Run:

    readlink .codex/skills
    readlink -f .codex/skills

Expected shape:
- `readlink` returns `../.claude/skills`
- `readlink -f` resolves to the repo's real `.claude/skills` directory

### Step 5: Verify Traversal

List a known file through the symlinked path, for example:

    ls .codex/skills
    ls .codex/skills/<skill-name>

Do not stop after only checking the symlink string.
Confirm that the linked directory contents are actually reachable.

## Quality Check

- [ ] `.claude/skills` exists
- [ ] No entry other than `.codex/skills` was changed
- [ ] `.codex/skills` points to `../.claude/skills`
- [ ] `readlink -f .codex/skills` resolves to the expected real directory
- [ ] A file inside `.codex/skills/...` can be listed successfully
- [ ] The link shape matches the pattern known to work with editor discovery in this repo

## References

- `references/symlink-notes.md`
