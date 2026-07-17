# Posting API Examples

## Review 作成 API

inline review comment の投稿は、原則として `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews` を使う。
`event: "COMMENT"` と `comments` 配列を指定すると、複数コメントを 1 つの review としてまとめられる。
取得、投稿、再チェックはいずれも `gh` CLI / `gh api` で行い、GitHub コネクタは使わない。

最低限指定する値:

- `commit_id`: 対象 PR の head commit SHA
- `body`: review 全体の本文。`event: "COMMENT"` では必須
- `event`: `"COMMENT"`
- `comments[].path`: 対象ファイルのリポジトリ相対パス
- `comments[].side`: 変更後行なら `"RIGHT"`、変更前行なら `"LEFT"`
- `comments[].line`: ファイル内の絶対行番号
- `comments[].body`: コメント本文

## payload 作成例

`<agent>` と `<model>` は、実行中の環境から取得したエージェント名とモデル名へ置き換える。

    HEAD_COMMIT_SHA=$(gh pr view "$PR_NUMBER" --json headRefOid --jq .headRefOid)

    jq -n \
      --arg commit_id "$HEAD_COMMIT_SHA" \
      --rawfile review_body review-body.md \
      --rawfile comment_body review-comment.md \
      '{
        commit_id: $commit_id,
        body: $review_body,
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

`review-body.md` の例:

    今回確認できた良い点:

    - 同じ要求が重複して到達する条件を確認しましたが、永続化前の一意性確認とそのケースを扱うテストにより、二重登録を防ぐ構成になっています。

    AIレビュー補助（<agent> / <model>）によるレビューです 🤖

良い点は明確な根拠がある場合だけ、最大2件まで記載する。指摘がある場合も、承認やマージ可否を示す本文にはしない。

`review-comment.md` の例:

    [must] ⚠️ 問題の要約

    なぜ問題になるかを短く説明します。

    必要なら修正案を書きます。

    AIレビュー補助（<agent> / <model>）によるレビューです 🤖

## 注意事項

- JSON payload は一時ファイルとして作成し、`gh api --input review-payload.json` で渡す。
- 複数行の Markdown コメント本文は別ファイルから読み込んで JSON を生成する。
- JSON 内では改行が `\n` として表現されるが、GitHub 上のコメント本文は実改行として表示される。
- 本文にバッククォート、`$()`、引用符、改行が含まれるため、JSON や Markdown コメント本文をシェル引数へ直接埋め込まない。

## 指摘なしの review comment

指摘がない場合は、inline comment を作らず、`event: "COMMENT"` と `body` だけを指定した review comment を投稿する。
この場合も `APPROVE` は使わない。

payload 例:

    jq -n \
      --rawfile body no-findings.md \
      '{
        event: "COMMENT",
        body: $body
      }' > no-findings-review-payload.json

    gh api \
      --method POST \
      "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" \
      --input no-findings-review-payload.json

`no-findings.md` の例:

    確認した範囲では、修正が必要な指摘は見つかりませんでした。

    AIレビュー補助（<agent> / <model>）によるレビューです 🤖
