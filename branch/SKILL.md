---
name: branch
description: Suggest branch names and create branches
---

## Workflow

### 1. Check Current Branch

Run this git command to check the current branch:
- `git branch --show-current`

### 2. Determine Scope (for monorepo)

If the project appears to be a monorepo (multiple packages/apps), get the current directory name:
```bash
basename "$(pwd)"
```

### 3. Branch Name

**Standard format:** `<type>/<description>`

**Monorepo format:** `<type>/<scope>-<description>` or `<type>/<scope>/<description>`

**Types:** `feature/` `fix/` `docs/` `refactor/` `test/` `chore/`

**Rules:**
- Lowercase with hyphens (e.g., `feature/add-user-auth`)
- 3-5 words, concise
- Include issue# if applicable (e.g., `fix/issue-123-login-error`)
- For monorepo: include scope as prefix (e.g., `feature/auth-add-oauth`)

### 4. Output Format

**On main/develop* branch:**
```
## Recommended Branch

git checkout -b <type>/<description>
```

**On other branches:**
```
## Current Status
Already on branch: <branch-name>

## Suggested Branch (if needed)
git checkout -b <type>/<description>
```

### 5. User Confirmation

If the user says "OK" after the suggestion, execute the following automatically:

**On main/develop* branch:**
```bash
git switch -c <type>/<description>
```

**On other branches:**
Ask the user whether to create a new branch from current branch or checkout to main/develop first.
