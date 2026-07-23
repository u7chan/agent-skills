---
name: uv-dependency-update
description: >
  uv管理のPythonプロジェクトで依存関係を一括で非メジャー更新するとき、または特定パッケージをメジャー更新するときに使う。
  upstream調査、ユーザー確認、1パッケージずつの更新、プロジェクト検証まで扱う。
---

# uv Dependency Updater

## Overview

Use this skill when working on dependency updates in a uv-managed Python project.
It keeps dependency changes deliberate instead of blindly refreshing `uv.lock` or rewriting version specifiers.
Start by deciding whether the request stays within the current major series or crosses into a new one.
For non-major work, prefer bundling compatible updates together unless the user asked for a narrower change.
For major work, research first, confirm the plan with the user, then upgrade one package at a time.

## When to Use This Skill

- When asked to update one package in a uv project
- When asked to refresh multiple dependencies or the whole lockfile without a major bump
- When `pyproject.toml` and `uv.lock` need to stay in sync
- When a dependency bump may require source or test updates
- When the request may cross a major version boundary and needs researched migration guidance

## What the Agent Does

1. Read the local project instructions and inspect the dependency declarations before changing anything.
2. Determine whether the request is non-major or major.
3. For non-major work, choose the broadest safe uv command that matches the requested scope.
4. For major work, research upstream breaking changes before editing anything.
5. Stop for user confirmation before applying a major-version upgrade.
6. Update code or tests only if the dependency change requires it.
7. Run the project's validation commands and report the result.

## Input and Output

**Input:**
- A uv-managed Python project with `pyproject.toml`
- A request to update one dependency or a set of dependencies
- Project-specific verification commands from `AGENTS.md`, `pyproject.toml`, or nearby docs

**Output:**
- Updated dependency entries in `pyproject.toml` when required by the request
- Updated `uv.lock`
- Any required compatibility fixes in source or tests
- A concise report of what changed and whether validation passed

## Step Details

### Step 1: Inspect the Local Project Rules

Open `AGENTS.md` if it exists.
See `references/dependency-workflow.md` for pyproject.toml inspection.

### Step 2: Determine Whether This Is a Major Upgrade

Classify the request before editing files:

- `lockfile-refresh`: refresh resolved versions without changing the declared requirement
- `targeted-within-series`: update one named package within the current intended release series
- `broad-refresh`: refresh many packages while staying off major upgrades
- `specifier-change`: update the declared requirement in `pyproject.toml` because the user asked for a newer allowed series
- `major`: move a package to a new major series

Do not assume the current declared requirement prevents a major bump; uv projects often use lower bounds like `pkg>=1.2.3` that can allow a new major release.
If the user did not ask for a narrow scope, prefer `broad-refresh` for non-major updates so compatible changes can land together.

If the request is `major`, do not edit yet. Move to the major-upgrade branch of this workflow.

### Step 3A: Non-Major Flow

Apply the broadest safe uv command that matches the requested scope:

- `uv lock --upgrade` for a broader lockfile refresh when the declared requirements should not change
- `uv lock --upgrade-package <pkg>` for a targeted lockfile refresh when the declared requirement should not change
- `uv add '<pkg><specifier>'` for updates that must rewrite the declared requirement in `pyproject.toml`
- `uv add --group <group> '<pkg><specifier>'` when the package lives in a dependency group such as `dev`

When the user gives a general non-major refresh request, prefer `uv lock --upgrade` over splitting the work into many targeted updates.
Use `uv add` only when the requested change requires a new declared specifier.
Use a targeted command only when the user named a package, asked for a narrow change, or when a broader refresh cannot stay within this skill's non-major boundary.
If only one package is supposed to change, avoid unrelated dependency churn.

Before finishing, inspect the resulting versions in both `pyproject.toml` and `uv.lock`.
If any updated package crossed a major version boundary:

- do not continue under the non-major flow
- report which package crossed the boundary
- switch to the major-upgrade branch for that package

For non-major updates that still affect behavior:

- inspect where the package is used with `rg`
- update code only where the new release changed behavior in practice
- update tests that assert the old behavior

### Step 3B: Major-Upgrade Flow

Treat a major bump as an interactive workflow.
Before editing `pyproject.toml` or `uv.lock`:

- inspect where the package is used with `rg`
- confirm the current version and the target major version
- use web search and prioritize official migration guides, changelogs, release notes, and API docs
- collect only the breaking changes that are relevant to this repository

Before making changes, present a short checkpoint to the user that includes:

- the package to upgrade
- the current and target major versions
- the declaration that will change in `pyproject.toml`
- the main relevant breaking changes
- the expected code areas to touch
- the validation commands that will be run

Stop here until the user confirms.
After confirmation:

- upgrade only one package at a time
- prefer `uv add` with an explicit specifier; update the lockfile after the declaration change
- apply only the compatibility fixes supported by local usage and the researched sources
- avoid bundling unrelated dependency churn into the same change

### Step 4: Validate the Result

Run the narrowest meaningful checks first, then the required project checks.
For this repository, prioritize:

- `uv run ruff check .`
- `uv run pytest`
- `uv run ty check`

If a command cannot run, state why and what remains unverified.

## Quality Check

- [ ] The workflow explicitly decides between non-major and major before editing
- [ ] Non-major requests use the broadest safe uv command when no narrow scope was requested
- [ ] Major requests require upstream research before editing files
- [ ] Major requests stop for user confirmation before the dependency is changed
- [ ] Major upgrades are limited to one package at a time
- [ ] `pyproject.toml` changed only when the selected flow required it
- [ ] `uv.lock` reflects the dependency update
- [ ] Any required behavior changes were handled in code or tests
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

See `AGENTS.md`, `pyproject.toml`, and `uv.lock`.
