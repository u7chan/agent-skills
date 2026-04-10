# Error Handling

## 認証と権限

- 最初に `gh auth status` を実行し、対象リポジトリへ書き込み可能な認証があることを確認する。
- 必要なら `gh api user --jq .login` で認証ユーザー名を取得する。
- `gh auth status` が失敗した場合は、`gh auth login` を促して停止する。

## エラー時の扱い

- **`gh` 未認証**: `gh auth login` を促して停止する
- **権限不足 (`403`)**: 書き込み権限不足として報告する
- **対象が見つからない (`404`)**: comment 種別違い、comment ID 誤り、repo 不一致を確認する
- **review comment 返信**: `repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies` 以外の経路は使わない
- **top-level PR comment**: threaded reply は使えないため、`issues/{pr_number}/comments` への follow-up へ切り替える
- **候補が複数ある**: 自動投稿せず、最大 3 件まで提示してユーザーに選ばせる

## 投稿後の確認

- review comment reply は API 応答の `in_reply_to_id`、`id`、`html_url` を確認する。
- top-level PR comment follow-up は API 応答の `id` と `html_url` を確認する。
- 必要なら取得 API を再実行し、意図した本文が投稿されていることを確認する。

## ユーザーへの報告

- 対象 comment ID
- 投稿種別
  - review comment reply
  - top-level PR comment follow-up
- 投稿先 URL
- 実行できなかった場合は、失敗した API と理由
