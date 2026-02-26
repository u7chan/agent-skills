---
name: pr
description: Suggest PR body in markdown format
---

## Workflow

### 1. Check Context

**Before gathering context, check if sufficient context is already available** (e.g., branch name, commit history, or changed files are already known from the conversation).

- If context is already available:
  - Present what you know (branch name, commits, files changed)
  - Ask the user: "Is this information sufficient? If yes, I'll proceed to Step 2."
  - If the user responds with "OK" or confirmation, skip to Step 2

- If context is NOT available, gather it:
  - Current branch name
  - Commit history (git log --oneline main..HEAD)
  - Files changed (git diff --name-status main)

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
