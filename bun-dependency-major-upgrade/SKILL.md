---
name: bun-dependency-major-upgrade
description: >
  Use this when asked to upgrade a Bun application's dependency across a major version.
  This skill handles one package at a time, researches breaking changes with web search and
  primary sources, confirms the plan with the user before applying the update, and validates
  the app after compatibility fixes.
---

# Bun Major Upgrader

## Overview

Use this skill for major-version dependency upgrades in a Bun app.
It is intentionally interactive: research first, confirm scope with the user, then upgrade one package at a time.

## When to Use This Skill

- When the requested dependency update crosses a major version boundary
- When `bun update --latest` would move a package to a new major series
- When the user wants breaking changes researched before editing code
- When the upgrade risk is high enough that the agent should confirm each step

## What the Agent Does

1. Inspect the local project rules and the package's current usage before changing anything.
2. Research the target major version with web search, prioritizing official migration guides, changelogs, and release notes.
3. Summarize the likely impact and confirm the plan with the user before making changes.
4. Upgrade only one package at a time.
5. Apply the compatibility fixes required by the researched breaking changes.
6. Run the project's validation commands and report what passed, failed, or remains unknown.

## Input and Output

**Input:**
- A Bun app with `package.json`
- A request to upgrade one dependency across a major version boundary
- Local project verification commands from `AGENTS.md`, `package.json`, or nearby docs

**Output:**
- A researched upgrade plan for one package
- User-confirmed upgrade scope before edits
- Updated dependency entry and `bun.lock`
- Required application or test changes for compatibility
- A concise report of upstream impact, code changes, and validation status

## Step Details

### Step 1: Inspect the Local Project Context

Open `AGENTS.md` if it exists.
Read `package.json` scripts and inspect where the package is used with `rg`.

Do not upgrade multiple major dependencies in one pass unless the user explicitly asks for that and confirms the order.

### Step 2: Research Before Editing

Use web search before making dependency or code changes.
Prioritize primary sources:

- official migration guides
- official changelogs
- official release notes
- official API docs

Use secondary sources only when primary sources do not cover a practical migration detail, and label that as an inference.

Collect the minimum useful facts:

- current version and target major version
- breaking changes relevant to the package usage in this repo
- required code migrations
- config, runtime, or peer dependency changes
- test or behavior risks that need explicit verification

### Step 3: Confirm the Plan With the User

Before editing files, present a short upgrade checkpoint to the user that includes:

- the package to upgrade
- the current and target major versions
- the main breaking changes that appear relevant
- the expected code areas to touch
- the validation commands that will be run

Wait for user confirmation before applying the update.
If the research shows unusually high risk or unclear migration guidance, say so plainly and do not proceed on assumption alone.

### Step 4: Upgrade One Package at a Time

Change only the selected package to the approved target major version.
Avoid bundling unrelated dependency churn into the same change.

Prefer the smallest update that reaches the confirmed target.

### Step 5: Apply Compatibility Fixes

Use the researched migration guidance to update the codebase.
Do not guess at API changes that were not confirmed by local usage or source material.

When updating code:

- touch only call sites affected by the researched breaking changes
- update tests that assert old behavior
- preserve existing auth, path-safety, and route constraints in this repo

### Step 6: Validate and Report

Run the required project checks after the change.
For this repository, prioritize:

- `bun run lint`
- `bun test`

Report:

- what upstream sources were used
- what code paths changed
- whether validation passed
- any remaining manual verification or follow-up upgrades

## Interaction Rules

- Treat major upgrades as an interactive workflow, not a fire-and-forget edit.
- Stop for confirmation after research and before dependency edits.
- If a second major upgrade is needed, finish or pause the current one before starting the next.
- If web research is required for accuracy, perform it rather than relying on memory.

## Quality Check

- [ ] The upgrade scope is limited to one major dependency at a time
- [ ] Primary-source web research was done before editing
- [ ] The user confirmed the researched plan before the dependency was changed
- [ ] Code and tests were updated only where the researched breaking changes required it
- [ ] Required project validation commands were run or the blocker was stated clearly

## References

- `AGENTS.md`
- `package.json`
