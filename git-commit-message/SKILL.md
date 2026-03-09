---
name: git-commit-message
description: Commit message suggestion workflow
---

## ワークフロー

### 1. コンテキストを確認

**重要: まず会話コンテキストを確認する。**

会話内に十分なコンテキスト（作業内容の説明、タスクの詳細、変更予定の機能など）が既に利用可能か確認する。

**コンテキストが利用可能な場合:**
1. 現在のブランチのみを表示
2. ユーザーに尋ねる: "この情報で十分ですか？ \"OK\" と返信いただければコミットメッセージの作成に進みます。"
3. ユーザー確認を待つ
4. ユーザーが「OK」または確認を返信した場合、**ステップ3に直接スキップ**して即座にコミットメッセージを生成
5. ユーザーがより多くの情報を必要とする場合（「OK」以外）:
   - `git status`
   - `git diff --staged --name-status`

**コンテキストが利用できない場合:**
即座に以下のgitコマンドを実行してコンテキストを収集:
- `git status`
- `git diff --staged --name-status`

### 2. スコープの決定（モノレポの場合）

プロジェクトがモノレポの場合、現在のディレクトリ名を取得:
```bash
basename "$(pwd)"
```

または会話コンテキストから影響を受けるスコープを特定。

### 3. コミットメッセージ形式

**タイトル（≤60文字）:**
- 命令形（add, fix, update など）
- 小文字で記述（API などの頭字語は例外）
- プレフィックス: `feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`
- モノレポの場合: スコープ付き `feat(scope):` `fix(scope):` など

**本文:**
- 何を変更したか、および なぜ変更したかを説明

**生成手順:**
1. 変更内容を整理
2. 主な変更タイプを特定（新機能、バグ修正など）
3. 影響範囲を特定
4. 上記ルールに従ってコミットメッセージを作成

### 4. 出力形式

```
## コミットメッセージ

git commit -m "<prefix>: <title>" -m "<body>"
```

### 5. ステージング

```bash
git add <file>
# または特定の変更には `git hunks` を使用
git commit -m "title" -m "body"
```

### 6. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

```bash
git add .  # ファイルがステージされていない場合のみ
git commit -m "<prefix>: <title>" -m "<body>"
```

## 例

### モノレポではない場合
- コミット: `feat: add user authentication feature`

### モノレポの場合

**`/projects/monorepo/packages/auth` にいる場合:**
- コミット: `feat(auth): add OAuth2 support for Google login`

**`/projects/monorepo/apps/web` にいる場合:**
- コミット: `fix(web): resolve React hydration mismatch on SSR`
