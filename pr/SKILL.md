---
name: pr
description: Suggest PR body in markdown format
---

## Workflow

### 1. Check Context

**IMPORTANT: Do NOT run any git commands yet.**

First, check if sufficient context is already available in the conversation (branch name, commit history, or changed files).

**If context IS available:**
1. Show the branch name only
2. Ask the user: "Is this information sufficient? If yes, I'll proceed to Step 2."
3. Wait for user confirmation
4. If user responds with "OK" or confirmation, **skip directly to Step 2**
5. If user needs more info (NOT "OK"), run these git commands:
   - `git log --oneline main..HEAD`
   - `git diff --name-status main`

**Preview format:**
```
Context is available.
Branch: <branch-name>

Is this sufficient? Reply "OK" and I'll proceed to create the PR body.
```

**If context is NOT available, run this git command:**
- `git branch --show-current`

### 2. PR Body Format
Output in a markdown code block.

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

### 3. Guidelines

- Use clear, concise language
- Focus on *what* and *why*
- Keep summary under 2-3 sentences
- Checklist should reflect actual changes

### 4. Output Format

**Wrap the entire PR body in a markdown code block:**

~~~
```markdown
## Summary
...
```
~~~
