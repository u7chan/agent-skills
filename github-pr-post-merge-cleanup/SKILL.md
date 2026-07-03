---
name: github-pr-post-merge-cleanup
description: GitHub PRをユーザーがマージした後、PRのbase branchへ戻り、最新化してローカルの作業ブランチを削除するときに使う。「マージ後の片付け」「基準ブランチに戻して」「次の開発に備えてブランチを整理して」などの依頼が対象。PRのマージ操作やremote branchの削除は行わない。
---

# GitHub PR Post-Merge Cleanup

マージ済みPRの作業環境を片付け、次の開発を始められる状態に戻す。

## 原則

- PRのマージは行わない。ユーザーがGitHub上でマージした後にだけ実行する。
- 現在のローカルブランチに紐づくPRを対象にする。会話にPR番号があれば同じPRか照合する。
- PRのbase branchは`main`または`develop`だけを許可する。それ以外なら停止する。
- 削除対象は対象PRのローカルhead branchだけに限定する。
- remote branch、他のローカルブランチ、worktree、stashは変更しない。
- 未コミット変更または未追跡ファイルがあれば停止する。自動stashしない。

## 手順

1. `gh auth status`で認証を確認する。
2. `git status --porcelain`が空であることを確認する。空でなければ何も変更せず停止する。
3. `git branch --show-current`で現在ブランチを取得する。空、`main`、`develop`なら停止する。
4. 現在ブランチに紐づくPRを`gh pr view`で取得する。会話にPR番号またはURLがあれば、そのPRを取得して現在ブランチとの一致を検証する。
5. PRについて次をすべて確認する。一つでも満たさなければ停止する。
   - `state`が`MERGED`
   - `mergedAt`が空でない
   - `headRefName`が現在ブランチ名と一致する
   - `baseRefName`が`main`または`develop`
6. `git switch <baseRefName>`で基準ブランチへ切り替える。失敗時は停止する。
7. `git pull --ff-only origin <baseRefName>`で最新化する。fast-forwardできなければ、自動mergeやrebaseをせず停止する。
8. PRがマージ済みでhead branchも一致したという手順5の結果を再利用し、`git branch -D <headRefName>`でローカル作業ブランチを削除する。pull失敗時は削除しない。
9. 現在ブランチ、最新コミット、削除したブランチを報告する。

## 確認コマンド例

```bash
gh auth status
git status --porcelain
git branch --show-current
gh pr view <branch-or-pr> --json number,url,state,mergedAt,baseRefName,headRefName
git switch <baseRefName>
git pull --ff-only origin <baseRefName>
git branch -D <headRefName>
git status --short --branch
git log -1 --oneline
```

## 停止時の扱い

- 停止理由と、ユーザーが解消すべき状態を簡潔に示す。
- 基準ブランチへの切り替え後にpullが失敗した場合、元の作業ブランチは削除せず残す。
- `git branch -D`は、GitHub上のマージ済み状態と現在ブランチとの一致を確認できた場合だけ使う。squash mergeやrebase mergeでは`git branch -d`がマージ済みと判定しないため、この条件下では強制削除を許可する。
