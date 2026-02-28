---
name: commit
description: Suggest commit messages
---

## Workflow

### 1. Check Current Branch

Run this git command to check the current branch:
- `git branch --show-current`

### 2. Commit Message Format

**Title (≤60 chars):**
- Imperative mood ("add" not "adds")
- Lowercase (except symbols/acronyms)
- Prefix: `feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`

**Body:**
- Explain *what* and *why*
- Imperative mood

### 3. Output Format

```
## Commit Message

git commit -m "<prefix>: <title>" -m "<body>"
```

### 4. Staging

```bash
git add <file>
# or use `git hunks` for specific changes
git commit -m "title" -m "body"
```

### 5. User Confirmation

If the user says "OK" after the suggestion, execute the following automatically:

```bash
git add .  # only if files are not staged
git commit -m "<prefix>: <title>" -m "<body>"
```
