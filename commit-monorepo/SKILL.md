---
name: commit-monorepo
description: Monorepo commit message suggestion workflow
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. コンテキストを確認

**重要: まず会話コンテキストを確認する。**

会話内に十分なコンテキスト（作業内容の説明、タスクの詳細、変更予定の機能、影響を受けるパッケージ/アプリなど）が既に利用可能か確認する。

**コンテキストが利用可能な場合:**
1. 現在のブランチのみを表示
2. ユーザーに尋ねる: "この情報で十分ですか？ \"OK\" と返信いただければコミットメッセージの作成に進みます。"
3. ユーザー確認を待つ
4. ユーザーが「OK」または確認を返信した場合、**ステップ5に直接スキップ**して即座にコミットメッセージを生成
5. ユーザーがより多くの情報を必要とする場合（「OK」以外）:
   - `git status`
   - `git diff --staged --name-status`

**コンテキストが利用できない場合:**
即座に以下のgitコマンドを実行してコンテキストを収集（ユーザー確認不要）:
- `git status`
- `git diff --staged --name-status`

### 3. スコープの決定

スコープとして使用する現在のディレクトリ名を取得:
```bash
basename "$(pwd)"
```

または会話コンテキストから影響を受けるスコープを特定。

### 4. コミットメッセージ形式

**タイトル（≤60文字）:**
- 命令形（"add"而非"adds"）
- 小文字（記号・頭字語を除く）
- スコープ付きプレフィックス: `feat(scope):` `fix(scope):` `docs(scope):` `style(scope):` `refactor(scope):` `test(scope):` `chore(scope):`

**本文:**
- *何を* および *なぜ* を説明
- 命令形

**生成ロジック:**
1. 会話コンテキストから作業内容を分析
2. 主な変更タイプ（新機能、バグ修正、リファクタリングなど）を特定
3. 影響を受けるコンポーネント、機能、スコープを特定
4. 上記のルールに従ってコミットメッセージを生成

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

**`/projects/monorepo/packages/auth` にいる場合:**
- コミット: `feat(auth): add OAuth2 support for Google login`

**`/projects/monorepo/apps/web` にいる場合:**
- コミット: `fix(web): resolve React hydration mismatch on SSR`
