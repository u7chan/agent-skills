---
name: claude-to-codex-skills-link
description: >
  Use this when asked to make Claude Code skills available to Codex by creating a
  `.codex/skills` symlink that points to `.claude/skills`. It captures the exact
  symlink pattern that works in this repo and avoids the relative-path mistake that
  breaks editor discovery.
---

# Claude To Codex Skills Link

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
3. Create or recreate `.codex` and add the symlink using the working relative path.
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

### Step 2: Use the Correct Relative Symlink

From the project root, create:

    .codex/skills -> ../.claude/skills

Important:
- Do not use `./.claude/skills` as the symlink target from inside `.codex`.
- `./.claude/skills` resolves to `.codex/.claude/skills`, which is wrong.
- The working target is `../.claude/skills`.

### Step 3: Preferred Command Shape

Use this sequence when the repo-local `.codex` layout needs to be created or reset:

    rm -rf .codex
    mkdir .codex
    ln -s ../.claude/skills .codex/skills

If you must preserve other contents in `.codex`, replace only the `skills` entry instead of removing the whole directory.

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
- [ ] `.codex/skills` points to `../.claude/skills`
- [ ] `readlink -f .codex/skills` resolves to the expected real directory
- [ ] A file inside `.codex/skills/...` can be listed successfully
- [ ] The link shape matches the pattern known to work with editor discovery in this repo

## References

- `references/symlink-notes.md`
