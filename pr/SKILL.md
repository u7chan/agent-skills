---
name: pr
description: Suggest PR body in markdown format
---

## Workflow

### 1. PR Body Structure

Understand the output format first.

**Structure:**
```markdown
## Summary

Brief description of what this PR does.

## Changes

- Change 1
- Change 2

## Details

Optional: technical details, implementation notes, etc.

## Checklist

- [ ] Item 1
- [ ] Item 2
```

**Guidelines:**
- Use clear, concise language
- Focus on *what* and *why*
- Keep summary under 2-3 sentences
- Checklist should reflect actual changes

### 2. Check Context

**IMPORTANT: Do NOT run any git commands yet.**

First, check if sufficient context is already available in the conversation (branch name, commit history, or changed files).

**If context IS available:**
1. Show the branch name only
2. Ask the user: "Is this sufficient? Reply \"OK\" and I'll proceed to create the PR body."
3. Wait for user confirmation
4. If user responds with "OK" or confirmation, **skip directly to Step 3** and draft the PR body immediately
5. If user needs more info (NOT "OK"), run these git commands:
   - `git log --oneline main..HEAD`
   - `git diff --name-status main`

**Preview format:**
```
Context is available.
Branch: <branch-name>

Is this sufficient? Reply "OK" and I'll proceed to create the PR body.
```

**If context is NOT available:**
Immediately run these git commands to gather context (no user confirmation needed):
- `git branch --show-current`
- `git log --oneline main..HEAD`
- `git diff --name-status main`

### 3. Draft PR Body

Create the PR body following the structure from Step 1, using the context gathered in Step 2.

**Wrap the entire PR body in a markdown code block:**

~~~
```markdown
## Summary
...
```
~~~
