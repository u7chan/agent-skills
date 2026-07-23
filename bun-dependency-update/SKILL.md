---
name: bun-dependency-update
description: >
  Bunアプリの依存関係を一括で非メジャー更新するとき、または特定パッケージをメジャー更新するときに使う。
  upstream調査、ユーザー確認、1パッケージずつの更新、プロジェクト検証まで扱う。
---

# Bun Dependency Updater

## Overview

Use this skill when working on dependency updates in a Bun app.
It keeps package updates deliberate instead of blindly bumping versions or rewriting semver ranges.
Start by deciding whether the request stays within the current major series or crosses into a new one.
For non-major work, prefer bundling compatible updates together unless the user asked for a narrower change.
For major work, research first, confirm the plan with the user, then upgrade one package at a time.

## When to Use This Skill

- When asked to update one package in a Bun project
- When asked to refresh multiple dependencies or the whole Bun app
- When `package.json` and `bun.lock` need to be updated together
- When a dependency bump may require code changes or test updates
- When the request may cross a major version boundary and needs researched migration guidance

## What the Agent Does

1. Read the local project instructions and package scripts before changing dependencies.
2. Inspect the current dependency entry and determine whether the request is non-major or major.
3. For non-major work, choose the broadest safe Bun command that matches the requested scope.
4. For major work, research upstream breaking changes before editing anything.
5. Stop for user confirmation before applying a major-version upgrade.
6. Update application code or tests if the dependency change requires it.
7. Run the project's validation commands and confirm the result.

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

### Step 2: Determine Whether This Is a Major Upgrade

Classify the request before editing files:

- `range-preserving`: keep the declared semver range and refresh the lockfile-resolved version
- `latest`: move the declared dependency to the newest available release
- `latest-within-major`: move the declared dependency to the newest available release within the current major series
- `targeted`: update only the package named by the user
- `broad`: update multiple packages or all dependencies
- `major`: move a package to a new major series

Treat `latest` in this skill as `latest-within-major` unless the user explicitly asks for a new major series.
If the user did not ask for a narrow scope, prefer `broad` for non-major updates so compatible changes can land together.

If the request is `major`, do not edit yet. Move to the major-upgrade branch of this workflow.

### Step 3A: Non-Major Flow

Apply the broadest safe Bun command that matches the requested scope:

- `bun update --latest` only when the resulting updates stay within the current major series
- `bun update` for broader range-preserving refreshes
- `bun update --latest <pkg>` only when it still resolves within the current major series
- `bun update <pkg>` for a targeted update within the existing declared range

When the user gives a general non-major refresh request, prefer `bun update` or `bun update --latest` over splitting the work into many targeted updates.
Use a targeted command only when the user named a package, asked for a narrow change, or when a broader update would exceed this skill's non-major boundary.
If only one package is supposed to change, avoid unrelated dependency churn.

If `bun update --latest` would cross a major boundary, stop the non-major flow and switch to the major-upgrade branch below.

Before finishing the non-major update, inspect the changed versions in `package.json` and `bun.lock`.
If any dependency crossed a major version:

- do not continue under the non-major flow
- report which package crossed the boundary
- switch to the major-upgrade branch for that package

For non-major updates that still affect behavior:

- inspect where the package is used with `rg`
- update code only if the minor or patch release changed behavior in practice
- update tests that assert the old behavior

### Step 3B: Major-Upgrade Flow

Treat a major bump as an interactive workflow.
Before editing `package.json` or `bun.lock`:

- inspect where the package is used with `rg`
- confirm the current version and the target major version
- use web search and prioritize official migration guides, changelogs, release notes, and API docs
- collect only the breaking changes that are relevant to this repository

Before making changes, present a short checkpoint to the user that includes:

- the package to upgrade
- the current and target major versions
- the main relevant breaking changes
- the expected code areas to touch
- the validation commands that will be run

Stop here until the user confirms.
After confirmation:

- upgrade only one package at a time
- prefer the smallest change that reaches the confirmed target
- apply only the compatibility fixes supported by local usage and the researched sources
- avoid bundling unrelated dependency churn into the same change

### Step 4: Validate the Result

Run the narrowest meaningful checks first, then the required project checks.
For this repository, prioritize:

- `bun run lint`
- `bun test`

If a command cannot run, state why and what remains unverified.

## Quality Check

- [ ] The workflow explicitly decides between non-major and major before editing
- [ ] Non-major requests use the broadest safe Bun command when no narrow scope was requested
- [ ] Major requests require upstream research before editing files
- [ ] Major requests stop for user confirmation before the dependency is changed
- [ ] Major upgrades are limited to one package at a time
- [ ] `package.json` changed only when the selected flow required it
- [ ] `bun.lock` reflects the dependency update
- [ ] Any required behavior changes were handled in code or tests
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

See `AGENTS.md`, `package.json`, and `bun.lock`.
