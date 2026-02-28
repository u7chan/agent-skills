---
name: branch
description: ブランチ名の提案と作成ワークフロー
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. スコープの決定（モノレポの場合）

プロジェクトがモノレポ（複数パッケージ/アプリ）の場合、現在のディレクトリ名を取得:
```bash
basename "$(pwd)"
```

### 3. ブランチ名

**標準形式:** `<type>/<description>`

**モノレポ形式:** `<type>/<scope>-<description>` または `<type>/<scope>/<description>`

**Types:** `feature/` `fix/` `docs/` `refactor/` `test/` `chore/`

**ルール:**
- 小文字でハイフン区切り（例: `feature/add-user-auth`）
- 3〜5語で簡潔に
- issue番号がある場合は含める（例: `fix/issue-123-login-error`）
- モノレポの場合: スコープをプレフィックスとして含める（例: `feature/auth-add-oauth`）

### 4. 出力形式

**main/develop*ブランチの場合:**
```
## 推奨ブランチ

git checkout -b <type>/<description>
```

**その他のブランチの場合:**
```
## 現在の状態
現在のブランチ: <branch-name>

## 推奨ブランチ（必要な場合）
git checkout -b <type>/<description>
```

### 5. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

**main/develop*ブランチの場合:**
```bash
git switch -c <type>/<description>
```

**その他のブランチの場合:**
現在のブランチから新しいブランチを作成するか、先にmain/developにチェックアウトするかをユーザーに確認。
