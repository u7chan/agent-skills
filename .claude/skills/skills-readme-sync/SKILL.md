---
name: skills-readme-sync
description: >
  Use this when adding, renaming, removing, or materially changing skills in this
  repository and the README may need to be updated. It synchronizes the README's
  Available Skills table with the current skill set.
---

# Skills README Sync

## 概要

このスキルは、`agent-skills` リポジトリ内のスキル変更に合わせて `README.md` のスキル一覧を同期する。
スキル本体だけ直して README を更新し忘れる漏れを防ぐためのもの。

## このスキルを使用するタイミング

- 新しいスキルディレクトリを追加した時
- 既存スキルの名前を変更した時
- スキルを削除した時
- `SKILL.md` の説明変更により README の説明文も見直すべき時
- このリポジトリで「README も更新して」「一覧漏れを直して」と言われた時

## Agentが行うこと

1. 変更されたスキルと現在のスキル一覧を確認する。
2. `README.md` の `Available Skills` を現在のスキル構成に合わせて更新する。
3. 差分を確認し、README 以外を不用意に変更していないことを確認する。

## 入力と出力

**入力:**
- `agent-skills` リポジトリ内のスキル追加・更新・削除
- 更新対象の `README.md`

**出力:**
- 現在のスキル構成と整合する `README.md`

## ステップの詳細

### Step 1: 現在のスキル構成を確認する

確認するもの:
- リポジトリ直下の各スキルディレクトリ
- `.claude/skills/` 配下の各スキルディレクトリ
- 各スキルの `SKILL.md`
- `README.md` の `Available Skills`

`find . -maxdepth 4 -name SKILL.md | sort` などで実在するスキルを確認し、README の列挙漏れや古い名前を見つける。

### Step 2: 一覧表の説明を決める

README の説明文は `SKILL.md` の front matter と本文冒頭から短く要約する。

ルール:
- 1行で収まる短い説明にする
- スキルの用途を先に書く
- README では詳細手順を書きすぎない
- 既存の日本語トーンに合わせる

### Step 3: README の一覧を同期する

更新対象:
- `Available Skills` の表

注意:
- スキル追加時は一覧に追記する
- スキル名変更時は一覧の名前とリンク先を揃える
- スキル削除時は一覧から消す
- 配置場所が `.claude/skills/` の場合は一覧のリンク先にそのパスを反映する
- セットアップ手順など無関係な箇所は変更しない

### Step 4: 差分を検証する

確認すること:
- README に新旧の不整合が残っていない
- 追加したスキル名とリンク先が一致している
- 意図しない文章変更が入っていない

## 品質チェック

- [ ] 実在する全スキルが `Available Skills` に載っている
- [ ] 各スキルのリンク先が正しい
- [ ] 説明文が古いスキル名や古い用途を含んでいない
- [ ] README 以外のファイルを変更する場合は、その必要性が明確である
