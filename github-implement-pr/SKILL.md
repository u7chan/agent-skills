---
name: github-implement-pr
description: >
  Use this when the user asks to implement a GitHub Issue or implementation task
  and expects the agent to keep moving through branch creation, code changes,
  validation, commits, push, and pull request creation without delegating to
  other skills.
---

# 概要

GitHub Issue または実装指示を受け、作業ブランチ作成、実装、検証、コミット、push、PR 作成までを単体で進めるスキル。基本方針は「失敗時だけ停止」。ユーザー確認を細かく挟まず、完了まで進める。

# 使用タイミング

- ユーザーが GitHub Issue 番号や URL を示して「対応して」「実装して」と依頼した時
- ユーザーが実装、検証、コミット、PR 作成までまとめて任せたい時
- 作業開始から PR URL の提示までを一連のフローとして扱う時

# 基本方針

- 既存コード、Issue、会話から要求と完了条件を読み取り、探索で解決できる不明点は質問せず調べる。
- 目的、受け入れ条件、影響範囲が十分に分かる場合は、ユーザー確認なしでブランチ作成から PR 作成まで進める。
- `main`、`master`、`develop` では直接実装せず、必ず作業ブランチを作る。
- 無関係な未コミット変更は勝手に取り込まない。必要な変更だけを stage/commit する。
- 他のスキルへ委譲しない。このスキル内の手順だけで完結させる。
- PR 作成・本文更新は `gh` / `gh api` で行い、GitHub コネクタは使わない。コネクタは `gh` のユーザー認証と権限が異なるため、PR 更新で 403 になることがある。
- PR 本文、Issue 本文、コメント本文などの Markdown 長文は必ずファイル経由で渡す。バッククォートや `$()` を含む本文を `--body "..."` や `--field body="$(cat ...)"` へ直接埋め込まない。

# 停止条件

次の場合だけ停止して、短く状況と必要な判断をユーザーへ返す。

- 要求、完了条件、対象リポジトリ、対象 Issue が特定できない。
- 破壊的操作、履歴改変、無関係な変更の巻き込みが必要になる。
- 既存の作業ツリー変更が実装対象と衝突し、安全に分離できない。
- lint、test、build などの品質確認が失敗し、自力で修正できない。
- `gh` が未インストール、未認証、または権限不足。
- push や PR 作成が失敗し、原因が認証、権限、保護ルールなどユーザー側の対応を必要とする。

# ワークフロー

## 1. 依頼内容を確認する

- Issue がある場合は `gh issue view`、Issue URL、または提供された本文から、背景、受け入れ条件、関連コメントを確認する。
- Issue がない場合は、会話から目的、対象範囲、完了条件、検証観点を抽出する。
- 設計合意が必要なほど要求が曖昧な場合は停止する。自動で Issue 化しない。
- 実装前に `git status --short` を確認し、既存変更の有無と今回触ってよい範囲を把握する。

## 2. ベースブランチと作業ブランチを用意する

- 現在のブランチを `git branch --show-current` で確認する。
- ベースブランチを解決する前に `git fetch origin` を実行し、リモート状態を更新する。
- ベースブランチは `origin/HEAD` を優先し、取れない場合は `main`、`master`、`develop` の順で存在するものを使う。
- 保護対象ブランチ上にいる場合は、ベースブランチから作業ブランチを作る。
- 既に作業ブランチ上にいる場合は、再利用前に `git log <base>..HEAD`、upstream、既存 PR を確認する。
- 既存ブランチに今回の作業以外のコミットや別 PR の変更が含まれる場合は、ベースブランチから新しい作業ブランチを作る。
- 既存ブランチが今回の作業だけを含み、名前も適切な場合だけそのまま使う。
- ブランチ名は `<type>/<description>` を標準にする。Issue がある場合は `issue-123` を含める。
- `type` は `feature`、`fix`、`docs`、`refactor`、`test`、`chore` から選ぶ。
- 説明部分は英小文字とハイフンで 3〜5 語にする。

例:

```bash
git switch -c fix/issue-123-login-error
```

## 3. 実装する

- まず関連ファイル、設定、テストを読み、既存パターンに合わせて変更する。
- 変更は Issue や指示の範囲に絞る。ついでのリファクタや関係ない整形は避ける。
- 小さな変更は 1 ステップで完了させる。複数領域にまたがる場合は、個別に検証しやすい単位で進める。
- ユーザーが明示していない限り、生成物やロックファイルは必要な場合だけ更新する。

## 4. 品質確認する

- リポジトリの設定から利用可能な formatter、lint、test、build を確認する。
- 変更範囲に対して最小十分なチェックを実行する。共有処理や公開 API に触れた場合は広めに確認する。
- 失敗したチェックは原因を調べて修正し、再実行する。
- 最終報告と PR 本文に、実行したコマンドと結果を含める。

## 5. コミットする

- `git diff` と `git status --short` を確認し、今回の変更だけを stage する。
- コミットは原則 1 つ。独立してレビューできる大きな変更だけ複数コミットにする。
- コミットメッセージは英語の Conventional Commits 形式にする。
- タイトルは 60 文字以内を目安にし、本文には何を変えたか、なぜ必要かを簡潔に書く。

例:

```bash
git commit -m "fix: handle missing login redirect" -m "Update the login flow to keep redirects stable when the callback query is absent."
```

## 6. push して PR を作成する

- `gh auth status` で認証状態を確認する。
- `BASE..HEAD` に PR 対象コミットがあることを確認する。
- リモートに現在のブランチがなければ `git push -u origin <branch>` を実行する。既にあれば通常の `git push` を実行する。
- PR タイトルはコミットまたは Issue 内容から短く具体的に作る。
- PR 本文は次の構造を基本にする。Issue がない場合は `Issues` を省略する。

```markdown
## Issues

- Close #123

## Why

変更が必要な背景。

## Summary

この PR で行った変更の要約。

## Changes

- 変更点 1
- 変更点 2

## Verification

- `command` - passed
```

- Issue を閉じる意図が明確なら `Close #123`、関連付けのみなら `Refs #123` を使う。
- Markdown 本文は一時ファイルに書き、`gh pr create --body-file` で渡す。`gh pr create --body "..."` は使わない。
- PR 本文を作成後に直す必要がある場合は、同じ本文ファイルを使って `gh pr edit --body-file "$FILE"` を試す。`gh pr edit` が GraphQL の Projects classic など本文更新以外の取得エラーで失敗した場合は、`gh api repos/<owner>/<repo>/pulls/<number> --method PATCH --field body=@"$FILE"` に切り替える。
- 作成後に `gh pr view --json title,body,url` で結果を確認し、PR URL を最終報告に含める。

# 最終報告

- 変更概要、実行した検証、作成した PR URL を簡潔に返す。
- 失敗や未解決事項がある場合は、原因、現在の状態、次に必要な判断を明記する。

# 品質チェック

- [ ] 他スキルへの委譲や参照なしで、Issue 確認から PR 作成まで完結する
- [ ] 失敗時だけ停止する方針が明記されている
- [ ] ブランチ名、コミットメッセージ、PR 本文の生成規則が明記されている
- [ ] `main`、`master`、`develop` への直接実装と直接 push を避ける
- [ ] 無関係な変更を stage/commit しない
- [ ] PR 本文は `--body-file`、本文更新は `--body-file` または `gh api --field body=@file` で安全に渡す
