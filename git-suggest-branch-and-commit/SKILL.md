---
name: git-suggest-branch-and-commit
description: Suggest branch name and commit message from staged changes (monorepo support)
---

## Purpose
Summarize **staged changes only** and suggest branch name + commit message.
**Never commit directly to `main`** — always use a feature branch.

## Usage
1. Analyze `git status` and `git diff --staged`
2. Review suggested branch/commit
3. Switch to suggested branch (create if needed)
4. Commit (verify not on `main`)

## Inputs
- `git status` (staged only)
- `git diff --staged`
- Git root: `git rev-parse --show-toplevel`
- Current dir: `pwd`
- (optional) User intent

## Outputs
- **Branch:** `prefix/short-slug`
- **Commit:** `prefix[(project)]: imperative message`
- Summary of staged changes

## Rules
- **No commits on `main`**
- Prefix: `feat` | `update` | `refactor`
- One logical change per commit
- Monorepo: include project scope in commit message
- Non-monorepo: omit project scope, use prefix only

## Project Detection
1. **From path:** Use last dir name in relative path from Git root
   - `packages/api` → `api`
   - `apps/web` → `web`
   - `libs/shared/utils` → `utils`

2. **From staged files:** Group by path segments if at Git root
   - `packages/api/src/index.ts` → `api`

3. **Fallback:** 
   - Check if monorepo (has `workspaces` in root `package.json`)
   - If monorepo: use `package.json` name or `root`
   - If non-monorepo: omit project scope (empty string)

## Examples

| Relative path | Monorepo Project | Non-monorepo Project |
|---------------|------------------|----------------------|
| `packages/api` | `api` | N/A |
| `apps/web` | `web` | N/A |
| `.` (root-level files) | `root` | (empty) |

**Commit format:**
- Monorepo: `feat(api): add user authentication`
- Non-monorepo: `feat: add user authentication`
- `update(web): upgrade dependencies`
- `refactor(utils): extract common logic`
