---
name: commit-messages-monorepo
description: Suggest commit messages and branch names for monorepo projects
---

## Workflow

### 1. Check Changes
```bash
git diff HEAD
git status --short
git branch --show-current
pwd
```

### 2. Determine Scope
Get the current directory name to use as the scope:
```bash
basename "$(pwd)"
```

### 3. Branch Name (only if on `main` or `develop-*`)
**Format:** `<type>/<$dir-prefix>-<description>`

**Types:** `feature/` `fix/` `docs/` `refactor/` `test/` `chore/`

**Rules:**
- Lowercase with hyphens (e.g., `feature/auth-add-user-auth`)
- 3-5 words, concise
- Include directory name as prefix after the type (e.g., `feature/auth-`)
- Include issue# if applicable (e.g., `fix/api-issue-123-login-error`)

### 4. Commit Message Format
**Title (≤60 chars):**
- Imperative mood ("add" not "adds")
- Lowercase (except symbols/acronyms)
- Prefix with scope: `feat(scope):` `fix(scope):` `docs(scope):` `style(scope):` `refactor(scope):` `test(scope):` `chore(scope):`

**Body:**
- Explain *what* and *why*
- Imperative mood

### 5. Output Format

**On main/develop-* branch:**
```
## Recommended Branch
git checkout -b <type>/<scope>/<description>

## Commit Message
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

**On other branches:**
```
## Commit Message
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

### 6. Staging
```bash
git add <file>
# or use `git hunks` for specific changes
git commit -m "type(scope): title" -m "body"
```

## Examples

**If in `/projects/monorepo/packages/auth`:**
- Branch: `feature/auth-add-oauth-support`
- Commit: `feat(auth): add OAuth2 support for Google login`

**If in `/projects/monorepo/apps/web`:**
- Branch: `fix/web-resolve-hydration-error`
- Commit: `fix(web): resolve React hydration mismatch on SSR`
