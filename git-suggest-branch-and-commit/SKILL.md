---
name: git-suggest-branch-and-commit
description: Suggest a branch name and commit message from git status/diff
---

## Purpose

Automatically summarize **staged** repository changes and suggest a branch name and commit message.

※ Unstaged changes in the working tree are **not** included.

## How to use

1. Run this agent.
   - It inspects `git status` and `git diff --staged`.
2. Review the proposed branch name and commit message.
3. Confirm to create/switch to the branch and commit the staged changes.
4. If needed, the agent may request additional context.

## Inputs

- Repository state (`git status`, only items under “Changes to be committed” are considered)
- (optional) `git diff --staged` / `git diff --cached`
- (optional) Goal or intent

## Outputs

- Change summary (staged changes only)
- Branch: `prefix/short-slug`
- Commit: `prefix: imperative message`
- Notes: split suggestions if multiple independent staged changes exist

## Prefix rules

Choose one of: `feat`, `update`, `refactor`
