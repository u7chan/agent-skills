---
name: github-pr-feedback-address
description: >
  Use this when asked to address feedback on an existing GitHub Pull Request, including casual requests like "PRのFBおねがい", "PRのコメントみて", "レビューコメント対応して", "FB対応して", or requests made after a PR has been opened and review comments are expected. Finds the current PR from the provided PR URL/number or current branch, inspects unresolved review feedback, implements fixes, validates, commits, pushes, and replies to the addressed feedback comments.
---

# 概要

GitHub PR の未解決 feedback を検証し、必要なコード変更、テスト、commit、push、コメント返信まで行う。
reviewer の指摘をそのまま仕様とみなさず、現在のコードと既存仕様に照らして対応を決める。

# 実行ルール

- GitHub 操作は `gh` CLI / `gh api` を使い、最初に `gh auth status` を確認する。
- FB 対応依頼を、対応後のコメント返信までの許可として扱い、投稿前確認は挟まない。
- review thread の Resolve と PR approval は実行しない。
- ユーザーの未コミット変更、無関係な変更、既存 commit を壊さない。
- 指摘対応に必要な変更だけを行い、無関係な整形、リファクタ、依存更新を混ぜない。
- 指摘同士が衝突する、または仕様決定が必要な場合だけユーザーへ確認する。

# ワークフロー

1. 対象 PR と現在ブランチを特定する。
2. 未解決 feedback と最新差分を取得する。
3. 各 feedback の主張と根拠を検証し、対応を分類する。
4. `actionable` な指摘だけ実装する。
5. 変更範囲に対応する検証を実行する。
6. この作業の変更だけを commit して push する。
7. 各 feedback へ、対応結果または未対応理由を返信する。
8. 実装、検証、commit、返信結果を報告する。

# 手順

## 1. PR を特定する

- PR URL があれば `owner/repo` と PR 番号を読み取る。
- PR 番号だけなら現在の remote からリポジトリを推定する。
- 指定がなければ、現在ブランチに対して `gh pr view "$BRANCH"`、次に `gh pr view` を試す。
- 特定できない場合だけユーザーへ確認する。

## 2. feedback を収集する

- `gh pr view --json number,url,title,body,headRefName,baseRefName,comments,reviews` で概要を取得する。
- GraphQL または pull request comments API で review threads と resolved 状態を取得する。
- resolved 済みの指摘を原則として対象外にする。
- `gh pr diff` と現在のコードを読み、コメントが最新状態にも該当するか確認する。

## 3. 指摘を検証して分類する

各 feedback から、主張、想定する発生条件、問題となる挙動、要求された変更を分けて読む。
次の分類を使う。

- `actionable`: 現在のコードで問題を確認でき、コードまたはテスト変更で対応できる。
- `question`: 仕様、意図、実行時条件の確認が必要。
- `already-fixed`: 最新状態では、元の失敗条件が既に解消している。
- `not-applicable`: 前提が現行コードや仕様と一致せず、指摘した挙動が起きない。
- `blocked`: 情報、権限、環境が不足して判断または実装できない。

分類時は次を守る。

- reviewer の推定を未確認のまま事実や仕様として採用しない。
- ガード、呼び出し元、型、設定、フレームワーク仕様、既存テストによる反証を確認する。
- 複数の原因や要求が一つのコメントに含まれる場合は、個別に判定する。
- 小さな推測で進める場合も、仮定と影響範囲を明確にできる場合に限る。
- コード変更が不要なら、根拠を示した返信だけで完了してよい。

## 4. 実装する

- `actionable` の発生条件を閉じる最小の変更を行う。
- 症状だけを隠さず、指摘された挙動を生む原因を修正する。
- 既存の設計、命名、エラー処理、テスト方針へ合わせる。
- feedback の要求より狭い変更で問題を解消できる場合は、狭い変更を選ぶ。

## 5. 検証する

- 元の失敗条件を再現または防止できるテストを優先する。
- 変更範囲に応じて test、lint、typecheck を実行する。
- 検証不能なら理由を記録する。
- 失敗が今回の変更に関係するかを切り分け、無関係な既存失敗と混同しない。

## 6. commit と push を行う

- `git status --short` と `git diff` で変更範囲を確認する。
- この作業の変更だけを stage する。`git add .` は使わない。
- commit message は `git-commit-message/SKILL.md` を使い、feedback 対応用 type に従う。
- 既存 commit を勝手に amend / rebase しない。
- 現在ブランチを push し、upstream がなければ設定する。force push はしない。

## 7. feedback へ返信する

- review comment には threaded reply、top-level comment には follow-up comment を投稿する。
- 投稿方法は `github-pr-comment-reply/SKILL.md` に従う。
- `actionable` には、変更内容、元の失敗条件をどう閉じたか、commit、検証結果を書く。
- `already-fixed` / `not-applicable` には、判断根拠となる現在のコードや仕様を書く。
- `question` / `blocked` には、確定に必要な情報を具体的に書く。
- 一部だけ対応した場合は「対応済み」と言い切らず、残っている条件を明記する。
- 「修正しました」だけの返信や、変更内容の重複要約を避ける。
- 返信後も thread は Resolve しない。

## 8. 報告する

- 対応、未対応、判断不能の feedback と理由を簡潔に列挙する。
- 実行した検証、commit hash、PR URL、返信先を伝える。
- push または返信に失敗した場合は、失敗箇所と理由を伝える。

# 完了条件

- 各 feedback の前提を検証し、未確認の推定を仕様として実装していない。
- 変更が元の失敗条件を閉じ、対応範囲外の変更を含まない。
- 検証、commit、push、必要な返信が完了している。
- Resolve と PR approval を実行していない。
