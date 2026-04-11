# PR Body Template

## テンプレート

````markdown
## Issues

- Close {IssueId}  <!-- Issue をクローズする場合 -->
- Refs {IssueId}   <!-- 関連付けのみでクローズしない場合 -->

## Why

この変更が必要な背景・目的・モチベーション。

## Summary

この PR で行う変更の簡潔な説明。

## Changes

- 変更 1
- 変更 2

## Checklist

- [ ] 項目 1
- [ ] 項目 2

## Details（任意）

技術的な詳細、実装メモなど
````

## ガイドライン

- 明確で簡潔な言葉を使用する
- *何を* と *なぜ* に焦点を当てる
- Issue をクローズする場合、`Issues` セクションは `- Close {IssueId}` の形式にする
- Issue をクローズしない場合、`Issues` セクションは `- Refs {IssueId}` の形式にする
- `Summary` は 2〜3 文以内に収める
- `Checklist` は実際の変更内容を反映させる
- `Details` は必要な場合のみ追加する

## 利用ルール

- `git-pr-description` と `github-pr-create` はこのファイルを一次情報として参照する
- 本文構造やガイドラインを変更する場合は、このファイルを更新して両スキルへ反映する
- 会話内に完成済みの `PR_BODY` がある場合は、その本文を優先して利用してよい
