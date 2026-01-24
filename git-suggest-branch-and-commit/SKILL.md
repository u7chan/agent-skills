---
name: git-suggest-branch-and-commit
description: Suggest a branch name and commit message from git status/diff
---

## Purpose

Automatically summarize **staged** repository changes and suggest a branch name and commit message.

※ Unstaged changes in the working tree are **not** included.

※ **Direct commits to the `main` branch are strictly prohibited.**
All commits must be made on a newly created or existing feature branch suggested by this agent.

## How to use

1. Run this agent.
   - It inspects `git status` and `git diff --staged`.
2. Review the proposed **branch name** and **commit message**.
3. **Switch to the proposed branch (or create it if it does not exist).**
4. Commit the staged changes **only after confirming you are not on `main`**.
5. If needed, the agent may request additional context.

⚠️ If the current branch is `main`, you must switch branches before committing.

## Inputs

- Repository state (`git status`, only items under “Changes to be committed” are considered)
- (optional) `git diff --staged` / `git diff --cached`
- (optional) Goal or intent

## Outputs

- Change summary (staged changes only)
- **Branch (required):** `prefix/short-slug`
- **Commit (required):** `prefix: imperative message`
- Notes: split suggestions if multiple independent staged changes exist

## Branch & Commit Rules

- Commits on `main` are **not allowed**
- Always create or switch to the suggested branch **before** committing
- One logical change per commit

## Prefix rules

Choose one of: `feat`, `update`, `refactor`
