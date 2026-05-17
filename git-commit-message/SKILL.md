---
name: git-commit-message
description: Commit message suggestion workflow
---

## ワークフロー

### 1. コンテキストを確認

**重要: まず会話コンテキストを確認する。**

会話内に十分なコンテキスト（作業内容の説明、タスクの詳細、変更予定の機能など）が既に利用可能か確認する。

**コンテキストが利用可能な場合:**
1. 会話履歴から十分な情報（作業内容、変更の目的など）が得られると判断
2. **ステップ3に直接スキップ**して即座にコミットメッセージを生成

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
- **英語で記述する**
- 命令形（add, fix, update など）
- 小文字で記述（API などの頭字語は例外）
- プレフィックス: `feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`
- PR レビュー指摘への対応コミットでは、変更種別よりも feedback 対応であることを優先して `fb:` を使う
- モノレポの場合: スコープ付き `feat(scope):` `fix(scope):` など
- `fb:` でもスコープは通常ルールに従う。モノレポでは feedback ではなく対象プロジェクトや対象スキルを scope に入れる

**本文（英語で記述）:**
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
