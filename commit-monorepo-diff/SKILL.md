---
name: commit-monorepo-diff
description: モノレプロジェクト向けgit差分からコミットメッセージを生成するワークフロー
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. 変更内容の確認

ステージング済みの変更とワークツリーの変更を確認:
- `git diff --staged --name-status`
- `git diff --name-status`

### 3. スコープの決定

変更ファイルのパスからパッケージ/アプリ名を抽出してスコープを特定:
- 例: `packages/auth/src/index.ts` → スコープ: `auth`
- 例: `apps/web/components/Button.tsx` → スコープ: `web`

### 4. コミットメッセージ形式

**タイトル（≤60文字）:**
- 命令形（"add"而非"adds"）
- 小文字（記号・頭字語を除く）
- スコープ付きプレフィックス: `feat(scope):` `fix(scope):` `docs(scope):` `style(scope):` `refactor(scope):` `test(scope):` `chore(scope):`

**本文:**
- *何を* および *なぜ* を説明
- 命令形

**生成ロジック:**
1. 変更ファイルの種類と内容を分析
2. 変更ファイルのパスからスコープを特定
3. 主な変更タイプ（新機能、バグ修正、リファクタリングなど）を特定
4. 影響を受けるコンポーネントや機能を特定
5. 上記のルールに従ってコミットメッセージを生成

### 5. 出力形式

```
## コミットメッセージ

git commit -m "<type>(<scope>): <title>" -m "<body>"
```

### 6. ステージング

```bash
git add <file>
# または特定の変更には `git hunks` を使用
git commit -m "type(scope): title" -m "body"
```

### 7. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

```bash
git add .  # ファイルがステージされていない場合のみ
git commit -m "<type>(<scope>): <title>" -m "<body>"
```

## 例

**`packages/auth` 内のファイルが変更された場合:**
- コミット: `feat(auth): add OAuth2 support for Google login`

**`apps/web` 内のファイルが変更された場合:**
- コミット: `fix(web): resolve React hydration mismatch on SSR`
