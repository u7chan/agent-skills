# Target Resolution

## 目的

対象 PR と返信対象コメントを特定し、review comment と top-level PR comment を切り分ける。

## 入力の扱い

- コメント URL がある場合は、URL から `owner/repo`、PR 番号、comment ID を読み取る。
- comment ID だけがある場合は、現在の `origin` と PR 文脈から `owner/repo` と PR 番号を補完する。
- PR 番号または PR URL だけがあり、comment ID がない場合は、その PR から返信候補を探索する。
- 何も指定がない場合は、`gh pr view --json number,url` で現在ブランチの PR を特定する。

## コメント URL のアンカー

- `#discussion_r<id>`: review comment
- `#issuecomment-<id>`: top-level PR comment

## コメント種別の判定

- コメント URL に `#discussion_r<id>` が含まれている場合は、その時点で review comment とみなす。
- コメント URL に `#issuecomment-<id>` が含まれている場合は、その時点で top-level PR comment とみなす。
- URL アンカーがなく、bare comment ID だけで種別が分からない場合のみ API で判定する。
- まず `gh api repos/{owner}/{repo}/pulls/comments/{comment_id}` を試す。
- 取得できれば review comment とみなし、`pull_request_review_id` や `in_reply_to_id` を確認する。
- 404 の場合のみ `gh api repos/{owner}/{repo}/issues/comments/{comment_id}` を試す。
- 取得できれば top-level PR comment とみなす。
- どちらでも取得できない場合は、comment ID の誤りまたは対象リポジトリ不一致として停止する。

## comment ID 未指定時の候補探索

- review comment を優先して探す。
- `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate` で review comments を取得し、`in_reply_to_id == null` のコメントを返信元候補として扱う。
- 認証ユーザー自身が書いたコメントは候補から外す。
- 同じ comment ID を `in_reply_to_id` に持つ返信コメントのうち、認証ユーザー自身のものが既にある場合は候補から外す。
- review comment の候補がなければ、`gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate` で top-level PR comments を確認する。
- top-level PR comments も認証ユーザー自身のものは除外し、最新順で候補を並べる。
- 候補が複数ある場合は、最新順で最大 3 件まで URL と本文要約をユーザーへ提示し、どれに返信するか確認する。
