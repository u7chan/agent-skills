---
name: github-pr-review
description: >
  Use this when asked to review a specific GitHub Pull Request and leave review comments on the PR itself.
  Trigger this skill when the user provides a PR number or URL, says casual review requests like "レビューして", "PRレビューして", or "このPR見て", or explicitly asks you to review and comment on a GitHub PR instead of only summarizing findings in chat. Also trigger when the user asks to recheck feedback previously posted by this skill.
---

# 概要

指定された GitHub Pull Request をレビューし、可能な限り差分上の適切な位置にレビューコメントを付けるためのスキル。
チャット上の総評ではなく、GitHub PR 上へ実際にコメントを残す運用を前提にする。

# このスキルを使用するタイミング

- ユーザーが GitHub PR の URL または PR 番号を指定してレビューを依頼した時
- PR 文脈で、ユーザーが「レビューして」「このPR見て」など短くレビューを依頼した時
- ユーザーが「GitHub 上にコメントしてほしい」と明示した時
- チャット要約だけでなく、PR へ inline comment を残すことが成果物として求められている時
- このスキルで指摘コメントを投稿した後、ユーザーが FB 対応完了後の再確認を依頼した時

# 入力と出力

## 入力

- PR 番号、PR URL、`owner/repo` と PR 番号、または現在ブランチに紐づく PR
- レビュー対象リポジトリのローカル checkout
- `gh` CLI が利用可能で、対象リポジトリへコメント権限のある認証が済んでいること
- 必要に応じてユーザーから指定される観点や除外範囲

## 前提

- GitHub 連携は `gh` CLI / `gh api` を優先して使い、GitHub コネクタには依存しない。コネクタと `gh` は認証主体や権限が異なるため、コメント投稿や PR 更新で 403 になることがある
- レビュー開始前に `gh auth status` が成功することを確認する
- レビュー投稿者が自分自身のアカウントになるため、PR を `APPROVE` しない。`gh pr review --approve` や review event `APPROVE` は決して実行しない
- 外部書き込みが禁止された評価・dry-run・権限不足の環境では、取得や投稿を実行せず、実行予定手順、コメント候補、未実施理由を報告する

## 出力

- GitHub PR 上の inline review comments
- 差分箇所に紐づけられない指摘がある場合のみ、代替としての overall review comment
- ユーザーへの簡潔な報告
  - 何件コメントしたか
  - 重大な指摘があるか
  - 実行できなかった操作があるか
- 各コメントに、AI エージェントが投稿したと識別できるメタ情報

# Agentが行うこと

1. 対象 PR とレビュー対象リポジトリを特定する。
2. PR の概要、差分、既存コメントを取得する。
3. 差分を読み、バグ・仕様逸脱・保守性低下・テスト不足を優先して指摘候補を作る。
4. 各指摘を原則として差分上の行へ inline comment として紐づける。
5. コメント文を簡潔に整え、重要度ラベルを付ける。
6. 重複投稿を避けたうえで GitHub PR にコメントを投稿する。
7. 投稿結果と未解決事項をユーザーへ報告する。
8. ユーザーが再チェックを促した場合は、元の指摘が改善されたか確認する。

参照マップ:

- Step 3, コメント分類: `references/review-criteria.md`
- Step 5, 6: `references/posting-rules.md`
- Step 8: `references/recheck.md`

# ステップの詳細

## 1. PR を特定する

- ユーザーが PR URL を渡した場合は URL から `owner/repo` と PR 番号を読み取る。
- ユーザーが PR 番号だけを渡した場合は、現在の git remote から対象リポジトリを推定する。
- ユーザーが PR URL や番号を渡していない場合は、現在ブランチ名から対象 PR を特定する。
  - `git branch --show-current` で現在ブランチを取得する。
  - `gh pr view "$BRANCH" --json number,url,title,headRefName,baseRefName` を試す。
  - ブランチ名指定で見つからない場合は `gh pr view --json number,url,title,headRefName,baseRefName` を試し、現在 checkout 中のブランチに紐づく PR を取得する。
  - どちらでも対象 PR が特定できない場合のみ、レビュー対象 PR をユーザーへ確認する。
- 対象が曖昧な場合のみ、レビュー対象 PR をユーザーへ確認する。

## 2. PR 情報を取得する

- 最初に `gh auth status` を実行し、認証と対象権限を確認する。
- `gh pr view --json title,body,url,baseRefName,headRefName,files` で PR のタイトル、説明、base/head、変更ファイル一覧を確認する。
- `gh pr diff` で差分を取得する。
- `gh api` または `gh pr view --comments` を使い、既存の review comments と overall comments を確認する。
- 既存コメントに同じ論点がある場合は重複投稿しない。同じ論点とは、同じファイルや近接行でなくても、同じ入力条件・失敗モード・修正方針を扱っている指摘を指す。表現だけ違う同趣旨の指摘は重複として扱う。

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
- ファイル全体への指摘、複数ファイルをまたぐ設計指摘、削除済み行や GitHub API 制約で差分箇所に付けられない指摘だけ、overall review comment へ落とす。
- overall review comment は inline comment の代替手段であり、総評や要約のためには使わない。
- GitHub のレビューコメントは差分に紐づくため、変更されていないファイル先頭へのコメントを前提にしない。

