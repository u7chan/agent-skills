---
name: bun-nonmajor-updater
description: >
  Use this when asked to update dependencies in a Bun application, especially when the
  request involves `package.json`, `bun.lock`, a specific npm package, or refreshing packages
  to newer non-major versions. It captures a safe workflow for choosing the update scope,
  applying the Bun command that matches that scope, and verifying the app still passes its
  project checks. Do not use it for major-version upgrades.
---

# Bun Nonmajor Updater

## Overview

Use this skill when working on dependency updates in a Bun app.
It keeps package updates deliberate instead of blindly bumping versions or rewriting semver ranges.
This skill is limited to non-major updates.

## When to Use This Skill

- When asked to update one package in a Bun project
- When asked to refresh multiple dependencies or the whole Bun app
- When `package.json` and `bun.lock` need to be updated together
- When a dependency bump may require code changes or test updates

Do not use this skill for major-version upgrades.
Handle those with a separate skill and workflow.

## What the Agent Does

1. Read the local project instructions and package scripts before changing dependencies.
2. Inspect the current dependency entry and determine whether the request is range-preserving or latest-version within the same major series.
3. Choose the Bun command that matches that intent instead of defaulting to a full upgrade.
4. Reject or defer the work if it would require a major-version bump.
5. Update application code or tests if the new package behavior requires it.
6. Run the project's validation commands and confirm the result.

## Input and Output

**Input:**
- A Bun app with `package.json`
- An update request for one package or a set of packages
- Project-specific verification commands from `AGENTS.md`, `package.json`, or nearby docs

**Output:**
- Updated dependency entries in `package.json` when needed
- Updated `bun.lock`
- Any required compatibility fixes in source or tests
- A clear report of what changed and whether validation passed

## Step Details

### Step 1: Inspect the Local Project Rules

Open `AGENTS.md` if it exists.
Read `package.json` scripts and note the required verification commands.

### Step 2: Determine the Update Intent

Decide which of these applies:

- `range-preserving`: keep the declared semver range and refresh the lockfile-resolved version
- `latest`: move the declared dependency to the newest available release
- `latest-within-major`: move the declared dependency to the newest available release within the current major series
- `targeted`: update only the package named by the user
- `broad`: update multiple packages or all dependencies

Treat `latest` in this skill as `latest-within-major`.
Do not assume a major-version bump unless the user explicitly asks for a separate major-upgrade workflow.

### Step 3: Apply the Smallest Correct Bun Command

Prefer commands that match the requested scope:

- `bun update <pkg>` for a targeted update within the existing declared range
- `bun update` for broader range-preserving refreshes
- `bun update --latest <pkg>` only when it still resolves within the current major series
- `bun update --latest` only when the resulting updates stay within the current major series

If only one package is changing, avoid unrelated dependency churn.

If `bun update --latest` would cross a major boundary, stop and treat that as out of scope for this skill.

### Step 4: Guard Against Major Upgrades

Before finishing the update, inspect the changed versions in `package.json` and `bun.lock`.

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
For this repository, prioritize:

- `bun run lint`
- `bun test`

If a command cannot run, state why and what remains unverified.

## Quality Check

- [ ] The chosen Bun command matches the user's requested scope
- [ ] No dependency was upgraded across a major boundary
- [ ] `package.json` changed only when the requested update required it
- [ ] `bun.lock` reflects the dependency update
- [ ] Any behavior changes from non-major updates were handled in code or tests
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

- `AGENTS.md`
- `package.json`
