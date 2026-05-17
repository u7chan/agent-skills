---
name: github-pr-feedback-address
description: >
  Use this when asked to address feedback on an existing GitHub Pull Request, including casual requests like "PRのFBおねがい", "PRのコメントみて", "レビューコメント対応して", "FB対応して", or requests made after a PR has been opened and review comments are expected. Finds the current PR from the provided PR URL/number or current branch, inspects unresolved review feedback, implements fixes, validates, commits, pushes, and replies to the addressed feedback comments.
---

# 概要

GitHub PR に付いた review comments / conversation comments を確認し、指摘内容に沿ってコードを修正するためのスキル。
このスキルは実装対応、検証、コミット、push、対応した feedback コメントへの返信までを担当する。

# このスキルを使用するタイミング

- ユーザーが「PRのFBおねがい」「PRのコメントみて」「FB対応して」「レビューコメント対応して」と依頼した時
- PR 作成後の文脈で、指摘コメントやレビューコメントへの対応を求められた時
- PR URL や番号が明示されていなくても、現在ブランチに紐づく PR の feedback 対応が自然な時

# 入力と出力

## 入力

- PR 番号、PR URL、`owner/repo` と PR 番号、または現在ブランチに紐づく PR
- review comments、review threads、top-level PR comments
- 対象リポジトリのローカル checkout
- `gh` CLI が利用可能で、対象リポジトリへ read/write 権限のある認証が済んでいること

## 出力

- 指摘に対応するコード変更
- 必要な検証結果
- 対応コミットと push 済みブランチ
- 対応した feedback コメントへの返信
- ユーザーへの簡潔な報告
  - 対応した指摘
  - 対応しなかった指摘と理由
  - 実行した検証
  - 返信したコメント

# 前提

- GitHub 連携は `gh` CLI / `gh api` を優先して使い、GitHub コネクタには依存しない。コネクタと `gh` は認証主体や権限が異なるため、PR 取得や更新で 403 になることがある。
- 作業前に `gh auth status` を確認する。
- ユーザーの未コミット変更や無関係な変更を勝手に取り込まない。
- review thread の Resolve と Approve は行わない。
- 対応した feedback コメントには、対応内容や未対応理由が分かる返信を投稿する。
- PR approval に相当する操作は絶対に実行しない。

# Agentが行うこと

1. 対象 PR と現在ブランチを特定する。
2. 未対応の review feedback を収集する。
3. 対応対象を分類し、実装方針を決める。
4. コードを修正する。
5. 必要なテスト・lint・型チェックを実行する。
6. 変更を確認し、対応内容だけを commit する。
7. ブランチを push する。
8. 対応した feedback コメントへ返信する。
9. 対応結果を報告する。

# ステップの詳細

## 1. PR を特定する

- ユーザーが PR URL を渡した場合は URL から `owner/repo` と PR 番号を読み取る。
- ユーザーが PR 番号だけを渡した場合は、現在の git remote から対象リポジトリを推定する。
- PR URL や番号がない場合は、現在ブランチから対象 PR を特定する。
  - `git branch --show-current` で現在ブランチを取得する。
  - `gh pr view "$BRANCH" --json number,url,title,headRefName,baseRefName` を試す。
  - 見つからない場合は `gh pr view --json number,url,title,headRefName,baseRefName` を試す。
  - それでも特定できない場合のみ、対象 PR をユーザーへ確認する。

## 2. feedback を収集する

- `gh pr view --json number,url,title,body,headRefName,baseRefName,comments,reviews` で PR 概要とトップレベルコメントを確認する。
- review comments / review threads は `gh api graphql` または `gh api repos/{owner}/{repo}/pulls/{number}/comments` で取得する。
- 可能なら thread の resolved 状態を取得し、resolved 済みの指摘は原則対応対象から外す。
- 既存の最新差分を `gh pr diff` で確認し、コメントが現在のコードにまだ該当するかを見る。
- feedback は次のように分類する。
  - `actionable`: コードやテストの変更で対応できる
  - `question`: 仕様確認や意図説明が必要
  - `already-fixed`: 現在の差分では解消済み
  - `not-applicable`: 現在のコードに該当しない、または誤認
  - `blocked`: 情報不足や権限不足で対応できない

