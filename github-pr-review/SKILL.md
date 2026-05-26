---
name: github-pr-review
description: >
  Use this when asked to review a specific GitHub Pull Request and leave review comments on the PR itself.
  Trigger this skill when the user provides a PR number or URL, says casual review requests like "レビューして", "PRレビューして", or "このPR見て", or explicitly asks you to review and comment on a GitHub PR instead of only summarizing findings in chat. Also trigger when the user asks to recheck feedback previously posted by this skill.
---

# 概要

指定された GitHub Pull Request をレビューし、可能な限り差分上の適切な位置へレビューコメントを付けるためのスキル。
チャット上の総評ではなく、GitHub PR 上へ実際にコメントを残す運用を前提にする。

# 使用タイミング

- ユーザーが GitHub PR の URL または PR 番号を指定してレビューを依頼した時
- PR 文脈で「レビューして」「このPR見て」など短くレビューを依頼した時
- ユーザーが「GitHub 上にコメントしてほしい」と明示した時
- チャット要約だけでなく、PR へ inline comment を残すことが成果物として求められている時
- このスキルで指摘コメントを投稿した後、ユーザーが FB 対応完了後の再確認を依頼した時

# 前提と禁止事項

- GitHub 連携は `gh` CLI / `gh api` を優先し、GitHub コネクタには依存しない。
- レビュー開始前に `gh auth status` が成功することを確認する。
- レビュー投稿者が自分自身のアカウントになるため、PR を `APPROVE` しない。
- `gh pr review --approve`、`gh api` の `APPROVE` review event、その他 PR approval 相当の操作は絶対に実行しない。
- 外部書き込みが禁止された評価・dry-run・権限不足の環境では、取得や投稿を実行せず、実行予定手順、コメント候補、未実施理由を報告する。
- コメント本文はファイルまたは JSON 入力で渡し、バッククォート、`$()`、引用符、改行を含む Markdown をシェル引数へ直接埋め込まない。
- すべてのコメントに、AI エージェントによる投稿だと分かる識別用メタ情報を必ず入れる。
- 改行を含む本文は実改行で扱い、文字列としての `\n` を投稿しない。

# 入力と出力

## 入力

- PR 番号、PR URL、`owner/repo` と PR 番号、または現在ブランチに紐づく PR
- レビュー対象リポジトリのローカル checkout
- `gh` CLI が利用可能で、対象リポジトリへコメント権限のある認証が済んでいること
- 必要に応じてユーザーから指定される観点や除外範囲

## 出力

- GitHub PR 上の inline review comments
- 差分箇所に紐づけられない指摘がある場合のみ、代替としての overall review comment
- ユーザーへの簡潔な報告

# Agentが行うこと

1. 対象 PR とレビュー対象リポジトリを特定する。
2. PR の概要、差分、既存コメントを取得する。
3. 差分を読み、バグ・仕様逸脱・保守性低下・テスト不足を優先して指摘候補を作る。
4. 各指摘を原則として差分上の行へ inline comment として紐づける。
5. コメント文を簡潔に整え、重要度ラベルと AI 識別メタ情報を付ける。
6. 重複投稿を避けたうえで GitHub PR にコメントを投稿する。
7. 投稿結果と未解決事項をユーザーへ報告する。
8. ユーザーが再チェックを促した場合は、元の指摘が改善されたか確認する。

参照マップ:

- Step 3, コメント分類: `references/review-criteria.md`
- Step 5, 6, 本文フォーマット: `references/posting-rules.md`
- Step 6, API 例: `references/posting-api.md`
- Step 8, 再チェックと Resolve: `references/recheck.md`

# ステップの詳細

## 1. PR を特定する

- ユーザーが PR URL を渡した場合は URL から `owner/repo` と PR 番号を読み取る。
- ユーザーが PR 番号だけを渡した場合は、現在の git remote から対象リポジトリを推定する。
- ユーザーが PR URL や番号を渡していない場合は、現在ブランチ名から対象 PR を特定する。
  - `git branch --show-current` で現在ブランチを取得する。
  - `gh pr view "$BRANCH" --json number,url,title,headRefName,baseRefName` を試す。
  - 見つからない場合は `gh pr view --json number,url,title,headRefName,baseRefName` を試す。
- どちらでも対象 PR が特定できない場合のみ、レビュー対象 PR をユーザーへ確認する。

## 2. PR 情報を取得する