## 5. コメント文を作る

- 投稿前に `references/posting-rules.md` を読み、コメント本文と AI エージェント識別メタ情報を整える。
- 1コメント1論点を守る。
- 何が問題か、なぜ問題か、必要ならどう直すかを短く書く。
- すべてのコメントに、AI エージェントによる投稿だと分かる識別用メタ情報を必ず入れる。
- 改行を含む本文は、文字列としての `\n` を埋め込まず、GitHub 上でそのまま複数行表示される実改行のテキストとして組み立てる。

## 6. コメントを投稿する

- 複数コメントがある場合は、可能なら pending review としてまとめて送信する。
- コメント投稿は `gh` CLI / `gh api` を使って行い、GitHub コネクタは使わない。
- inline review comment の投稿は、原則として `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews` を使う。`event: "COMMENT"` と `comments` 配列を指定すると、各コメントでファイル内の行番号を使える。
- `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments` は通常のレビュー投稿では避ける。この単一レビューコメント作成 API でも `commit_id` / `path` / `line` / `side` / `body` を使って投稿できるが、複数コメントを 1 つの review としてまとめにくく、通知もコメントごとに飛びやすい。返信や単発コメントなど、この endpoint が自然な場合だけ使う。
- review 作成 API で inline comment を送る場合は、少なくとも次を指定する。
  - `commit_id`: 対象 PR の head commit SHA
  - `body`: review 全体の本文。`event: "COMMENT"` では必須
  - `event`: `"COMMENT"`
  - `comments[].path`: 対象ファイルのリポジトリ相対パス
  - `comments[].side`: 変更後行なら `"RIGHT"`、変更前行なら `"LEFT"`
  - `comments[].line`: ファイル内の絶対行番号
  - `comments[].body`: コメント本文
- 具体例:

```bash
HEAD_COMMIT_SHA=$(gh pr view "$PR_NUMBER" --json headRefOid --jq .headRefOid)

jq -n \
  --arg commit_id "$HEAD_COMMIT_SHA" \
  --rawfile comment_body review-comment.md \
  '{
    commit_id: $commit_id,
    body: "AIレビュー補助（Codex / GPT-5）によるレビューです。",
    event: "COMMENT",
    comments: [
      {
        path: "src/example.ts",
        side: "RIGHT",
        line: 42,
        body: $comment_body
      }
    ]
  }' > review-payload.json

gh api \
  --method POST \
  "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" \
  --input review-payload.json
```

`review-comment.md` の例:

```markdown
[must] 問題の要約

なぜ問題になるかを短く説明します。

必要なら修正案を書きます。

AIレビュー補助（Codex / GPT-5）によるコメントです
```

生成される JSON payload の形:

```json
{
  "commit_id": "HEAD_COMMIT_SHA",
  "body": "AIレビュー補助（Codex / GPT-5）によるレビューです。",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/example.ts",
      "side": "RIGHT",
      "line": 42,
      "body": "[must] 問題の要約\n\nなぜ問題になるかを短く説明します。\n\n必要なら修正案を書きます。\n\nAIレビュー補助（Codex / GPT-5）によるコメントです\n"
    }
  ]
}
```

- JSON payload は一時ファイルとして作成し、`gh api --input review-payload.json` で渡す。複数行の Markdown コメント本文は別ファイルから読み込んで JSON を生成する。JSON 内では改行が `\n` として表現されるが、GitHub 上のコメント本文は実改行として表示される。本文にバッククォート、`$()`、引用符、改行が含まれるため、JSON や Markdown コメント本文をシェル引数へ直接埋め込まない。
- 投稿前に、同一内容の既存コメントがないことを再確認する。
- 投稿前に、すべてのコメント本文へ AI エージェント識別メタ情報が入っていることを確認する。
- 投稿前に、コメント本文の元ファイルや GitHub 上の表示に、文字列としての `\n` が残らないことを確認する。JSON payload 内のエスケープ表現としての `\n` は問題ない。
- 複数行コメントや Markdown コメントは、一時ファイル、JSON ファイル、または `gh api --field body=@file` のようなファイル参照で渡す。バッククォート、`$()`、引用符、改行を含む本文をシェル引数へ直接埋め込まない。
- `gh pr review` が GraphQL の Projects classic などコメント投稿以外の取得エラーで失敗した場合は、可能な範囲で `gh api` の REST / GraphQL 呼び出しへ切り替える。
- CLI や API の制約、または指摘の性質上 inline comment ができない場合のみ、overall review comment を使う。
- overall review comment を使う場合は、どの指摘が inline comment にできなかったか分かる本文にする。
- 投稿後は `gh api` または `gh pr view --comments` で、意図した本文が実際に投稿されていることを確認する。

