---
name: commit
description: コミットメッセージの提案ワークフロー
---

## ワークフロー

### 1. 現在のブランチを確認

現在のブランチを確認するためのgitコマンドを実行:
- `git branch --show-current`

### 2. コミットメッセージ形式

**タイトル（≤60文字）:**
- 命令形（"add"而非"adds"）
- 小文字（記号・頭字語を除く）
- プレフィックス: `feat:` `fix:` `docs:` `style:` `refactor:` `test:` `chore:`

**本文:**
- *何を* および *なぜ* を説明
- 命令形

### 3. 出力形式

```
## コミットメッセージ

git commit -m "<prefix>: <title>" -m "<body>"
```

### 4. ステージング

```bash
git add <file>
# または特定の変更には `git hunks` を使用
git commit -m "title" -m "body"
```

### 5. ユーザー確認

提案後にユーザーが「OK」と言った場合、以下を自動実行:

```bash
git add .  # ファイルがステージされていない場合のみ
git commit -m "<prefix>: <title>" -m "<body>"
```
