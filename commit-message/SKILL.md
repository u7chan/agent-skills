---
name: commit-messages
description: Suggest commit messages and branch names
---

## Workflow

### 1. Check Changes
```bash
git diff HEAD
git status --short
git branch --show-current
```

### 2. Branch Name (only if on `main` or `develop-*`)
**Format:** `<type>/<description>`

**Types:** `feature/` `fix/` `docs/` `refactor/` `test/` `chore/`

**Rules:**
- Lowercase with hyphens (e.g., `feature/add-user-auth`)
- 3-5 words, concise
- Include issue# if applicable (e.g., `fix/issue-123-login-error`)

### 3. Commit Message Format
**Title (≤60 chars):**
- Imperative mood ("add" not "adds")
- Lowercase (except symbols/acronyms)
- Prefix: `feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`

**Body:**
- Explain *what* and *why*
- Imperative mood

### 4. Output Format

**On main/develop-* branch:**
```
## Recommended Branch
git checkout -b <type>/<description>

## Commit Message
git commit -m "<prefix>: <title>" -m "<body>"
```

**On other branches:**
```
## Commit Message
git commit -m "<prefix>: <title>" -m "<body>"
```

### 5. Staging
```bash
git add <file>
# or use `git hunks` for specific changes
git commit -m "title" -m "body"
