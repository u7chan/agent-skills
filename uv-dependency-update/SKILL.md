---
name: uv-dependency-update
description: >
  Use this when asked to update dependencies in a uv-managed Python project, especially when the
  request mentions `pyproject.toml`, `uv.lock`, a specific Python package, or refreshing packages
  without taking a major-version upgrade. It captures a safe workflow for choosing whether to
  update only the lockfile or also the declared requirement, applying the matching uv command,
  and validating the project afterward. Do not use it for major-version upgrades.
---

# uv Nonmajor Updater

## Overview

Use this skill when working on dependency updates in a uv-managed Python project.
It keeps dependency changes deliberate instead of blindly refreshing `uv.lock` or rewriting version specifiers.
This skill is limited to non-major updates.

## When to Use This Skill

- When asked to update one package in a uv project
- When asked to refresh multiple dependencies or the whole lockfile without a major bump
- When `pyproject.toml` and `uv.lock` need to stay in sync
- When a dependency bump may require source or test updates

Do not use this skill for major-version upgrades.
Handle those with a separate major-upgrade workflow.

## What the Agent Does

1. Read the local project instructions and inspect the dependency declarations before changing anything.
2. Determine whether the request is a lockfile refresh, a declared-requirement change, a targeted package update, or a broader refresh.
3. Choose the smallest uv command that matches that intent.
4. Reject or defer the work if it would require a major-version bump.
5. Update code or tests only if the non-major release changed behavior in practice.
6. Run the project's validation commands and report the result.

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
Read `pyproject.toml` and identify:

- the dependency location: `project.dependencies`, optional dependencies, or `[dependency-groups]`
- whether the package is runtime or development-only
- the available validation commands

Inspect package usage with `rg` before changing a dependency that may affect code behavior.

### Step 2: Determine the Update Intent

Decide which of these applies:

- `lockfile-refresh`: refresh resolved versions without changing the declared requirement
- `targeted-within-series`: update one named package within the current intended release series
- `broad-refresh`: refresh many packages while staying off major upgrades
- `specifier-change`: update the declared requirement in `pyproject.toml` because the user asked for a newer allowed series

Do not assume that the current declared requirement prevents a major bump.
In uv projects, many dependencies are recorded with only a lower bound such as `pkg>=1.2.3`, which can still allow a new major release.

### Step 3: Apply the Smallest Correct uv Command

Prefer commands that match the requested scope:

- `uv lock --upgrade-package <pkg>` for a targeted lockfile refresh when the declared requirement should not change
- `uv lock --upgrade` for a broader lockfile refresh when the declared requirements should not change
- `uv add '<pkg><specifier>'` for updates that must rewrite the declared requirement in `pyproject.toml`
- `uv add --group <group> '<pkg><specifier>'` when the package lives in a dependency group such as `dev`

Use `uv add` only when the requested change requires a new declared specifier.
If only one package is changing, avoid unrelated dependency churn.

### Step 4: Guard Against Major Upgrades

Before finishing, inspect the resulting versions in both `pyproject.toml` and `uv.lock`.

If any updated package crossed a major version boundary:

- do not continue under this skill
- report which package crossed the boundary
- hand off to a separate major-upgrade workflow

For non-major updates that still affect behavior:

- inspect where the package is used with `rg`
- update code only where the new release changed behavior in practice
- update tests that assert the old behavior

### Step 5: Validate the Result

Run the narrowest meaningful checks first, then the required project checks.
For this repository, prioritize:

- `uv run ruff check .`
- `uv run pytest`
- `uv run ty check`

If a command cannot run, state why and what remains unverified.

## Quality Check

- [ ] The chosen uv command matches the user's requested scope
- [ ] No dependency was upgraded across a major boundary
- [ ] `pyproject.toml` changed only when the request required a declared-specifier update
- [ ] `uv.lock` reflects the dependency update
- [ ] Any behavior changes from non-major updates were handled in code or tests
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

- `AGENTS.md`
- `pyproject.toml`
- `uv.lock`

