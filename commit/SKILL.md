---
name: commit
description: Suggest commit messages and branch names
---

## Workflow

### 1. Check Context

**IMPORTANT: Do NOT run any git commands yet.**

First, check if sufficient context is already available in the conversation (changed files, current branch, or staged changes).

**If context IS available:**
1. Show the branch name and draft commit message
2. Ask the user: "Is this information sufficient? If yes, I'll proceed."
3. Wait for user confirmation
4. If user responds with "OK" or confirmation, **output the final result**
5. If user needs more info (NOT "OK"), run these git commands:
   - `git diff HEAD`
   - `git status --short`

**Preview format:**
```
Context is available.
Branch: <branch-name>

Proposed commit message:
<type>: <title>

Is this sufficient? Reply "OK" to confirm this commit message.
```

**If context is NOT available, run this git command:**
- `git branch --show-current`

### 2. Branch Name (only if on `main` or `develop*`)
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

**On main/develop* branch:**
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
```

### 6. User Confirmation
If the user says "OK" after the suggestion, execute the following automatically:

**On main/develop* branch:**
```bash
git switch -c <type>/<description>
git add .  # only if files are not staged
git commit -m "<prefix>: <title>" -m "<body>"
```

**On other branches:**
```bash
git add .  # only if files are not staged
git commit -m "<prefix>: <title>" -m "<body>"
```
