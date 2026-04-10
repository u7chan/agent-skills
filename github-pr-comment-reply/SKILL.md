---
name: github-pr-comment-reply
description: >
  Use this when asked to reply to an existing GitHub Pull Request review comment
  or PR conversation comment. Trigger this skill when the user provides a
  comment URL or comment ID, or asks to find a comment on the current PR and
  post a reply on GitHub.
---

# 概要

既存の GitHub PR コメントへ返信するためのスキル。
review comment への threaded reply と、トップレベルの PR conversation comment への follow-up comment 投稿を安全に切り分けて扱う。

# このスキルを使用するタイミング

- ユーザーが GitHub PR の review comment に返信したい時
- ユーザーが GitHub PR の conversation comment に返答したい時
- コメント URL や comment ID を渡して「これに返して」と言われた時
- 現在の PR から返信対象コメントを探して返答したい時

# Agent が行うこと

1. 対象 PR と返信対象コメントを特定する。
2. `gh auth status` で認証と権限を確認する。
3. 対象コメントが review comment か top-level PR comment かを判定する。
4. 返信本文を作成またはドラフトする。
5. 投稿前に必ずユーザー確認を取る。
6. `gh api` で返信または follow-up comment を投稿する。
7. 投稿結果を確認してユーザーへ報告する。

# 入力と出力

## 入力

- PR URL、PR 番号、comment URL、comment ID のいずれか
- 未指定の場合は、現在ブランチに紐づく PR
- 返信本文、または返信に含めたい要点
- 必要なら関連コミットや修正内容

## 出力

- GitHub 上に投稿された返信コメント
- 投稿先 URL
- ユーザーへの簡潔な実行報告

# ステップの詳細

## 1. 対象 PR とコメントを特定する

- コメント URL がある場合は、URL から `owner/repo`、PR 番号、comment ID を読み取る。
- comment ID だけがある場合は、現在の `origin` と PR 文脈から `owner/repo` と PR 番号を補完する。
- PR 番号または PR URL だけがあり、comment ID がない場合は、その PR から返信候補を探索する。
- 何も指定がない場合は、`gh pr view --json number,url` で現在ブランチの PR を特定する。
- コメント URL のアンカーは以下として扱う。
  - `#discussion_r<id>`: review comment
  - `#issuecomment-<id>`: top-level PR comment

## 2. 認証とリポジトリ権限を確認する

- 最初に `gh auth status` を実行し、対象リポジトリへ書き込み可能な認証があることを確認する。
- 必要なら `gh api user --jq .login` で認証ユーザー名を取得する。
- `gh auth status` が失敗した場合は、`gh auth login` を促して停止する。

## 3. コメント種別を判定する

- まず `gh api repos/{owner}/{repo}/pulls/comments/{comment_id}` を試す。
- 取得できれば review comment とみなし、`pull_request_review_id` や `in_reply_to_id` を確認する。
- 404 の場合のみ `gh api repos/{owner}/{repo}/issues/comments/{comment_id}` を試す。
- 取得できれば top-level PR comment とみなす。
- どちらでも取得できない場合は、comment ID の誤りまたは対象リポジトリ不一致として停止する。

## 4. comment ID 未指定時は現在 PR から候補を探索する

- review comment を優先して探す。
- `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate` で review comments を取得し、`in_reply_to_id == null` のコメントを返信元候補として扱う。
- 認証ユーザー自身が書いたコメントは候補から外す。
- 同じ comment ID を `in_reply_to_id` に持つ返信コメントのうち、認証ユーザー自身のものが既にある場合は候補から外す。
- review comment の候補がなければ、`gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate` で top-level PR comments を確認する。
- top-level PR comments も認証ユーザー自身のものは除外し、最新順で候補を並べる。
- 候補が複数ある場合は、最新順で最大 3 件まで URL と本文要約をユーザーへ提示し、どれに返信するか確認する。

## 5. 返信本文を作る

- ユーザーが返信本文を明示している場合は、その文面を使う。
- 明示がない場合は、対象コメントの論点と直近の修正内容から返信案をドラフトする。
- AI エージェント識別メタ情報は既定で付ける。ユーザーが明示的に不要と言った場合のみ省略する。
- 返信本文に改行が必要な場合は、実改行のテキストとして組み立てる。文字列としての `\n` をそのまま投稿しない。

## 6. 投稿前に必ずユーザー確認を取る

- 投稿前に、対象コメント URL、返信種別、返信本文のプレビューをユーザーへ見せる。
- 投稿前確認は必須とし、ユーザーの承認があるまで外部投稿しない。
- 推奨確認文は次の形式とする。

```text
この内容で返信します。
対象: <comment-url>
種別: review comment reply / PR comment follow-up

<reply body preview>

"OK" と返信いただければ投稿します。
```

## 7. `gh api` で投稿する

- 本文は原則として一時ファイル経由で渡す。単純な 1 行本文以外をシェル引数へ直接埋め込まない。
- 推奨パターンは次のとおり。

```bash
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
printf '%s\n' "$BODY" > "$TMP"
```

- review comment への返信は、次のエンドポイントに固定する。

```bash
gh api -X POST "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -F "body=@$TMP"
```

- top-level PR comment には threaded reply がないため、新しい PR comment を追加する。
- その場合は、本文の冒頭に元コメント URL か comment ID を入れて関連を明示する。

```bash
gh api -X POST "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" \
  -F "body=@$TMP"
```

## 8. 投稿結果を確認する

- review comment reply は API 応答の `in_reply_to_id`、`id`、`html_url` を確認する。
- top-level PR comment follow-up は API 応答の `id` と `html_url` を確認する。
- 必要なら取得 API を再実行し、意図した本文が投稿されていることを確認する。

## 9. ユーザーへ報告する

- 対象 comment ID
- 投稿種別
  - review comment reply
  - top-level PR comment follow-up
- 投稿先 URL
- 実行できなかった場合は、失敗した API と理由

# エラー対応

- **`gh` 未認証**: `gh auth login` を促して停止する
- **権限不足 (`403`)**: 書き込み権限不足として報告する
- **対象が見つからない (`404`)**: comment 種別違い、comment ID 誤り、repo 不一致を確認する
- **review comment 返信**: `repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies` 以外の経路は使わない
- **top-level PR comment**: threaded reply は使えないため、`issues/{pr_number}/comments` への follow-up へ切り替える
- **候補が複数ある**: 自動投稿せず、最大 3 件まで提示してユーザーに選ばせる

# 品質チェック

- `description` を読むだけで、返信専用スキルであることが分かる
- review comment と top-level PR comment の扱いが分かれている
- 投稿前のユーザー確認が必須になっている
- 複数行本文を一時ファイル経由で渡すルールが含まれている
- AI エージェント識別メタ情報の既定ルールと省略条件が明記されている
- 未指定時の候補探索で、認証ユーザー自身のコメントを除外している

# 参考資料

- `gh pr view --help`
- `gh api --help`
- `github-pr-review/SKILL.md`
