---
name: github-pr-create
description: Use when asked to create or open a GitHub PR, including casual requests like "PRまでお願い", "PRまで", "pushしてPR", "PR作って", or "PR open". Handles PR body generation and gh-based PR creation.
---

## 概要
`gh` CLI を使って GitHub に PR を作成する。GitHub コネクタは使わない。会話内に完成済みの `PR_BODY` がない場合でも、このスキル内のテンプレートに従ってその場で本文を生成してから PR を作成する。

## 事前確認

- `gh auth status` が成功することを確認する
- 現在のブランチが `main` `master` `develop` 系なら、そのまま PR を作らず先に作業ブランチを作る
- `BASE..HEAD` にコミットがない場合は、先にコミットを作る
- 未追跡ファイルや無関係な変更は勝手に追加・コミットしない

## 実行手順

### 1. PR 本文を用意する

- 会話内に完成済みの `PR_BODY` がある場合は、それを優先して使う
- `PR_BODY` がない場合は、現在の変更内容から以下の構造で本文を生成する

````markdown
## Issues

- Close {IssueId}  <!-- Issue をクローズする場合 -->
- Refs {IssueId}   <!-- 関連付けのみでクローズしない場合 -->

## Why

この変更が必要な背景・目的・モチベーション。

## Summary

この PR で行う変更の簡潔な説明。

## Changes

- 変更 1
- 変更 2

## Checklist

- [ ] 項目 1
- [ ] 項目 2

## Details（任意）

技術的な詳細、実装メモなど
````

- 本文生成時は次のガイドラインに従う:
  - 明確で簡潔な言葉を使用する
  - *何を* と *なぜ* に焦点を当てる
  - Issue をクローズする場合、`Issues` セクションは `- Close {IssueId}` の形式にする
  - Issue をクローズしない場合、`Issues` セクションは `- Refs {IssueId}` の形式にする
  - `Summary` は 2〜3 文以内に収める
  - `Checklist` は実際の変更内容を反映させる
  - `Details` は必要な場合のみ追加する

### 2. gh で PR を作成する

```bash
# 変数設定
BRANCH=$(git branch --show-current)
BASE="${BASE_BRANCH:-main}"

# gh 認証確認
gh auth status

# 保護ブランチ上では止める
case "$BRANCH" in
  main|master|develop)
    echo "Create or switch to a work branch before opening a PR."
    exit 1
    ;;
esac

# PR対象のコミットがない場合は止める
if [ -z "$(git log --oneline "${BASE}..HEAD")" ]; then
  echo "No commits to include in the PR. Commit your changes first."
  exit 1
fi

# リモート確認＆プッシュ（必要時）
if [ -z "$(git ls-remote --heads origin $BRANCH)" ]; then
  git push -u origin $BRANCH
fi

# PR作成（PR_BODY は既存入力またはその場で生成）
FILE=$(mktemp)
trap 'rm -f "$FILE"' EXIT
cat > "$FILE" << 'EOF'
${PR_BODY}
EOF

gh pr create --base "$BASE" --body-file "$FILE" --title "${PR_TITLE}" ${WEB:+--web}

# 作成結果の確認
gh pr view "$BRANCH" --json title,body,url
```

## 入力
- **PR_BODY**: 会話履歴や事前生成済み本文（任意。未指定時はその場で生成）
- **PR_TITLE**: タイトル（未指定時は推定またはユーザー確認）
- **BASE_BRANCH**: ベースブランチ（default: main）
- **WEB**: ブラウザで開く場合は`--web`を追加

## エラー対応
- **gh未インストール/未認証**: `gh auth login` を促す
- **main/master/develop 上で作業中**: 先に作業ブランチを作る
- **コミットが未作成**: 先にコミットを作る
- **Push失敗**: エラー内容を表示して手動対応を促す
- **既存PRがある**: `gh pr view "$BRANCH" --json title,url` で既存PRを確認する
- **本文更新が必要**: `gh api repos/<owner>/<repo>/pulls/<number> --method PATCH --field body="$(cat "$FILE")"` を使う

## 注意

- Markdown を含む PR 本文は `gh pr create --body` に直接埋め込まず、原則 `--body-file` を使う
- 作成後は `gh pr view --json title,body,url` でタイトル・本文・URL を確認する
