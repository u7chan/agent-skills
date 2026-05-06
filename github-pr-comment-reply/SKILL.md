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
review comment への threaded reply と、トップレベルの PR conversation comment への follow-up comment 投稿を切り分けて扱う。

# ワークフロー

1. 対象 PR と返信対象コメントを特定する。
2. `gh auth status` で認証と権限を確認する。
3. 対象コメントが review comment か top-level PR comment かを判定する。
4. 返信本文を作成またはドラフトする。
5. 投稿前に必ずユーザー確認を取る。
6. `gh api` で返信または follow-up comment を投稿する。
7. 投稿結果を確認してユーザーへ報告する。

GitHub コネクタは使わず、`gh` / `gh api` の認証で投稿する。コネクタと `gh` は認証主体や権限が異なるため、書き込み操作で 403 になることがある。

参照マップ:

- Step 1, 3: `references/target-resolution.md`
- Step 2, 7: `references/error-handling.md`
- Step 4, 5, 6: `references/posting-rules.md`

# 参考資料

- `github-pr-review/SKILL.md`