## 7. ユーザーへ報告する

- 投稿したコメント件数を伝える。
- `[must]` がある場合は、その有無だけ簡潔に伝える。
- 権限不足、`gh` 未認証、差分取得失敗などで未実施部分があれば明記する。
- 対象 PR の URL または番号、投稿した指摘の要約を簡潔に残す。
- overall review comment を使った場合は、inline comment にできなかった理由を伝える。
- この報告では、ユーザーに PR URL や番号の再入力を求めない。次の再チェックで文脈から対象 PR を引き継ぐ。

## 8. FB対応後に再チェックする

- 詳細手順は `references/recheck.md` を読む。
- 直前または会話内でこのスキルが投稿したレビュー指摘だけを再チェック対象にする。
- ユーザーが再チェックを依頼した場合は、FB対応が完了した合図として扱う。
- 対象 PR は、会話内に残した PR URL/番号を優先し、なければ現在ブランチ名から特定する。
- 最新状態を確認するため、`gh pr view --json number,url,title,headRefName,baseRefName,commits` と `gh pr diff` を再取得する。
- 返信・Resolve の対象を特定するため、`gh api graphql` で `pullRequest.reviewThreads` を取得し、各 thread の `id`、`isResolved`、コメントの `databaseId`、`body`、`path`、`url`、`author` を確認する。
- 前回このスキルが投稿した指摘だけを review thread と対応付ける。対応付けの優先順は `references/recheck.md` に従う。
- 既に `isResolved: true` の thread は原則として再コメントや Resolve 対象から外し、未解決 thread だけを再チェック対象にする。
- 必要に応じて `git fetch` し、ローカル checkout が古い場合はその旨を報告する。ユーザーの未コミット変更を勝手に上書きしない。
- 各指摘について、次のどれかに分類する。
  - `resolved`: 指摘内容が改善されている
  - `partial`: 一部改善されたが、まだ問題が残っている
  - `unresolved`: 改善されていない、または別の問題として残っている
  - `unknown`: 差分や権限の都合で判断できない
- `unknown` は、前回コメントや thread は特定できるが、最新差分・現在のファイル内容・取得権限のいずれかが不足し、修正有無を根拠付きで判断できない場合にだけ使う。`unknown` は Resolve しない。
- `resolved` は返信して Resolve、`partial` / `unresolved` は該当スレッドへ追加コメント、`unknown` は理由を報告して Resolve しない。
- 追加コメントや完了コメントを投稿する場合は、重複を避け、改善済みの指摘へ不要な再指摘をしない。
- 再チェックコメントにも AI エージェント識別メタ情報を必ず付け、`references/posting-rules.md` の再チェック用フォーマットに従う。
- `gh pr review --approve`、`gh api` での `APPROVE` review event、その他 PR approval に相当する操作は絶対に実行しない。自分自身のレビューは Approve できずエラーになるため、完了通知は reply / resolve / overall comment で行う。
- 最終報告では、再コメントした件数、Resolve した件数、overall comment で代替した件数、未解決の有無を簡潔に伝える。

# 品質チェック

- `description` を読むだけで、このスキルの起動条件がわかる
- PR 情報の取得、差分レビュー、コメント投稿、報告までの手順が上から順に実行できる
- GitHub の inline comment 制約に合わない指示が入っていない
- コメント重複の回避が手順に含まれている
- 総評だけで終わらず、差分上の inline comment を基本成果物として明記されている
- overall review comment は、差分箇所に紐づけられない指摘の代替に限定されている
- FB対応後の再チェックで、未改善の指摘へ再コメントし、改善済みの指摘へ返信して Resolve する手順が含まれている
- 再チェック時に `pullRequest.reviewThreads` を取得し、前回投稿コメントと review thread ID / resolved 状態を対応付ける手順が含まれている
- 返信や Resolve ができない場合、overall comment で完了状態を伝える手順が含まれている
- PR approval に相当する操作を決して実行しないルールが含まれている
- すべてのコメントに AI エージェント識別メタ情報を付けるルールが含まれている
- コメント本文の改行を実改行で扱い、`\\n` をそのまま投稿しないルールが含まれている
- Markdown コメント本文をシェル引数へ直接埋め込まず、ファイル参照または JSON 入力で渡すルールが含まれている

# 参考資料

- `gh pr view`
- `gh pr diff`
- `gh api`
- `references/review-criteria.md`
- `references/posting-rules.md`
- `references/recheck.md`
