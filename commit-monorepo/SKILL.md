---
name: commit-monorepo
description: Suggest commit messages and branch names for monorepo projects
---

## Workflow

### 1. Check Context

**IMPORTANT: Do NOT run any git commands yet.**

First, check if sufficient context is already available in the conversation (changed files, current branch, staged changes, or current directory).

**If context IS available:**
1. Show the branch name and draft commit message
2. Ask the user: "Is this information sufficient? If yes, I'll proceed."
3. Wait for user confirmation
4. If user responds with "OK" or confirmation, **output the final result**
5. If user needs more info (NOT "OK"), run these git commands:
   - `git diff HEAD`
   - `git status --short`
   - `pwd`

**Preview format:**
```
Context is available.
Branch: <branch-name>

Proposed commit message:
<type>(<scope>): <title>

Is this sufficient? Reply "OK" to confirm this commit message.
```

**If context is NOT available, run this git command:**
- `git branch --show-current`

### 2. Determine Scope
Get the current directory name to use as the scope:
```bash
basename "$(pwd)"
```

### 3. Branch Name (only if on `main` or `develop*`)
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

**On main/develop* branch:**
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

### 7. User Confirmation
If the user says "OK" after the suggestion, execute the following automatically:

**On main/develop* branch:**
```bash
git switch -c <type>/<$dir-prefix>-<description>
git add .  # only if files are not staged
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

**On other branches:**
```bash
git add .  # only if files are not staged
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

## Examples

**If in `/projects/monorepo/packages/auth`:**
- Branch: `feature/auth-add-oauth-support`
- Commit: `feat(auth): add OAuth2 support for Google login`

**If in `/projects/monorepo/apps/web`:**
- Branch: `fix/web-resolve-hydration-error`
- Commit: `fix(web): resolve React hydration mismatch on SSR`
