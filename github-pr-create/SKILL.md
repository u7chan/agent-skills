---
name: github-pr-create
description: When instructed to create a PR for GitHub.
---

## 概要
既存のPR本文を使ってGitHubにPRを作成。`git-pr-description` スキル実行後や本文作成済み状態で使用。リモートにブランチがなければ自動pushしてから `gh pr create` を実行。

## 実行手順

```bash
# 変数設定
BRANCH=$(git branch --show-current)
BASE="${BASE_BRANCH:-main}"

# リモート確認＆プッシュ（必要時）
if [ -z "$(git ls-remote --heads origin $BRANCH)" ]; then
  git push -u origin $BRANCH
fi

# PR作成（PR_BODYはコンテキストから取得）
FILE=$(mktemp)
cat > "$FILE" << 'EOF'
${PR_BODY}
EOF

gh pr create --base "$BASE" --body-file "$FILE" --title "${PR_TITLE}" ${WEB:+--web}

# 一時ファイル削除
rm -f "$FILE"
```

## 入力
- **PR_BODY**: 会話履歴/コンテキストから取得（必須。ない場合はユーザーに依頼）
- **PR_TITLE**: タイトル（未指定時は推定またはユーザー確認）
- **BASE_BRANCH**: ベースブランチ（default: main）
- **WEB**: ブラウザで開く場合は`--web`を追加

## エラー対応
- **gh未インストール/未認証**: `gh auth login` を促す
- **Push失敗**: エラー内容を表示して手動対応を促す
