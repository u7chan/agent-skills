---
name: github-pr-comment-reply
description: >
  GitHub PRのreview commentやconversation commentへの返信を依頼されたときに使う。
  コメントURL・IDが指定された場合や、現在のPRから対象コメントを探してGitHubへ返信する場合に起動する。
---

# 概要

既存の GitHub PR コメントへ返信するためのスキル。
review comment への threaded reply と、トップレベルの PR conversation comment への follow-up comment 投稿を切り分けて扱う。

# ワークフロー

1. 対象 PR と返信対象コメントを特定する。
2. `gh auth status` で認証と権限を確認する。
3. 対象コメントが review comment か top-level PR comment かを判定する。
4. 返信本文を作成またはドラフトする。
5. 対象コメントと返信本文が一意に決まる場合は、投稿前確認を挟まず自動で投稿する。
6. 現在の委譲指示末尾に標準の`herdr-delegation-metadata`がある場合だけ、その3値をAI識別メタ情報へ使う。なければ識別文全体を省略し、再解決しない。
7. `gh api` で返信または follow-up comment を投稿する。
8. 投稿結果を確認してユーザーへ報告する。

GitHub コネクタは使わず、`gh` / `gh api` の認証で投稿する。コネクタと `gh` は認証主体や権限が異なるため、書き込み操作で 403 になることがある。

対象コメントが複数候補に分かれる、返信本文の意図が会話や直近の作業結果から決められない、または外部書き込みが禁止されている場合だけ停止してユーザーへ確認する。

参照マップ:

- Step 1, 3: `references/target-resolution.md`
- Step 2, 8: `references/error-handling.md`
- Step 4, 5, 6, 7: `references/posting-rules.md`
- 委譲メタ情報のconsumer規則: `references/posting-rules.md`

# 参考資料

- `github-pr-review`