- `gh auth status` を実行し、認証と対象権限を確認する。
- `gh pr view --json title,body,url,baseRefName,headRefName,headRefOid,files` で PR の概要と変更ファイル一覧を確認する。
- `gh pr diff` で差分を取得する。
- `gh api` または `gh pr view --comments` を使い、既存の review comments と overall comments を確認する。
- 既存コメントに同じ論点がある場合は重複投稿しない。同じ入力条件・失敗モード・修正方針を扱う指摘は同一論点として扱う。

## 3. 差分をレビューする

- レビュー観点と重要度ラベルの詳細は `references/review-criteria.md` を読む。
- まず正しさ、仕様逸脱、セキュリティ、データ破壊、例外処理漏れを優先して確認する。
- 次に設計、一貫性、可読性、保守性、テスト不足を確認する。
- 問題がない箇所に無理にコメントしない。
- 「改善案はあるが任意」の論点より、「修正しないと不具合になる」論点を優先する。

## 4. コメント位置を決める

- 原則として、該当する差分行に対して inline comment を付ける。
- 各指摘は、可能な限り個別の差分箇所へコメントする。
- 直接その行に付けられない場合は、同じ hunk 内で最も近い差分行に付ける。
- ファイル全体への指摘、複数ファイルをまたぐ設計指摘、削除済み行や GitHub API 制約で差分箇所に付けられない指摘だけ overall review comment へ落とす。
- overall review comment は inline comment の代替手段であり、総評や要約のためには使わない。

## 5. コメント文を作る

- 投稿前に `references/posting-rules.md` を読み、コメント本文と AI エージェント識別メタ情報を整える。
- 1コメント1論点を守る。
- 何が問題か、なぜ問題か、必要ならどう直すかを短く書く。
- 投稿前に、コメント本文へ AI 識別メタ情報が入っていることと、文字列としての `\n` が残らないことを確認する。

## 6. コメントを投稿する

- 複数コメントがある場合は、可能なら pending review としてまとめて送信する。
- コメント投稿は `gh` CLI / `gh api` を使い、GitHub コネクタは使わない。
- inline review comment の投稿は、原則として `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews` を使う。
- review 作成 API で inline comment を送る場合は、`commit_id`、`body`、`event: "COMMENT"`、`comments[].path`、`comments[].side`、`comments[].line`、`comments[].body` を指定する。
- 具体的な payload 例と `jq` での作成例は `references/posting-api.md` を読む。
- `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments` は、返信や単発コメントなど自然な場合だけ使う。
- CLI や API の制約、または指摘の性質上 inline comment ができない場合のみ、overall review comment を使う。
- 投稿後は `gh api` または `gh pr view --comments` で、意図した本文が実際に投稿されていることを確認する。

## 7. ユーザーへ報告する

- 投稿したコメント件数を伝える。
- `[must]` がある場合は、その有無だけ簡潔に伝える。
- 権限不足、`gh` 未認証、差分取得失敗などで未実施部分があれば明記する。
- 対象 PR の URL または番号、投稿した指摘の要約を簡潔に残す。
- overall review comment を使った場合は、inline comment にできなかった理由を伝える。

## 8. FB対応後に再チェックする

- 詳細手順は `references/recheck.md` を読む。
- 直前または会話内でこのスキルが投稿したレビュー指摘だけを再チェック対象にする。
- 最新状態を確認するため、PR 情報と差分を再取得する。
- `pullRequest.reviewThreads` を取得し、前回投稿コメントと review thread ID / resolved 状態を対応付ける。
- `resolved` は返信して Resolve、`partial` / `unresolved` は該当スレッドへ追加コメント、`unknown` は理由を報告して Resolve しない。
- 再チェックコメントにも AI エージェント識別メタ情報を必ず付け、PR approval 相当の操作は実行しない。

# 品質チェック

- `description` を読むだけで、このスキルの起動条件がわかる
- PR 情報の取得、差分レビュー、コメント投稿、報告までの手順が上から順に実行できる
- GitHub の inline comment 制約に合わない指示が入っていない
- コメント重複の回避が手順に含まれている
- overall review comment は、差分箇所に紐づけられない指摘の代替に限定されている
- FB対応後の再チェックで、未改善の指摘へ再コメントし、改善済みの指摘へ返信して Resolve する手順が含まれている
- PR approval に相当する操作を決して実行しないルールが含まれている
- すべてのコメントに AI エージェント識別メタ情報を付けるルールが含まれている
- コメント本文の改行を実改行で扱い、文字列としての `\n` をそのまま投稿しないルールが含まれている
- Markdown コメント本文をシェル引数へ直接埋め込まず、ファイル参照または JSON 入力で渡すルールが含まれている
