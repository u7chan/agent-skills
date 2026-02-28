---
name: commit-monorepo
description: モノレプロジェクト向けコミットメッセージの提案ワークフロー
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. スコープの決定

スコープとして使用する現在のディレクトリ名を取得:
```bash
basename "$(pwd)"
```

### 3. コミットメッセージ形式

**タイトル（≤60文字）:**
- 命令形（"add"而非"adds"）
- 小文字（記号・頭字語を除く）
- スコープ付きプレフィックス: `feat(scope):` `fix(scope):` `docs(scope):` `style(scope):` `refactor(scope):` `test(scope):` `chore(scope):`

**本文:**
- *何を* および *なぜ* を説明
- 命令形

### 4. 出力形式

```
## コミットメッセージ

git commit -m "<type>(<scope>): <title>" -m "<body>"
```

### 5. ステージング

```bash
git add <file>
# または特定の変更には `git hunks` を使用
git commit -m "type(scope): title" -m "body"
```

### 6. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

```bash
git add .  # ファイルがステージされていない場合のみ
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

## 例

**`/projects/monorepo/packages/auth` にいる場合:**
- コミット: `feat(auth): add OAuth2 support for Google login`

**`/projects/monorepo/apps/web` にいる場合:**
- コミット: `fix(web): resolve React hydration mismatch on SSR`
