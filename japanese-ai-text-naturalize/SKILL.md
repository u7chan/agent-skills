---
name: japanese-ai-text-naturalize
description: AI生成っぽい日本語の技術・業務文を診断し、自然で実用的な文章に書き直す。技術ブログ、設計メモ、PR説明、社内文書、リリース文、レビューコメントの下書き改善で使う。
---

# Japanese AI Text Naturalize

AIで生成したように見える日本語を、読み手がそのまま使える技術・業務文に戻す。
詳細指示は必要な reference だけ読む。

## 必須方針

- 目的は「くだけた文章」ではなく、誰が何を判断し、読者が何を得るかを明確にすること。
- 事実、数値、固有名詞、判断の強さを勝手に足さない。不足情報は `要確認` として残す。
- 元文の敬体・常体、対象読者、会社やチームの温度感を維持する。
- 技術・業務文として必要な硬さ、仕様語、確認事項は無理に消さない。

## 実行ルート

1. 依頼種別を判定する。
   - 書き直し: `references/output-format.md` と、必要に応じて `references/rewrite-playbook.md` を読む。
   - 診断: `references/diagnosis.md` と `references/output-format.md` を読む。
   - 比較・レビュー: `references/diagnosis.md`、`references/phrase-watchlist.md`、`references/output-format.md` を読む。
2. 文書種別を判定する。
   - 技術ブログ、設計メモ、PR説明、社内告知、レビューコメントなら `references/rewrite-playbook.md` を読む。
   - 文書種別が不明なら、技術・業務文の標準トーンで扱う。
3. 語彙や記号の違和感を確認する必要がある場合だけ `references/phrase-watchlist.md` を読む。
4. Before/After の作り方に迷った場合だけ `references/examples.md` を読む。

## リファレンス索引

- `references/diagnosis.md`: AIっぽさを見分ける5軸の診断表。
- `references/rewrite-playbook.md`: 文書種別ごとの書き換え方。
- `references/phrase-watchlist.md`: 注意すべき語彙と扱い方。
- `references/output-format.md`: 出力形式、品質チェック、不足情報の扱い。
- `references/examples.md`: 技術・業務文のBefore/After例。
