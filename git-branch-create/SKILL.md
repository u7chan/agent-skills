---
name: git-branch-create
description: Branch naming and creation workflow
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. コンテキストを確認

**重要: まず会話コンテキストを確認する。**

会話内に十分なコンテキスト（作業内容の説明、タスクの詳細、変更予定の機能など）が既に利用可能か確認する。

**コンテキストが利用可能な場合:**
1. 会話履歴から十分な情報（作業内容、変更の目的など）が得られると判断
2. **ステップ4に直接スキップ**して即座にブランチ名を生成

**コンテキストが利用できない場合:**
即座に以下のgitコマンドを実行してコンテキストを収集（ユーザー確認不要）:
- `git status`
- `git diff --staged --name-status`

### 3. スコープの決定（モノレポの場合）

プロジェクトがモノレポ（複数パッケージ/アプリ）の場合、現在のディレクトリ名を取得:
```bash
basename "$(pwd)"
```

または会話コンテキストから影響を受けるスコープを特定。

### 4. ブランチ名の生成

**標準形式:** `<type>/<description>`

**モノレポ形式:** `<type>/<scope>-<description>` または `<type>/<scope>/<description>`

**Types:** `feature/` `fix/` `docs/` `refactor/` `test/` `chore/`

**ルール:**
- 小文字でハイフン区切り（例: `feature/add-user-auth`）
- 3〜5語で簡潔に
- issue番号がある場合は含める（例: `fix/issue-123-login-error`）
- モノレポの場合: スコープをプレフィックスとして含める（例: `feature/auth-add-oauth`）

**生成ロジック:**
1. 会話コンテキストから作業内容を分析
2. 主な変更タイプ（新機能、バグ修正、リファクタリングなど）を特定
3. 影響を受けるコンポーネントや機能を特定
4. 上記のルールに従ってブランチ名を生成

### 5. 出力形式

**main/develop*ブランチの場合:**
```
## 推奨ブランチ

git switch -c <type>/<description>
```

**その他のブランチの場合:**
```
## 現在の状態
現在のブランチ: <branch-name>

## 推奨ブランチ（必要な場合）
git switch -c <type>/<description>
```

### 6. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

**main/develop*ブランチの場合:**
```bash
git switch -c <type>/<description>
```

**その他のブランチの場合:**
現在のブランチから新しいブランチを作成するか、先にmain/developにチェックアウトするかをユーザーに確認。
