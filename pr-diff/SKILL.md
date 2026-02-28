---
name: pr-diff
description: git差分からPR本文を生成するワークフロー
---

## ワークフロー

### 1. PR本文の構造

まず出力形式を理解する。

**構造:**
```markdown
## Summary

このPRで行う変更の簡潔な説明。

## Changes

- 変更1
- 変更2

## Details

任意: 技術的な詳細、実装メモなど

## Checklist

- [ ] 項目1
- [ ] 項目2
```

**ガイドライン:**
- 明確で簡潔な言葉を使用
- *何を* および *なぜ* に焦点を当てる
- サマリーは2〜3文以内に収める
- チェックリストは実際の変更を反映させる

### 2. コンテキストを収集

即座に以下のgitコマンドを実行してコンテキストを収集:
- `git branch --show-current`
- `git log --oneline main..HEAD`
- `git diff --name-status main`

### 3. PR本文の作成

ステップ1の構造に従い、ステップ2で収集したコンテキストを使用してPR本文を作成。

**PR本文全体をマークダウンのコードブロックで囲む:**

~~~
```markdown
## Summary
...
```
~~~
