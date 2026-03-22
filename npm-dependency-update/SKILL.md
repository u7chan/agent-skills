---
name: npm-dependency-update
description: >
  Use this when asked to update dependencies in an npm application, especially when the
  request involves `package.json`, `package-lock.json`, a specific package, or refreshing
  packages to newer non-major versions. It captures a safe workflow for preferring broad
  range-preserving refreshes with `npm update` unless the user asks to move declared ranges,
  applying targeted `npm install <pkg>@...` only when needed, and verifying the project
  after compatibility fixes. Do not use it for major-version upgrades.
---

# npm Nonmajor Updater

## Overview

Use this skill when working on dependency updates in an npm app.
It keeps package updates deliberate instead of blindly bumping versions or rewriting semver ranges.
For non-major work, prefer broad range-preserving refreshes unless the user asked for a narrower change or a direct dependency range move.
This skill is limited to non-major updates.

## When to Use This Skill

- When asked to update one package in an npm project
- When asked to refresh multiple dependencies or the whole npm app
- When `package.json` and `package-lock.json` need to be updated together
- When a dependency bump may require code changes or test updates

Do not use this skill for major-version upgrades.
Handle those with a separate skill and workflow.

## What the Agent Does

1. Read the local project instructions, dependency manifest, and package scripts before changing dependencies.
2. Inspect the current dependency entry and determine whether the request is range-preserving or requires moving a direct dependency within the same major series.
3. Choose the broadest safe npm command that matches that intent instead of defaulting to narrowly targeted updates.
4. Reject or defer the work if it would require a major-version bump.
5. Update application code or tests if the new package behavior requires it.
6. Run the project's validation commands and confirm the result.

## Input and Output

**Input:**
- An npm app with `package.json`
- An update request for one package or a set of packages
- Project-specific verification commands from `AGENTS.md`, `package.json`, or nearby docs

**Output:**
- Updated dependency entries in `package.json` when needed
- Updated `package-lock.json` or `npm-shrinkwrap.json`
- Any required compatibility fixes in source or tests
- A clear report of what changed and whether validation passed

## Step Details

### Step 1: Inspect the Local Project Rules

Open `AGENTS.md` if it exists.
Read `package.json` scripts and note the required verification commands.
Check whether the repo uses `package-lock.json`, `npm-shrinkwrap.json`, or workspaces.

### Step 2: Determine the Update Intent

Decide which of these applies:

- `range-preserving`: keep the declared semver range and refresh the lockfile-resolved version
- `latest-within-major`: move a direct dependency declaration to a newer release without crossing the current major series
- `targeted`: update only the package named by the user
- `broad`: update multiple packages or all dependencies

Treat a general refresh request as `broad` plus `range-preserving` unless the user explicitly asks to move declared ranges.
Do not assume a major-version bump unless the user explicitly asks for a separate major-upgrade workflow.
If the repo uses npm workspaces, determine whether the request applies to the root package or a specific workspace before running commands.

### Step 3: Apply the Broadest Safe npm Command

Prefer commands that match the requested scope while avoiding unnecessary PR fragmentation:

- `npm update` for broader range-preserving refreshes
- `npm update <pkg>` for a targeted update within the existing declared range
- `npm install <pkg>@<version-or-range>` only when a direct dependency range must move forward within the same major series
- `npm install` after manual `package.json` edits so the lockfile and installed tree are synchronized

When replacing a direct dependency with `npm install <pkg>@...`, preserve its dependency class such as `dependencies` or `devDependencies`.
When the user gives a general non-major refresh request, prefer `npm update` over splitting the work into many targeted updates.
Use a targeted command only when the user named a package, asked for a narrow change, or when changing `package.json` for one dependency is the safer path.
If only one package is supposed to change, avoid unrelated dependency churn.

### Step 4: Guard Against Major Upgrades

Before finishing the update, inspect the changed versions in `package.json` and `package-lock.json` or `npm-shrinkwrap.json`.

If any dependency crossed a major version:

- do not continue under this skill
- report which package crossed the boundary
- leave the request for a separate major-upgrade skill or workflow

For non-major updates that still affect behavior:

- inspect where the package is used with `rg`
- update code only if the minor or patch release changed behavior in practice
- update tests that assert the old behavior

### Step 5: Validate the Result

Run the narrowest meaningful checks first, then the required project checks.
For npm projects, prioritize:

- `npm run lint` when a lint script exists
- `npm test` when a test script exists

Run any additional project-specific commands required by `AGENTS.md` or nearby docs.
If a command cannot run, state why and what remains unverified.

## Quality Check

- [ ] The chosen npm command matches the user's requested scope and defaults to a broad range-preserving refresh when no narrow scope was requested
- [ ] No dependency was upgraded across a major boundary
- [ ] `package.json` changed only when the requested update required it
- [ ] `package-lock.json` or `npm-shrinkwrap.json` reflects the dependency update
- [ ] Any behavior changes from non-major updates were handled in code or tests
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

- `AGENTS.md`
- `package.json`
- `package-lock.json`
