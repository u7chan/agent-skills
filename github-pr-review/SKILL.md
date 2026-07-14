---
name: github-pr-review
description: >
  指定されたGitHub PRのレビューや再チェックを行い、PR上へコメントするときに使う。
  PR URL・番号の指定や、「レビューして」「PRレビューして」「このPR見て」など、GitHubへの投稿を求める依頼で起動する。
---

# 概要

GitHub Pull Request をレビューし、根拠のある指摘を可能な限り差分行へ投稿する。
指摘がない場合も、PR approval ではない `COMMENT` review を残す。

# 実行ルール

- 取得、投稿、再チェックは `gh` CLI / `gh api` で行い、GitHub コネクタは使わない。
- 最初に `gh auth status` を確認する。
- レビュー依頼を、review comment の投稿、再チェック時の返信、改善済み thread の Resolve までの許可として扱う。投稿前確認は挟まない。
- 自分のアカウントから投稿するため、`APPROVE` review や同等の操作は実行しない。
- 外部書き込み禁止、権限不足、対象不明の場合は投稿せず、確認できた範囲の指摘候補と未投稿理由を報告する。
- Markdown 本文はファイルまたは JSON で渡し、シェル引数へ直接埋め込まない。
- ユーザーの未コミット変更を上書きしない。
- AI識別に関する上位のsystem、user、`AGENTS.md`指示がある場合は、その指示に従う。該当する上位指示がなくても、利用先リポジトリの `AGENTS.md` を前提にせず、本スキルの標準契約として投稿直前に `ai-identity-resolve` を必ず読み、適用する。

# ワークフロー

1. 対象 PR を特定する。
2. PR の説明、差分、関連コード、テスト、既存コメントを取得する。
3. 指摘候補を作り、投稿可能な根拠があるか検証する。
4. 重複を除き、重要度とコメント位置を決める。
5. コメント本文を整え、GitHub へ投稿する。
6. 投稿結果を確認し、ユーザーへ報告する。
7. 再チェック依頼では、以前に投稿した指摘の失敗条件が解消したか検証する。

参照先:

- Step 3, 4: `references/review-criteria.md`
- Step 5: `references/posting-rules.md`
- Step 5 の API payload: `references/posting-api.md`
- Step 7: `references/recheck.md`

# 手順

## 1. PR とレビュー範囲を特定する

- PR URL があれば `owner/repo` と PR 番号を読み取る。
- PR 番号だけなら現在の remote からリポジトリを推定する。
- 指定がなければ、現在ブランチに対して `gh pr view "$BRANCH"`、次に `gh pr view` を試す。
- ユーザー指定の観点や除外範囲があれば、通常のレビュー観点へ追加する。

## 2. 根拠を収集する

- `gh pr view --json title,body,url,baseRefName,headRefName,headRefOid,files` と `gh pr diff` を取得する。
- 差分だけで判断せず、変更箇所の呼び出し元、型、設定、既存テスト、プロジェクト規約を必要な範囲で読む。
- review comments と overall comments を取得する。
- 同じ入力条件、失敗モード、影響、修正方針を扱う既存指摘は重複として除外する。

## 3. 指摘候補を検証する

- `references/review-criteria.md` の品質ゲートを通過した候補だけ投稿対象にする。
- 正しさ、仕様逸脱、セキュリティ、データ破壊、例外経路を優先する。
- 次に、設計、一貫性、保守性、テスト不足を確認する。
- PR が導入または悪化させていない既存問題は、原則として指摘しない。
- 根拠が不足する場合は断定せず、確認が必要なら `[ask]`、好みなら `[imo]` とする。
- 問題がない箇所へコメントを作らない。

## 4. コメント位置を決める

- 原因または修正対象に最も近い差分行へ inline comment を付ける。
- 直接付けられない場合は同じ hunk 内の最も近い差分行を使う。
- 複数ファイルにまたがる問題、削除済み行、API 制約で紐づけられない問題だけ overall comment にする。
- overall comment を総評や差分要約には使わない。

## 5. コメントを投稿する

- PR 本文、次にタイトルの言語へ合わせ、判別できなければ日本語を使う。
- `references/posting-rules.md` に従い、各コメントへ重要度ラベルを付ける。
- 投稿本文と payload を確定して API へ渡す直前に `ai-identity-resolve` を必ず適用し、その時点の AI 識別メタ情報を各コメントへ付ける。会話開始時や過去に取得した識別値を再利用しない。
- 複数の inline comment は、可能なら `event: "COMMENT"` の review にまとめる。
- 投稿 API と payload は `references/posting-api.md` を使う。
- 指摘がない場合は inline comment を作らず、指摘なしの `COMMENT` review を投稿する。
- 投稿後に本文、コメント位置、メタ情報、改行が正しいことを再取得して確認する。

## 6. 報告する

- PR URL、投稿件数、`[must]` の有無を簡潔に伝える。
- 指摘がない場合は、指摘なしの review comment を投稿したと伝える。
- 投稿できなかった項目や overall comment へ回した指摘があれば理由を添える。

## 7. 再チェックする

- `references/recheck.md` を読み、この会話で以前に投稿した未解決指摘だけを対象にする。
- 最新差分と review threads を再取得する。
- 元コメントが示した失敗条件ごとに `resolved`、`partial`、`unresolved`、`unknown` を判定する。
- 改善済みなら返信して Resolve し、未改善なら同じ thread へ残存条件を返信する。
- 判断材料が不足する場合は Resolve しない。

# 完了条件

- 投稿した各指摘が、差分上の根拠、発生条件、因果、影響を説明できる。
- 重要度が確度と影響に合い、事実、推定、質問、好みを混同していない。
- 重複投稿、PR approval、メタ情報欠落、リテラル `\n` がない。
- 再チェックではコード変更の有無ではなく、元の失敗条件の解消を確認している。
