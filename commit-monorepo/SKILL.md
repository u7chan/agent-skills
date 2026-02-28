---
name: commit-monorepo
description: Suggest commit messages for monorepo projects
---

## Workflow

### 1. Check Current Branch

Run this git command to check the current branch:
- `git branch --show-current`

### 2. Determine Scope

Get the current directory name to use as the scope:
```bash
basename "$(pwd)"
```

### 3. Commit Message Format

**Title (≤60 chars):**
- Imperative mood ("add" not "adds")
- Lowercase (except symbols/acronyms)
- Prefix with scope: `feat(scope):` `fix(scope):` `docs(scope):` `style(scope):` `refactor(scope):` `test(scope):` `chore(scope):`

**Body:**
- Explain *what* and *why*
- Imperative mood

### 4. Output Format

```
## Commit Message

git commit -m "<type>(<scope>): <title>" -m "<body>"
```

### 5. Staging

```bash
git add <file>
# or use `git hunks` for specific changes
git commit -m "type(scope): title" -m "body"
```

### 6. User Confirmation

If the user says "OK" after the suggestion, execute the following automatically:

```bash
git add .  # only if files are not staged
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

## Examples

**If in `/projects/monorepo/packages/auth`:**
- Commit: `feat(auth): add OAuth2 support for Google login`

**If in `/projects/monorepo/apps/web`:**
- Commit: `fix(web): resolve React hydration mismatch on SSR`
