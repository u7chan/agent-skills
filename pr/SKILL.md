---
name: pr
description: Suggest PR body in markdown format
---

## Workflow

### 1. Check Context
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
