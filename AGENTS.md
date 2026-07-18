# Agent Instructions

日本語で簡潔かつ丁寧に回答してください。

## Skill Naming Convention

スキル名は原則として `service-target-action` の順で付けます。

- `service`: `git` `github` `bun` `codex` `skill` のような対象領域
- `target`: `branch` `pr` `issue` `dependency` `skills` のような主対象
- `action`: `create` `review` `update` `description` のような操作内容

一覧を見た時に「どこで」「何に対して」「何をする」スキルかを判断できる名前にします。
README のグルーピングはスキル名の prefix ではなく、利用目的を優先して決めます。

## Skill Maintenance

- `SKILL.md` は原則として180行以内に収め、必須ルール・禁止事項・主要ワークフローは先頭150行以内に置く
- 長い例、詳細手順、CLI/APIサンプル、トラブルシュートは `references/` に用途別で分割する
- スキルの追加・変更時は、`SKILL.md`、`references/`、`scripts/`、プログラム内の import・外部コマンドを確認し、README の `External Dependencies` を同期する
- スキルの追加・削除時は、README 先頭の Shields.io スキル数バッジも同期する
- 依存が特定フローに限られる場合は `conditional`、代替手段の場合は `optional` と明記する

ローカル検証:

```sh
bash .scripts/validate-skills.sh
```

この検証では、`SKILL.md` の行数、`references/` の参照切れ、README の `Available Skills` と実スキル一覧、スキル数バッジ、依存カラムの一致を確認します。