## 3. 対応方針を決める

- `actionable` を優先して実装する。
- `question`、`not-applicable`、`blocked` は勝手に仕様を決めず、必要ならユーザーに確認する。
- 小さな推測で安全に進められる場合のみ、理由を明確にして実装する。
- 複数指摘が衝突する場合は、先にユーザーへ確認する。
- 対応不要と判断した指摘は、最終報告に理由を残す。

## 4. コードを修正する

- 既存の設計、命名、テスト方針に合わせる。
- 指摘対応に必要な範囲だけを変更する。
- 無関係な整形、リファクタ、依存更新を混ぜない。
- ユーザーの未コミット変更が同じファイルにある場合は、差分を読んで壊さないように作業する。
- 変更対象が不明な場合は、先に `rg`、`git diff`、関連ファイルの読み取りで根拠を集める。

## 5. 検証する

- 変更範囲に応じて最小限かつ十分な検証を行う。
- 既存の test / lint / typecheck コマンドが分かる場合はそれを使う。
- 検証できなかった場合は理由を報告する。
- 失敗した場合はログを読み、指摘対応に関係する失敗なら修正する。無関係な既存失敗は区別して報告する。

## 6. commit する

- `git status --short` と `git diff` で変更範囲を確認する。
- このスキルで行った変更だけを stage する。
- 未追跡ファイルや無関係な変更を勝手に commit しない。
- commit message の生成には必ず `git-commit-message/SKILL.md` を使い、そのワークフローに従う。
- `git-commit-message` 側に `git add .` の例があっても、このスキルでは使わない。stage 対象は必ずこのスキルで行った変更だけに限定する。
- commit message は `git-commit-message` のルールに従い、feedback 対応であることが分かる Conventional Commits 形式にする。
- feedback 対応であることは `git-commit-message` の feedback 対応用 type で表し、scope は通常ルールに従って対象プロジェクトや対象スキルを入れる。
- コミット済みの変更が既にある場合は、必要に応じて新しい commit を追加する。既存 commit を勝手に amend / rebase しない。

## 7. push する

- 現在ブランチを push する。
- upstream がなければ `git push -u origin "$BRANCH"` を使う。
- push に失敗した場合は理由を報告し、勝手に force push しない。

## 8. feedback コメントへ返信する

- 対応した review comment には threaded reply を投稿する。
- 対応した top-level PR conversation comment には follow-up comment を投稿する。
- 返信本文には、対応内容、関連 commit、検証結果を簡潔に含める。
- 未対応、判断不能、質問が必要な feedback には、必要に応じて理由や確認事項を返信する。
- 返信対象と投稿方法は `github-pr-comment-reply/SKILL.md` の方針に従う。
- review thread の Resolve と Approve は行わない。

## 9. 報告する

- 対応した feedback を簡潔に列挙する。
- 未対応、判断不能、質問が必要な feedback があれば理由を添える。
- 実行した検証と結果を伝える。
- commit hash と PR URL を伝える。
- 返信したコメントを伝える。
- このスキル自身では review thread の Resolve と Approve を行わない。

# 品質チェック

- `description` を読むだけで、「PRのFBおねがい」「PRのコメントみて」で発火すべきことが分かる
- PR URL/番号がなくても現在ブランチから PR を特定する手順がある
- review feedback の収集、分類、実装、検証、commit、push、返信、報告までの流れがある
- 無関係な変更を commit しないルールがある
- 対応した feedback コメントへ返信するルールがある
- Resolve / Approve をこのスキルで行わないルールがある
- GitHub コネクタに依存せず `gh` / `gh api` の認証で進めるルールがある

# 参考資料

- `github-pr-review/SKILL.md`
- `github-pr-comment-reply/SKILL.md`
- `gh pr view`
- `gh pr diff`
- `gh api`
